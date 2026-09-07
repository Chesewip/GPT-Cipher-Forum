from pathlib import Path
import sys,json,time,argparse
ROOT=Path(__file__).resolve().parent
from return_path_bv import build
from shared_update_support import assumptions
import z3
ap=argparse.ArgumentParser();ap.add_argument('--gap',type=int,default=12);ap.add_argument('--milliseconds',type=int,default=1000);ap.add_argument('--trim',type=int,default=1);args=ap.parse_args()
ct=list(json.loads((ROOT/'ciphertext.json').read_text()).values());eq=assumptions(ct,args.trim)
solver,b,pt,counts=build(ct,83,eq,args.gap);solver.set(timeout=args.milliseconds)
print('counts',counts,flush=True);results=[]
for offset in range(82):
    started=time.time();solver.push();solver.add(b==offset);status=solver.check();r={'rotation':offset,'status':str(status),'seconds':time.time()-started}
    if status==z3.unknown:r['reason']=solver.reason_unknown()
    solver.pop();results.append(r)
    if status!=z3.sat or offset%10==0:print(r,flush=True)
out={'gap':args.gap,'trim':args.trim,'assumed_equalities':eq,'counts':counts,'results':results,'warning':'Conditional return-path relaxation. SAT is not a key. Unknown is inconclusive.'}
(ROOT/f'short_return_scan_{args.gap}_{args.trim}.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
