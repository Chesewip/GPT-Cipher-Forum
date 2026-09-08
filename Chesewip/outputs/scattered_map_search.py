"""Bounded unknown-map search for scattered fractionation codebooks.

Search failures are NOT exclusions. Moves exchange adjacent or arbitrary cube
cells, preserving the output substitution's bijectivity. No language model is used.
"""
from pathlib import Path
from collections import Counter
import json,random,math,time,argparse,hashlib
ROOT=Path(__file__).resolve().parent
WEIGHTS=(25,5,1)

def dependencies(messages,period,first,strip=False,reverse=False):
    sources=[];dep=[[] for _ in range(375)]
    for raw in messages:
        seq=raw[int(strip):]
        if reverse:seq=seq[::-1]
        lo=0;length=first
        while lo<len(seq):
            block=seq[lo:lo+length];n=len(block)
            for pos in range(n):
                cells=[]
                for axis in range(3):
                    j,d=divmod(axis*n+pos,3);cell=3*block[j]+d
                    cells.append(cell);dep[cell].append((len(sources),WEIGHTS[axis]))
                sources.append(cells)
            lo+=n;length=period
    return sources,dep

def decoded_values(key,sources):
    digits=[(key[label]//WEIGHTS[d])%5 for label in range(125) for d in range(3)]
    return [sum(WEIGHTS[a]*digits[cell] for a,cell in enumerate(row)) for row in sources]

def search(messages,period,first,strip,reverse,seed,steps,initial_key=None,perturb=0,move_set='mixed',temperature_start=3.0):
    started=time.monotonic();rng=random.Random(seed)
    sources,dep=dependencies(messages,period,first,strip,reverse)
    active=sorted({cell//3 for row in sources for cell in row})
    key=list(range(125)) if initial_key is None else list(initial_key)
    if initial_key is None:rng.shuffle(key)
    for _ in range(perturb):
        a,b=rng.sample(range(125),2);key[a],key[b]=key[b],key[a]
    initial=list(key);owner=[0]*125
    for label,code in enumerate(key):owner[code]=label
    values=decoded_values(key,sources);counts=[0]*125
    for v in values:counts[v]+=1
    n=len(values)
    # Occupied-cell cost plus smooth concentration reward; bounded heuristic.
    term=[0.0]+[1.0-0.1*k*math.log(k) for k in range(1,n+1)]
    energy=sum(term[x] for x in counts);support=sum(x>0 for x in counts)
    best=(support,energy);bestkey=list(key);trace=[[0,support,energy]];accepted=0
    for step in range(steps):
        a=rng.choice(active)
        if move_set=='mixed' and rng.random()<0.5:
            b=rng.randrange(125)
        else:
            axis=rng.randrange(3);oldcode=key[a];old=(oldcode//WEIGHTS[axis])%5
            new=rng.randrange(4);new+=new>=old
            b=owner[oldcode+(new-old)*WEIGHTS[axis]]
        changes={}
        for axis in range(3):
            shift=(key[b]//WEIGHTS[axis])%5-(key[a]//WEIGHTS[axis])%5
            if not shift:continue
            for pos,w in dep[3*a+axis]:changes[pos]=changes.get(pos,0)+shift*w
            for pos,w in dep[3*b+axis]:changes[pos]=changes.get(pos,0)-shift*w
        counts_delta={}
        for pos,delta in changes.items():
            if delta:
                before=values[pos];after=before+delta
                counts_delta[before]=counts_delta.get(before,0)-1
                counts_delta[after]=counts_delta.get(after,0)+1
        delta_energy=sum(term[counts[v]+d]-term[counts[v]] for v,d in counts_delta.items())
        temperature=temperature_start*(0.02/temperature_start)**(step/max(1,steps-1))
        if delta_energy<=0 or rng.random()<math.exp(-delta_energy/temperature):
            for pos,delta in changes.items():values[pos]+=delta
            for v,d in counts_delta.items():
                support+=(counts[v]+d>0)-(counts[v]>0);counts[v]+=d
            key[a],key[b]=key[b],key[a];owner[key[a]]=a;owner[key[b]]=b
            energy+=delta_energy;accepted+=1
            if (support,energy)<best:
                best=(support,energy);bestkey=list(key)
        if (step+1)%10000==0:
            # Periodic whole-state audit of incremental scoring and routing.
            assert values==decoded_values(key,sources)
            assert Counter(values)==Counter({v:c for v,c in enumerate(counts) if c})
            assert abs(energy-sum(term[x] for x in counts))<1e-7
            trace.append([step+1,best[0],best[1]])
    decoded=decoded_values(bestkey,sources)
    assert len(set(decoded))==best[0] and sorted(bestkey)==list(range(125))
    return dict(seed=seed,steps=steps,period=period,first_block=first,strip_first=strip,reverse=reverse,
                initialization='blind random permutation' if initial_key is None else 'planted permutation with perturbations',
                initial_perturbation_swaps=perturb,move_set=move_set,temperature_start=temperature_start,
                initial_key=initial,best_key=bestkey,
                best_support=best[0],best_energy=best[1],decoded=decoded,trace=trace,
                accepted_moves=accepted,seconds=time.monotonic()-started)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--steps',type=int,default=100000)
    ap.add_argument('--phase',choices=['calibrate','eyes'],default='calibrate')
    ap.add_argument('--move-set',choices=['adjacent','mixed'],default='mixed');a=ap.parse_args()
    source=(ROOT/'scattered_coordinate_control.json').read_bytes();control=json.loads(source)
    out=dict(status='Bounded heuristic search, not an exclusion or decipherment.',
             control_sha256=hashlib.sha256(source).hexdigest(),move_set=a.move_set,objective='occupied cells minus 0.1 * sum(count * log(count))',runs=[])
    target=ROOT/('scattered_map_'+a.phase+'.json')
    def save():target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    if a.phase=='calibrate':
        inverse=[0]*125
        for code,label in enumerate(control['coordinate_code_to_output_label']):inverse[label]=code
        configurations=[(907420,inverse,5),(907421,inverse,20),(907422,None,0),(907423,None,0),(907424,None,0)]
        for seed,key,perturb in configurations:
            r=search(control['ciphertext'],7,7,False,False,seed,a.steps,key,perturb,a.move_set)
            out['runs'].append(r);save()
            print(seed,r['initialization'],'support',r['best_support'],'seconds',round(r['seconds'],2),flush=True)
    else:
        raw_bytes=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(raw_bytes).values())
        out['ciphertext_sha256']=hashlib.sha256(raw_bytes).hexdigest()
        out['scope']='Exploratory fixed periods 2,3,5,7,11,13; full first blocks; strip first symbol, forward only.'
        for period in [2,3,5,7,11,13]:
            r=search(messages,period,period,True,False,907430+period,a.steps,move_set=a.move_set)
            out['runs'].append(r);save()
            print('Eyes period',period,'support',r['best_support'],'seconds',round(r['seconds'],2),flush=True)

if __name__=='__main__':main()
