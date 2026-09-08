"""Complete partially recovered feedback maps using an input-codebook bound.

Enumerates at most two normalized linear parameters, then completes unknown
output labels with permutation, feedback, and training-only codebook checks.
No held-out message enters candidate generation or selection.
"""
from pathlib import Path
import hashlib,itertools,json
import numpy as np
from lifted_feedback_recovery import rows_for
from frozen_candidate_search import table,evaluate
ROOT=Path(__file__).resolve().parent

def fiber(messages,equalities):
    rows=rows_for(messages,equalities);inactive=[j for j in range(166) if not any(row[j] for row in rows)]
    common=[j for j in range(83) if j not in inactive and j+83 not in inactive]
    if len(common)<2:return dict(status='insufficient_common_anchors')
    a,b=common[:2];fixed=[(a,0),(b,1),(83+a,0)]+[(j,0) for j in inactive]
    mat=np.array([row+[0] for row in rows]+[[int(j==i) for j in range(166)]+[v] for i,v in fixed],dtype=np.int64)
    rank=0;pivots=[]
    for col in range(166):
        choices=np.flatnonzero(mat[rank:,col])
        if not len(choices):continue
        chosen=rank+int(choices[0]);mat[[rank,chosen]]=mat[[chosen,rank]]
        mat[rank]=mat[rank]*pow(int(mat[rank,col]),-1,83)%83
        mult=mat[:,col].copy();mult[rank]=0;mat=(mat-mult[:,None]*mat[rank])%83;pivots.append(col);rank+=1
    if any(not row[:166].any() and row[166] for row in mat):return dict(status='normalization_inconsistent')
    free=sorted(set(range(166))-set(pivots));base=np.zeros(166,dtype=np.int64);base[pivots]=mat[:rank,166];vs=[]
    for j in free:
        v=np.zeros(166,dtype=np.int64);v[j]=1;v[pivots]=-mat[:rank,j]%83;vs.append(v.tolist())
    return dict(status='normalized_affine_fiber',anchors=[a,b],inactive_columns=inactive,
        normalized_dimension=len(free),particular=base.tolist(),directions=vs,nonzero_rows=len(rows))

def link_parameters(name,u,v,common,anchor):
    f=table(name)
    # Addition has a free affine gauge; one representative suffices for every
    # key/codebook completion modulo a shared affine output renumbering.
    pairs=[(1,0)] if name=='add' else itertools.product(range(1,83),range(83))
    for scale,shift in pairs:
        const=int(f[shift])
        if all((int(f[(scale*u[j]+shift)%83])-scale*v[j])%83==const for j in common):yield scale,shift

def complete_labels(messages,name,u,v,inactive,scale,shift,cap=27,max_missing=8):
    missing=[j for j in range(83) if j in inactive]
    if len(missing)>max_missing:return dict(status='missing_label_budget',keys=[],nodes=0)
    known=[j for j in range(83) if j not in missing];f=table(name)
    key={j:(scale*u[j]+shift)%83 for j in known};available=set(range(83))-set(key.values())
    allowed=set(range(83))-{(x-int(f[x]))%83 for x in range(83)}
    edges=sorted({(m[t-1],m[t]) for m in messages[:6] for t in range(2,len(m))})
    initial_codes={(key[b]-int(f[key[a]]))%83 for a,b in edges if a in key and b in key}
    if len(initial_codes)>cap or not initial_codes<=allowed:return dict(status='partial_codebook_rejected',keys=[],nodes=0)
    incident={j:[e for e in edges if j in e] for j in missing};order=sorted(missing,key=lambda j:(-len(incident[j]),j));results=[];nodes=0
    def visit(depth,codes):
        nonlocal nodes
        nodes+=1
        if depth==len(order):results.append(dict(key=[key[j] for j in range(83)],codebook=sorted(codes)));return
        label=order[depth]
        for value in sorted(available):
            if label+83 not in inactive and (int(f[value])-scale*v[label])%83!=int(f[shift]):continue
            key[label]=value
            new={(key[b]-int(f[key[a]]))%83 for a,b in incident[label] if a in key and b in key};merged=codes|new
            if len(merged)<=cap and merged<=allowed:
                available.remove(value);visit(depth+1,merged);available.add(value)
            del key[label]
    visit(0,initial_codes)
    return dict(status='completion_enumerated',keys=results,nodes=nodes,initial_codebook=sorted(initial_codes),missing_labels=missing)

def recover(messages,equalities,max_dimension=2):
    info=fiber(messages,equalities);out=dict(fiber=info,dimension_budget=max_dimension,missing_label_budget=8)
    if info['status']!='normalized_affine_fiber' or info['normalized_dimension']>max_dimension:
        out['status']='outside_enumeration_budget';return out
    inactive=set(info['inactive_columns']);active=[j for j in range(83) if j not in inactive]
    common=[j for j in active if j+83 not in inactive];base=np.array(info['particular']);directions=[np.array(v) for v in info['directions']]
    out.update(status='enumerated_candidates',fibers_tested=83**len(directions),injective_output_fibers=[],link_counts={n:0 for n in ['add','square','inverse']},completion_nodes=0,candidates=[])
    for coefficients in itertools.product(range(83),repeat=len(directions)):
        vector=base.copy()
        for coefficient,v in zip(coefficients,directions):vector=(vector+coefficient*v)%83
        u=vector[:83].tolist();v=vector[83:].tolist()
        if len({u[j] for j in active})!=len(active):continue
        out['injective_output_fibers'].append(list(coefficients))
        for name in ['add','square','inverse']:
            for scale,shift in link_parameters(name,u,v,common,info['anchors'][0]):
                out['link_counts'][name]+=1
                c=complete_labels(messages,name,u,v,inactive,scale,shift)
                out['completion_nodes']+=c['nodes']
                for candidate in c['keys']:
                    candidate.update(name=name,coefficients=list(coefficients),scale=scale,shift=shift)
                    out['candidates'].append(candidate)
    # No late scores, true keys, or plaintext are used in this ordering.
    out['candidates'].sort(key=lambda c:(c['name'],c['key']))
    out['selected_candidate']=0 if out['candidates'] else None
    return out

def main():
    raw=(ROOT/'lifted_feedback_recovery.json').read_bytes();source=json.loads(raw)
    short_raw=(ROOT/'frozen_candidate_search.json').read_bytes();short=json.loads(short_raw)
    out=dict(executed_date='2026-09-08',status='Sparse linear-map completion calibration; no Eye key.',
        rich_parent_sha256=hashlib.sha256(raw).hexdigest(),short_parent_sha256=hashlib.sha256(short_raw).hexdigest(),controls=[],short_controls=[])
    for c in source['controls']:
        selected_blocks=5 if c['name']=='add' else 4
        for blocks in [3,selected_blocks]:
            eq=c['training_equalities'][:blocks*5];r=recover(c['ciphertext'],eq)
            entry=dict(seed=c['seed'],true_name=c['name'],blocks=blocks,training_equalities=eq,result=r)
            if r.get('selected_candidate') is not None:
                chosen=r['candidates'][r['selected_candidate']];entry['heldout']=evaluate(c['ciphertext'],c['late_equalities'],chosen)
            out['controls'].append(entry)
            print(c['name'],blocks,'dimension',r['fiber'].get('normalized_dimension'),'status',r['status'],'injective fibers',len(r.get('injective_output_fibers',[])),'keys',len(r.get('candidates',[])),flush=True)
    for c in short['controls']:
        r=recover(c['ciphertext'],short['early_equalities']);out['short_controls'].append(dict(seed=c['seed'],result=r))
    messages=list(json.loads((ROOT/'ciphertext.json').read_bytes()).values())
    out['eye']=recover(messages,short['early_equalities']);print('Eye dimension',out['eye']['fiber'].get('normalized_dimension'),flush=True)
    (ROOT/'sparse_map_completion.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')

if __name__=='__main__':main()
