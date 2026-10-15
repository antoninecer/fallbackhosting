#!/usr/bin/env python3
"""REVIEW PROPOSAL: not installed. Execution requires explicit CLI flag."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import ssl
import subprocess
import time
from urllib.request import urlopen

LINEAGES={
    '/etc/letsencrypt/live/project.lab.ventureout.cz':'project.lab.ventureout.cz',
    '/etc/letsencrypt/live/lab.ventureout.cz':'lab.ventureout.cz',
}
REFERENCE=[
    ('https://dashboard.api.ventureout.cz/cards32.php','text/html'),
    ('https://dashboard.api.ventureout.cz/assets/css/style.css?v=11','text/css'),
    ('https://dashboard.api.ventureout.cz/assets/js/app.js?v=3','javascript'),
]
COMMANDS=[['/usr/sbin/nginx','-t'],['/usr/bin/systemctl','reload','nginx']]

class HookFailure(RuntimeError):pass


def perform(environment,command,canary,loaded,guard):
    lineage=environment.get('RENEWED_LINEAGE','')
    if lineage not in LINEAGES:return {'status':'SKIPPED_UNRELATED_CERTIFICATE'}
    domain=LINEAGES[lineage]
    if environment.get('RENEWED_DOMAINS','').split()!=[domain]:raise HookFailure('DOMAIN_SCOPE_MISMATCH')
    with guard():
        canary('before')
        command(COMMANDS[0],timeout=10)
        command(COMMANDS[1],timeout=10)
        loaded(lineage,domain)
        canary('after')
    return {'status':'VERIFIED_RELOAD','domain':domain}


def command(argv,timeout):
    subprocess.run(argv,check=True,timeout=timeout,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C'})


def canary(stage):
    for url,kind in REFERENCE:
        with urlopen(url,timeout=5) as response:
            if response.status!=200 or response.geturl()!=url or kind not in response.headers.get_content_type():raise HookFailure('REFERENCE_'+stage.upper()+'_FAILED')
            body=response.read(262145)
            if not body or len(body)>262144:raise HookFailure('REFERENCE_ASSET_BOUNDS')


def loaded(lineage,domain):
    # Public certificate only. Never open privkey.pem.
    pem=(Path(lineage)/'cert.pem').read_text()
    expected=hashlib.sha256(ssl.PEM_cert_to_DER_cert(pem)).digest()
    context=ssl.create_default_context()
    for attempt in range(3):
        try:
            with socket.create_connection((domain,443),timeout=5) as tcp:
                with context.wrap_socket(tcp,server_hostname=domain) as connection:
                    actual=hashlib.sha256(connection.getpeercert(binary_form=True)).digest()
            if actual==expected:return
        except (OSError,ssl.SSLError):pass
        if attempt<2:time.sleep(0.5)
    raise HookFailure('RENEWED_CERTIFICATE_NOT_OBSERVED')


@contextmanager
def guard():
    fd=os.open('/run/lock/fallbackhosting-cert-reload.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        status=os.fstat(fd)
        if status.st_uid!=os.geteuid() or status.st_mode&0o077:raise HookFailure('UNSAFE_RELOAD_LOCK')
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError as error:raise HookFailure('RELOAD_ALREADY_IN_PROGRESS') from error
        yield
    finally:os.close(fd)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--show-plan',action='store_true')
    group.add_argument('--execute-approved-deploy-hook',action='store_true')
    args=parser.parse_args()
    if args.show_plan:
        print(json.dumps({'status':'PROPOSAL_NOT_INSTALLED','lineages':LINEAGES,'commands':COMMANDS,'reference_requests':len(REFERENCE),'outer_timeout_seconds':60},indent=2))
    else:
        try:print(json.dumps(perform(os.environ,command,canary,loaded,guard)))
        except Exception:
            print(json.dumps({'status':'FAILED_OR_UNKNOWN','action':'No automatic retry or certificate/config rollback; reconcile operator evidence'}))
            raise SystemExit(1)
