#!/usr/bin/env python3
"""Explicit operator exercise on intended test node; never installed/run by broker."""
import argparse
from datetime import datetime, timezone
import json
import os
import re
import tempfile
from pathlib import Path
import subprocess
import uuid

class ExerciseFailure(RuntimeError): pass

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-owned-test',action='store_true')
    args=parser.parse_args()
    if not args.execute_owned_test:parser.error('--execute-owned-test is required; no Docker command executed')
    os.umask(0o077)
    token=uuid.uuid4().hex;name='fallbackhosting-exercise-'+token
    journal=Path(tempfile.mkdtemp(prefix=name+'-'))/'journal.json'
    state={'owner':token,'name':name,'container_id':None,'phases':[],'cleanup':'NOT_NEEDED'}
    def record(phase,status):
        event={'phase':phase,'status':status,'utc':datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}
        state['phases'].append(event)
        pending=journal.with_suffix('.tmp');pending.write_text(json.dumps(state,indent=2)+'\n');pending.replace(journal)
        print(json.dumps(event),flush=True)
    def run(*parts,timeout=20,missing=False):
        r=subprocess.run(['/usr/bin/docker',*parts],capture_output=True,text=True,timeout=timeout)
        if r.returncode and not missing:
            state['docker_stdout_private']=r.stdout[:4096];state['docker_stderr_private']=r.stderr[:4096]
            diagnostic=(r.stdout+' '+r.stderr).lower()
            categories={key:(phrase in diagnostic) for key,phrase in {'permission_denied':'permission denied','operation_not_permitted':'operation not permitted','missing_path':'no such file or directory','cgroup':'cgroup','read_only':'read-only','apparmor':'apparmor','mount':'mount','memory':'memory','cpu':'cpu','pids':'pids','runtime':'runc','executable':'exec','user_setup':'user','argument':'argument','authorization':'authorization','unsupported':'not supported'}.items()}
            state['failed_docker_command']=parts[0];state['docker_failure_categories']=categories
            raise ExerciseFailure('DOCKER_COMMAND_FAILED')
        return r
    def inspect(target):
        r=run('inspect',target,missing=True)
        return json.loads(r.stdout)[0] if r.returncode==0 else None
    def owns(item):
        return isinstance(item,dict) and item.get('Config',{}).get('Labels',{}).get('io.fallbackhosting.exercise')==token and item['Config']['Labels'].get('io.fallbackhosting.managed')=='true'
    def original_snapshot(ids):
        result={}
        for cid in ids:
            data=inspect(cid)
            if data is None:raise ExerciseFailure('REFERENCE_UNAVAILABLE')
            result[cid]={key:data[key] for key in ('Id','Image','RestartCount')}
            result[cid].update({key:data['State'][key] for key in ('Running','StartedAt')})
        return result
    existing=run('ps','-aq','--no-trunc').stdout.split()
    if not existing or len(existing)>50 or any(not re.fullmatch(r'[a-f0-9]{64}',cid) for cid in existing):raise ExerciseFailure('BOUNDED_REFERENCE_REQUIRED')
    baseline=original_snapshot(existing)
    image=next(iter(baseline.values()))['Image']
    if not re.fullmatch(r'sha256:[a-f0-9]{64}',image):raise ExerciseFailure('IMMUTABLE_IMAGE_REQUIRED')
    image_info=json.loads(run('image','inspect',image).stdout)[0]
    if image_info.get('Config',{}).get('Volumes'):raise ExerciseFailure('IMAGE_DECLARES_ANONYMOUS_VOLUMES')
    journal.touch(mode=0o600,exist_ok=False)
    record('baseline','PASS')
    error=None
    try:
        record('create','STARTED')
        created=run('create','--name',name,'--label','io.fallbackhosting.managed=true','--label','io.fallbackhosting.project=exercise','--label','io.fallbackhosting.app='+name[:39],'--label','io.fallbackhosting.node=ctx1','--label','io.fallbackhosting.exercise='+token,'--network','none','--read-only','--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','64m','--cpus','0.25','--pids-limit','32','--log-driver','local','--log-opt','max-size=1m','--log-opt','max-file=2','--entrypoint','/bin/sh',image,'-c','echo fallbackhosting-exercise; exec sleep 120').stdout.strip()
        if not re.fullmatch(r'[a-f0-9]{64}',created):raise ExerciseFailure('CREATE_ID_UNKNOWN')
        state['container_id']=created;state['cleanup']='REQUIRED';record('create','PASS')
        item=inspect(created)
        checks={'ownership':owns(item),'exact_id':item['Id']==created,'no_mounts':not item.get('Mounts'),'network_none':item['HostConfig']['NetworkMode']=='none','no_ports':not item['HostConfig'].get('PortBindings'),'read_only':item['HostConfig']['ReadonlyRootfs']}
        state['isolation_checks']=checks;record('isolation_checks','PASS' if all(checks.values()) else 'FAIL')
        if not all(checks.values()):raise ExerciseFailure('CREATED_RESOURCE_ISOLATION_FAILED')
        run('start',created);started=inspect(created)
        if not owns(started) or not started['State']['Running']:raise ExerciseFailure('START_UNVERIFIED')
        record('start_inspect','PASS')
        logs=run('logs','--tail','5',created).stdout
        if 'fallbackhosting-exercise' not in logs:raise ExerciseFailure('BOUNDED_LOG_UNVERIFIED')
        record('bounded_logs','PASS')
        run('restart','--time','3',created);restarted=inspect(created)
        if not owns(restarted) or not restarted['State']['Running'] or restarted['State']['StartedAt']==started['State']['StartedAt']:raise ExerciseFailure('RESTART_UNVERIFIED')
        record('restart','PASS')
        run('stop','--time','3',created);stopped=inspect(created)
        if not owns(stopped) or stopped['State']['Running']:raise ExerciseFailure('STOP_UNVERIFIED')
        record('stop','PASS')
    except Exception as failure:
        error=str(failure) if isinstance(failure,ExerciseFailure) else type(failure).__name__
        state['failure_code']=error;record('exercise','FAILED_OR_UNKNOWN')
    finally:
        owned=inspect(state['container_id'] or name)
        if owned is not None:
            if not owns(owned):raise ExerciseFailure('CLEANUP_OWNERSHIP_MISMATCH')
            state['container_id']=owned['Id']
            if owned['State']['Running']:run('stop','--time','3',owned['Id'])
            run('rm',owned['Id'])
        remaining=run('ps','-aq','--no-trunc','--filter','label=io.fallbackhosting.exercise='+token).stdout.strip()
        if remaining or inspect(state['container_id'] or name) is not None:raise ExerciseFailure('CLEANUP_ABSENCE_UNVERIFIED')
        state['cleanup']='ABSENCE_VERIFIED';record('exact_remove_absence','PASS')
        if original_snapshot(existing)!=baseline:raise ExerciseFailure('REFERENCE_CHANGED')
        record('original_reference_unchanged','PASS')
    print(json.dumps({'result':'PASS' if error is None else error,'cleanup':state['cleanup'],'original_count':len(existing),'original_reference_unchanged':True,'image_pull':False,'network':'none','ports':False,'mounts_or_volumes':False,'journal_directory':journal.parent.name,'failed_docker_command':state.get('failed_docker_command'),'failure_categories':state.get('docker_failure_categories')}),flush=True)
    if error:raise ExerciseFailure(error)

if __name__=='__main__':
    try:main()
    except Exception:
        print(json.dumps({'result':'FAILED_OR_UNKNOWN','next':'Inspect exact private journal and owned resource before any retry'}),flush=True)
        raise SystemExit(1)
