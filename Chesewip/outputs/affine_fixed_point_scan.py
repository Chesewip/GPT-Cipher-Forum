"""Search partial isomorph maps for violations of affine fixed-point bounds."""
from pathlib import Path
import json,time,argparse,collections
from progressive_reduction import RUNS
ROOT=Path(__file__).resolve().parent

def observed_maps(ct,trim=1):
    maps=[]
    for i,s,j,t,n in RUNS:
        a=ct[i][s+trim-1:s+n];b=ct[j][t+trim-1:t+n];d={}
        for x,y in zip(a,b):
            assert x not in d or d[x]==y;d[x]=y
        assert len(set(d.values()))==len(d);maps.append(d)
    return maps

def scan(maps,max_depth=12,state_limit=500000,verbose=True):
    start=time.time();generators={i+1:d for i,d in enumerate(maps)};generators.update({-i:{v:k for k,v in d.items()} for i,d in list(generators.items())})
    def violation(mapping,word,kind):
        fixed=[x for x,y in mapping.items() if x==y];moved=[(x,y) for x,y in mapping.items() if x!=y]
        if len(fixed)>=(1 if kind=='commutator_translation' else 2) and moved:return dict(kind=kind,word=list(word),fixed=fixed,moved=moved,mapping=sorted(mapping.items()))
    # A commutator's multiplier is 1, so one fixed point makes it identity.
    commutators=0
    for a in generators:
        for b in generators:
            if abs(a)==abs(b):continue
            word=[a,b,-a,-b];d={x:x for x in range(83)}
            for g in word:d={x:generators[g][y] for x,y in d.items() if y in generators[g]}
            commutators+=1;r=violation(d,word,'commutator_translation')
            if r:return dict(status='affine_obstruction',witness=r,commutators_checked=commutators,seconds=time.time()-start)
    level=[(tuple([g]),d) for g,d in generators.items()];seen={tuple(sorted(d.items())) for _,d in level};counts=[]
    for depth in range(1,max_depth+1):
        counts.append(dict(depth=depth,states=len(level)))
        if verbose:print('depth',depth,'states',len(level),'seen',len(seen),flush=True)
        nxt=[]
        for word,d in level:
            r=violation(d,word,'two_fixed_points')
            if r:return dict(status='affine_obstruction',witness=r,levels=counts,commutators_checked=commutators,seconds=time.time()-start)
            if depth==max_depth:continue
            for g,gen in generators.items():
                if g==-word[-1]:continue
                new={x:gen[y] for x,y in d.items() if y in gen}
                if len(new)<3:continue
                sig=tuple(sorted(new.items()))
                if sig in seen:continue
                seen.add(sig);nxt.append((word+(g,),new))
                if len(seen)>=state_limit:return dict(status='state_limit',levels=counts,unique_partial_maps=len(seen),commutators_checked=commutators,seconds=time.time()-start)
        if not nxt:break
        level=nxt
    return dict(status='no_obstruction_in_completed_partial_map_search',levels=counts,unique_partial_maps=len(seen),commutators_checked=commutators,seconds=time.time()-start,scope='All enumerated words use only observed edges. This is not an affine model fit or a key recovery.')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--trim',type=int,default=1);ap.add_argument('--depth',type=int,default=12);a=ap.parse_args();ct=list(json.loads((ROOT/'ciphertext.json').read_text()).values());maps=observed_maps(ct,a.trim);r=scan(maps,a.depth);r['trim']=a.trim;r['observed_maps']=[sorted(d.items()) for d in maps]
    (ROOT/f'affine_fixed_point_scan_trim{a.trim}.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n');print({k:v for k,v in r.items() if k!='observed_maps'},flush=True)
