"""Inert in-memory Docker fixture. It never calls Docker, SSH or a shell."""
import copy
import hashlib

class FakeDriver:
    def __init__(self):
        self.containers={};self.calls=[];self.fail=None;self.logs='example log\n'
    def inspect(self,node,cid,**limits):
        self.calls.append(('inspect',node,cid))
        return copy.deepcopy(self.containers.get((node,cid)))
    def execute(self,node,action,params,**limits):
        self.calls.append((action,node,copy.deepcopy(params)))
        if self.fail:raise self.fail
        if action=='deploy':
            cid=hashlib.sha256((node+str(len(self.containers))+params['labels']['io.fallbackhosting.app']).encode()).hexdigest()
            self.containers[(node,cid)]={'id':cid,'labels':copy.deepcopy(params['labels']),'state':'created'}
            return {'id':cid}
        cid=params['container_id'];container=self.containers[(node,cid)]
        if action=='logs':return {'logs':self.logs}
        if action=='remove':del self.containers[(node,cid)]
        elif action=='stop':container['state']='exited'
        elif action in {'start','restart'}:container['state']='running'
        else:raise AssertionError('Unknown fixture action')
        return {}
