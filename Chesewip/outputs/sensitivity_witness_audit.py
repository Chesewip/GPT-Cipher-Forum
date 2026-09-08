"""Audit the saved minimum-column linear witness and bounded occurrence pilots."""
from pathlib import Path
import hashlib,itertools,json,random
import numpy as np
from equality_sensitivity import Problem
ROOT=Path(__file__).resolve().parent

def normalized_fiber(problem,dropped):
    rows=[problem.eqs[i]['row'] for i in problem.active(dropped)]
    active=sorted({j for row in rows for j,x in enumerate(row) if x});inactive=sorted(set(range(83))-set(active));anchors=active[:2]
    matrix=np.array([row+[0] for row in rows]+[[int(j==i) for j in range(83)]+[int(i==anchors[1])] for i in inactive+anchors],dtype=np.int64)
    rank=0;pivots=[]
    for j in range(83):
        found=next((i for i in range(rank,len(matrix)) if matrix[i,j]),None)
        if found is None:continue
        matrix[[rank,found]]=matrix[[found,rank]];matrix[rank]=matrix[rank]*pow(int(matrix[rank,j]),-1,83)%83
        mult=matrix[:,j].copy();mult[rank]=0;matrix=(matrix-mult[:,None]*matrix[rank])%83;pivots.append(j);rank+=1
    assert not any(not row[:83].any() and row[83] for row in matrix)
    base=np.zeros(83,dtype=np.int64);base[pivots]=matrix[:rank,83];directions=[]
    for j in sorted(set(range(83))-set(pivots)):
        v=np.zeros(83,dtype=np.int64);v[j]=1;v[pivots]=-matrix[:rank,j]%83;directions.append(v)
    assert len(directions)<=2
    collisions=[];survivors=[]
    for co in itertools.product(range(83),repeat=len(directions)):
        v=base.copy()
        for c,w in zip(co,directions):v=(v+c*w)%83
        seen={};pair=None
        for label in active:
            value=int(v[label])
            if value in seen:pair=[seen[value],label];break
            seen[value]=label
        collisions.append(pair)
        if pair is None:survivors.append(list(co))
    return dict(active_labels=active,inactive_labels=inactive,anchors=anchors,
                particular=base.tolist(),directions=[v.tolist() for v in directions],
                candidates=len(collisions),collision_pairs=collisions,injective_candidates=survivors)

def main():
    data=(ROOT/'equality_sensitivity.json').read_bytes();source=json.loads(data)
    messages=list(json.loads((ROOT/'ciphertext.json').read_bytes()).values());eq=source['assumption_sets']['strong']
    col=source['real']['strong']['columns'];p=Problem(messages,eq,'columns')
    out=dict(parent_sha256=hashlib.sha256(data).hexdigest(),status='Saved minimum-column witness fails bijection; bounded occurrence upper witnesses are only linear.',
        joint_column_map=normalized_fiber(p,col['dropped']),occurrence_pilots=[])
    q=Problem(messages,eq,'occurrences')
    seed_positions={q.pos_index[tuple(pos)] for i in col['dropped'] for pos in col['groups'][i]}
    for seed in list(range(909720,909728))+list(range(909730,909738)):
        initial=seed_positions if seed<909730 else set(range(len(q.units)))
        order=sorted(initial);random.Random(seed).shuffle(order);dropped=set(initial)
        for unit in order:
            trial=dropped-{unit};r=q.run_rows(q.active(trial))
            if r['status']=='no_forced_collision':dropped=trial
        r=q.run_rows(q.active(dropped));assert r['status']=='no_forced_collision'
        out['occurrence_pilots'].append(dict(seed=seed,start='saved_column_witness' if seed<909730 else 'all_occurrences',dropped=sorted(dropped),result=r))
    out['best_occurrence_upper_bound']=min(len(r['dropped']) for r in out['occurrence_pilots'])
    (ROOT/'sensitivity_witness_audit.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
    print('Normalized active-map candidates',out['joint_column_map']['candidates'],'injective',len(out['joint_column_map']['injective_candidates']))
    print('Occurrence greedy costs',[(r['seed'],len(r['dropped'])) for r in out['occurrence_pilots']])

if __name__=='__main__':main()
