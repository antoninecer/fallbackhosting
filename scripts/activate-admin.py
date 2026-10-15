#!/usr/bin/env python3
"""Approved, journaled one-host activation. Run phases individually as root.
A started phase without a done marker requires inspection; it is never replayed.
No SSH, Docker, firewall, DNS, existing vhost edits or password output.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess
import tarfile
import time
import urllib.error
import urllib.request

ROOT = Path('/opt/fallback')
REV = '21c050b36e8ddd4cd3d7ec5e87a727f556348e9b'
BACKUP = Path('/var/backups/fallbackhosting-admin-20261015')
RELEASE = Path('/var/www/fallback-admin/releases') / REV
DATA = Path('/var/lib/fallback-web/admin')
POOL = Path('/etc/php/8.3/fpm/pool.d/fallback-admin.conf')
SITE = Path('/etc/nginx/sites-available/lab.ventureout.cz')
LINK = Path('/etc/nginx/sites-enabled/lab.ventureout.cz')
CANARIES = {
    'https://dashboard.api.ventureout.cz/cards32.php': 200,
    'https://project.lab.ventureout.cz/': 200,
    'https://quantum.api.ventureout.cz/': 200,
    'https://organon.api.ventureout.cz/': 200,
    'https://app.wai.ventureout.cz/': 404,
    'https://city.api.ventureout.cz/': 502,
    'https://isocity.api.ventureout.cz/': 200,
    'https://api.wai.ventureout.cz/': 404,
}

def run(*args):
    subprocess.run(args, check=True, timeout=120)

def blob(name):
    return subprocess.check_output(['git','-c','safe.directory=/opt/fallback','-C',str(ROOT),'show',f'{REV}:{name}'], timeout=10)

def fetch(url):
    try:
        response = urllib.request.urlopen(url, timeout=12)
    except urllib.error.HTTPError as e:
        response = e
    with response:
        return response.status, response.headers.get_content_type(), response.geturl(), response.read(1048576)

def canaries():
    import re
    for url, expected in CANARIES.items():
        status, kind, final, body = fetch(url)
        assert status == expected and final == url, 'Canary mismatch: ' + url
        if 'cards32.php' in url or 'project.lab' in url:
            assert kind == 'text/html' and len(body) > 100, 'Canary content mismatch'
            paths = re.findall(rb'(?:src|href)=["\']([^"\']+\.(?:css|js)(?:\?[^"\']*)?)["\']', body)
            assert len(paths) >= 2, 'Canary assets missing'
            for path in paths:
                asset = urllib.parse.urljoin(url, path.decode())
                assert urllib.parse.urlsplit(asset).netloc == urllib.parse.urlsplit(url).netloc
                code, mime, _, data = fetch(asset)
                assert code == 200 and data and ('css' in mime or 'javascript' in mime), 'Canary asset mismatch'
    print('PASS protected canaries, TLS, reference/project assets (point-in-time)')

def config_hashes():
    result = {}
    for base in [Path('/etc/nginx'), Path('/etc/php/8.3/fpm')]:
        for p in base.rglob('*'):
            if p.is_file() and not p.is_symlink() and p not in (POOL, SITE):
                result[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return result

def verify_existing():
    baseline = json.loads((BACKUP/'config-hashes.json').read_text())
    assert baseline == config_hashes(), 'Existing configuration changed; reconcile before proceeding'
    canaries()

def install_bytes(path, content, mode=0o644):
    path.write_bytes(content)
    path.chmod(mode)

def reload_nginx():
    run('nginx','-t')
    run('systemctl','reload','nginx')
    time.sleep(2)
    verify_existing()

def prepare():
    for target in [POOL,SITE,LINK,Path('/var/www/fallback-admin'),Path('/var/lib/fallback-web'),Path('/etc/letsencrypt/live/lab.ventureout.cz')]:
        assert not os.path.lexists(target), f'Existing target requires reconciliation: {target}'
    assert subprocess.run(['getent','passwd','fallback-web'],stdout=subprocess.DEVNULL).returncode != 0
    assert subprocess.run(['getent','group','fallback-web'],stdout=subprocess.DEVNULL).returncode != 0
    canaries()
    seed = ROOT/'.local/admin'
    for name in ['auth.json','inventory.json']:
        assert (seed/name).stat().st_mode & 0o077 == 0, 'Private seed mode invalid'
        json.loads((seed/name).read_text())
    install_bytes(BACKUP/'config-hashes.json',json.dumps(config_hashes()).encode(),0o600)
    with tarfile.open(BACKUP/'prechange.tar.gz','w:gz') as archive:
        for path in ['/etc/nginx','/etc/php/8.3/fpm',str(seed/'auth.json'),str(seed/'inventory.json')]:
            archive.add(path,recursive=True)
    (BACKUP/'prechange.tar.gz').chmod(0o600)
    with tarfile.open(BACKUP/'prechange.tar.gz') as archive:
        for entry in archive:
            if entry.isfile():
                stream = archive.extractfile(entry)
                while stream.read(1048576): pass
    run('useradd','--system','--user-group','--home-dir','/var/lib/fallback-web','--shell','/usr/sbin/nologin','fallback-web')
    for directory in [RELEASE.parent.parent, RELEASE.parent, RELEASE]:
        directory.mkdir(mode=0o755)
        directory.chmod(0o755)
    (RELEASE/'public').mkdir(mode=0o755)
    (RELEASE/'public').chmod(0o755)
    for name in ['lib.php','manage.php','public/index.php','public/admin.css']:
        install_bytes(RELEASE/name,blob('admin/'+name))
    (RELEASE.parent.parent/'current').symlink_to(RELEASE)
    account=pwd.getpwnam('fallback-web')
    for path in [DATA.parent,DATA,DATA/'sessions']:
        path.mkdir(mode=0o700,exist_ok=True)
        path.chmod(0o700);os.chown(path,account.pw_uid,account.pw_gid)
    for name in ['auth.json','inventory.json']:
        install_bytes(DATA/name,(seed/name).read_bytes(),0o600)
        os.chown(DATA/name,account.pw_uid,account.pw_gid)
    install_bytes(POOL,blob('deploy/fallback-admin-pool.conf'))
    run('php-fpm8.3','-t')
    run('systemctl','reload','php8.3-fpm')
    for _ in range(20):
        if Path('/run/php/fallback-admin.sock').is_socket(): break
        time.sleep(.5)
    assert Path('/run/php/fallback-admin.sock').is_socket()
    verify_existing()

def http():
    assert not os.path.lexists(SITE) and not os.path.lexists(LINK)
    install_bytes(SITE,blob('deploy/lab-http.conf'))
    LINK.symlink_to(SITE)
    challenge=ROOT/'lab-public/.well-known/acme-challenge/fallbackhosting-activation'
    for directory in [ROOT/'lab-public/.well-known', challenge.parent]:
        if not directory.exists():
            directory.mkdir(mode=0o755)
            directory.chmod(0o755)
        assert directory.stat().st_mode & 0o005 == 0o005, 'Challenge directory not readable/traversable'
    install_bytes(challenge,b'fallbackhosting-activation-v1\n')
    reload_nginx()
    assert fetch('http://lab.ventureout.cz/.well-known/acme-challenge/fallbackhosting-activation')[3] == b'fallbackhosting-activation-v1\n'

def certificate():
    assert not Path('/etc/letsencrypt/live/lab.ventureout.cz').exists(), 'Do not request duplicate certificate'
    run('certbot','certonly','--webroot','-w',str(ROOT/'lab-public'),'-d','lab.ventureout.cz','--cert-name','lab.ventureout.cz','--non-interactive')
    assert Path('/etc/letsencrypt/live/lab.ventureout.cz/fullchain.pem').is_file()
    verify_existing()

def verify_app(check_existing=True):
    status,kind,final,body=fetch('https://lab.ventureout.cz/')
    assert status == 200 and kind == 'text/html' and b'name="password"' in body and b'ctx1' not in body
    assert fetch('https://lab.ventureout.cz/admin.css')[0:2] == (200,'text/css')
    for path in ['auth.json','inventory.json','lib.php','manage.php','.local/admin/auth.json','unknown']:
        assert fetch('https://lab.ventureout.cz/'+path)[0] == 404
    assert fetch('http://lab.ventureout.cz/')[2] == 'https://lab.ventureout.cz/'
    for name in ['lib.php','manage.php','public/index.php','public/admin.css']:
        assert (RELEASE/name).read_bytes() == blob('admin/'+name)
    if check_existing:
        verify_existing()
    print('PASS lab TLS/login/CSS/private-path denials/release integrity')

def https():
    assert SITE.read_bytes() == blob('deploy/lab-http.conf'), 'Unexpected lab configuration'
    install_bytes(SITE,blob('deploy/admin-lab-https.conf'))
    reload_nginx()
    verify_app(check_existing=False)

def rollback():
    # Preserve partial-state evidence and all data/certificates/releases/accounts.
    if os.path.lexists(LINK):
        assert LINK.is_symlink() and LINK.resolve() == SITE
        LINK.rename(BACKUP/'disabled-lab-symlink')
        if SITE.exists(): SITE.rename(BACKUP/'disabled-lab-config')
        reload_nginx()
    if POOL.exists():
        assert POOL.read_bytes() == blob('deploy/fallback-admin-pool.conf')
        POOL.rename(BACKUP/'disabled-fpm-pool')
        run('php-fpm8.3','-t');run('systemctl','reload','php8.3-fpm')
    verify_existing()

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase',choices=['prepare','http','certificate','https','verify','rollback'])
    phase=parser.parse_args().phase
    assert os.geteuid() == 0, 'Run with operator-authorized root execution'
    os.umask(0o077)
    if phase == 'prepare':
        assert not BACKUP.exists(), 'Existing activation journal: reconcile, do not replay prepare'
        BACKUP.mkdir(mode=0o700)
    assert BACKUP.is_dir() and BACKUP.stat().st_mode & 0o077 == 0
    if phase == 'verify':
        verify_app()
    else:
        started=BACKUP/(phase+'.started');done=BACKUP/(phase+'.done')
        assert not started.exists() and not done.exists(), 'Phase already started: inspect journal and actual state; do not replay'
        if phase not in ['prepare','rollback']:
            previous={'http':'prepare','certificate':'http','https':'certificate'}[phase]
            assert (BACKUP/(previous+'.done')).exists(), 'Previous phase incomplete'
            verify_existing()
        with started.open('x') as marker: marker.write(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+' '+REV+'\n')
        globals()[phase]()
        with done.open('x') as marker: marker.write(time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+'\n')
        print('PASS phase '+phase)
