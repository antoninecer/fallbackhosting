"""Operator-only fixed-script SSH transport; never exposed to PHP/web inputs."""
import base64
import json
import os
import pwd
from pathlib import Path
import re
import subprocess


def fixed_script(source, payload, node):
    host, user, port = node['host'], node['ssh_user'], node['ssh_port']
    if not re.fullmatch(r'[A-Za-z0-9.:-]+',host) or host.startswith('-') or not re.fullmatch(r'[a-z_][a-z0-9_-]{0,31}',user) or type(port) is not int or not 1<=port<=65535:
        raise ValueError('Invalid private endpoint mapping')
    encoded=base64.b64encode(json.dumps(payload).encode()).decode()
    code=Path(source).read_text()
    if code.count('PAYLOAD_PLACEHOLDER')!=1:raise ValueError('Fixed payload binding missing or repeated')
    code=code.replace('PAYLOAD_PLACEHOLDER',"json.loads(__import__('base64').b64decode("+repr(encoded)+"))")
    prefix=[] if os.geteuid()==pwd.getpwnam('fallback-agent').pw_uid else ['sudo','-n','-u','fallback-agent']
    args=prefix+['ssh','-o','BatchMode=yes','-o','ConnectTimeout=5','-o','HostKeyAlgorithms=ssh-ed25519','-o','StrictHostKeyChecking=yes','-o','UpdateHostKeys=no','-o','ForwardAgent=no','-o','ClearAllForwardings=yes','-T','-p',str(port),user+'@'+host,'python3','-']
    result=subprocess.run(args,input=code,text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=180)
    if result.returncode:raise RuntimeError('Fixed remote action failed; reconcile before retry')
    if len(result.stdout)>48*1024*1024:raise ValueError('Oversized remote reply')
    return json.loads(result.stdout)
