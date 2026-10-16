"""Single-demo control adapter using the existing bounded Unix peer protocol.

This service has no SSH/Docker privileges, image execution or command API.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import selectors
import signal
import socket
import stat
import time

from operations.core import Denied, exact
from operations.protocol import serve_connection
from standby.gateway import atomic_json, maintenance_active, tick
from standby.snapshot import origin_url


class Control:
    def __init__(self, runtime, allowed_uid, actor, snapshot=None):
        self.runtime=Path(runtime);self.uid=allowed_uid;self.actor=actor;self.snapshot=snapshot or {}
        self.runtime.mkdir(parents=True,exist_ok=True)
        if not (self.runtime/'control.json').exists():atomic_json(self.runtime/'control.json',{'manual_maintenance':False,'windows':[]})
        if not (self.runtime/'api.json').exists():atomic_json(self.runtime/'api.json',{'revision':1,'audit':[]})

    def authorize(self, request, uid):
        if uid!=self.uid or request.get('actor')!=self.actor or request.get('app')!='demo':raise Denied('FORBIDDEN')

    def view(self):
        control=json.loads((self.runtime/'control.json').read_text());api=json.loads((self.runtime/'api.json').read_text())
        health=json.loads((self.runtime/'health.json').read_text()) if (self.runtime/'health.json').exists() else None
        return {'ok':True,'app':'demo','revision':api['revision'],'control':control,'health':health,
                'snapshot':self.snapshot,'audit':api['audit'][-10:]}

    def read(self, request, uid):
        exact(request,'kind actor app');self.authorize(request,uid)
        if request['kind']!='view':raise Denied('UNKNOWN_OPERATION')
        return self.view()

    def submit(self, request, uid):
        exact(request,'kind actor app revision params');self.authorize(request,uid)
        if request['kind']!='set_control':raise Denied('UNKNOWN_OPERATION')
        exact(request['params'],'manual_maintenance windows');params=request['params']
        if type(params['manual_maintenance']) is not bool or not isinstance(params['windows'],list) or len(params['windows'])>20:raise Denied('INVALID_CONTROL')
        try:maintenance_active(params['windows'],datetime.now(timezone.utc))
        except (ValueError,TypeError,KeyError):raise Denied('INVALID_WINDOW')
        api=json.loads((self.runtime/'api.json').read_text())
        if type(request['revision']) is not int or request['revision']!=api['revision']:raise Denied('STALE_REVISION')
        active=params['manual_maintenance'] or maintenance_active(params['windows'],datetime.now(timezone.utc))
        # Write-ahead audit intent; interrupted changes are visible and fail closed.
        (self.runtime/'unhealthy').touch()
        api['revision']+=1
        api['audit']=(api['audit']+[{'utc':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'actor':self.actor,
                                  'manual_maintenance':params['manual_maintenance'],'windows':params['windows'],'revision':api['revision']}])[-100:]
        atomic_json(self.runtime/'api.json',api)
        atomic_json(self.runtime/'control.json',params)
        atomic_json(self.runtime/'health.json',{'successes':0,'maintenance_recovery':True})
        marker=self.runtime/'maintenance'
        if active:marker.touch()
        elif marker.exists():marker.unlink()
        return self.view()


def run_server(listener, control, origin, seconds=None):
    origin=origin_url(origin);running=True
    def stop(*unused):
        nonlocal running
        running=False
    if __import__('threading').current_thread() is __import__('threading').main_thread():
        signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    (control.runtime/'unhealthy').touch()
    atomic_json(control.runtime/'health.json',{'successes':0,'maintenance_recovery':False})
    selector=selectors.DefaultSelector();selector.register(listener,selectors.EVENT_READ)
    deadline=time.monotonic()+seconds if seconds is not None else None;next_tick=0
    try:
        while running and (deadline is None or time.monotonic()<deadline):
            if time.monotonic()>=next_tick:
                try:tick(origin,control.runtime)
                except Exception:(control.runtime/'unhealthy').touch()
                next_tick=time.monotonic()+2
            for key,mask in selector.select(.2):
                connection,_=listener.accept();serve_connection(connection,control)
    finally:
        (control.runtime/'unhealthy').touch();selector.close()


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--policy',type=Path,required=True);p.add_argument('--socket-fd',type=int,default=3);args=p.parse_args()
    info=args.policy.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=0 or info.st_mode&0o022:raise ValueError('Root-owned immutable policy required')
    policy=json.loads(args.policy.read_text())
    if os.geteuid()!=policy['service_uid']:raise ValueError('Incorrect service identity')
    listener=socket.socket(fileno=args.socket_fd)
    control=Control(policy['runtime'],policy['web_uid'],policy['actor'],policy['snapshot'])
    run_server(listener,control,policy['origin'])


if __name__=='__main__':main()
