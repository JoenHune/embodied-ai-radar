"""Cutoff-scoped status-query checkpoints preserving actual observation clocks."""
import hashlib,json,time
from datetime import datetime,timezone
from weekly_runtime import query_budget,QueryBudgetExpired,resource_reason

def fetchers(folder,cutoff,metadata,status):
    folder.mkdir(parents=True,exist_ok=True)
    clock=[datetime.now(timezone.utc).isoformat()]
    times=[]
    last=[0.0]
    def wrapped(kind,fn,args):
        # Attempt clocks are not part of request identity.
        identity=hashlib.sha256(json.dumps([kind,cutoff,args if kind=='metadata' else args[:2],1],sort_keys=True).encode()).hexdigest()
        path=folder/(identity+'.json')
        value=json.loads(path.read_text()) if path.exists() else {}
        if value.get('identity')==identity:
            clock[0]=value['observed_at'];times.append(clock[0])
            print(json.dumps({'status':'status_query_checkpoint_reused','kind':kind,'observed_at':clock[0]}),flush=True)
            return value['result']
        why=resource_reason()
        if why:raise RuntimeError(why)
        delay=max(0,3-(time.monotonic()-last[0]))
        if delay:time.sleep(delay)
        clock[0]=datetime.now(timezone.utc).isoformat()
        try:
            with query_budget(30):result=fn(*args)
        except QueryBudgetExpired:
            raise TimeoutError('StatusRequestBudgetExceeded') from None
        finally:
            last[0]=time.monotonic()
        value={'identity':identity,'observed_at':clock[0],'result':result}
        pending=path.with_suffix('.tmp');pending.write_text(json.dumps(value));pending.replace(path)
        times.append(clock[0])
        print(json.dumps({'status':'status_query_checkpoint_saved','kind':kind,'observed_at':clock[0]}),flush=True)
        return result
    return (lambda ids:wrapped('metadata',metadata,(ids,)),
            lambda *args:wrapped('status',status,args),lambda:clock[0],times)
