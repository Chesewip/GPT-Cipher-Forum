"""Use assumed plaintext equalities to bound relative update support.

Shared plaintext at aligned time t forces the paired deck-label relation at
outputs t-1 and t to agree. Contract those observations into partial-bijection
blocks, then count mandatory row changes across windows of blocks.
"""
from pathlib import Path
import json,itertools,time
from progressive_reduction import RUNS
from permutation_action_fold import make_plaintexts
ROOT=Path(__file__).resolve().parent

def assumptions(messages,trim=1):
    eq=[(i,s+trim,j,t+trim,n-trim) for i,s,j,t,n in RUNS]
    for i in range(len(messages)):
        for j in range(i):
            t=1
            while t<min(len(messages[i]),len(messages[j])) and messages[i][t]==messages[j][t]:t+=1
            if t>1:eq.append((i,1,j,1,t-1))
    return eq

def blocks(a,b,pa,pb,n):
    starts=[0]+[t for t in range(1,len(a)) if pa[t]!=pb[t]]+[len(a)];out=[]
    for lo,hi in zip(starts,starts[1:]):
        f={};inverse={}
        for x,y in zip(a[lo:hi],b[lo:hi]):
            if (x in f and f[x]!=y) or (y in inverse and inverse[y]!=x):return None
            f[x]=y;inverse[y]=x
        out.append({'lo':lo,'hi':hi,'mapping':f})
    return out

def scan_blocks(bs,n):
    full=(1<<n)-1
    domains=[]
    for b in bs:
        f=b['mapping'];used=sum(1<<y for y in f.values())
        domains.append([(1<<f[x]) if x in f else full^used for x in range(n)])
    strongest={'ratio':0,'minimum_entry_changes':0,'available_differences':0}
    for start in range(len(bs)-1):
        possible=domains[start].copy();cost=0
        for end in range(start+1,len(bs)):
            for row in range(n):
                hit=possible[row]&domains[end][row]
                if hit:possible[row]=hit
                else:cost+=1;possible[row]=domains[end][row]
            budget=end-start;ratio=cost/budget
            if ratio>strongest['ratio']:
                strongest={'ratio':ratio,'minimum_entry_changes':cost,'available_differences':budget,
                           'block_indices':[start,end],'output_window':[bs[start]['lo'],bs[end]['hi']]}
    return strongest

def scan(messages,pts,n=83):
    locations={}
    for i,pt in enumerate(pts):
        for t,letter in enumerate(pt):locations.setdefault(letter,[]).append((i,t))
    alignments=set()
    for occ in locations.values():
        for (i,s),(j,t) in itertools.combinations(occ,2):
            if i>j:i,s,j,t=j,t,i,s
            if i==j and s==t:continue
            alignments.add((i,j,t-s))
    results=[]
    for i,j,offset in sorted(alignments):
        sa=max(0,-offset);sb=max(0,offset);length=min(len(messages[i])-sa,len(messages[j])-sb)
        if length<2:continue
        a=messages[i][sa:sa+length];b=messages[j][sb:sb+length];pa=pts[i][sa:sa+length];pb=pts[j][sb:sb+length]
        same=sum(x==y for x,y in zip(pa,pb))
        if same<2:continue
        bs=blocks(a,b,pa,pb,n)
        if bs is None:
            results.append({'status':'inconsistent_equalities','messages':[i,j],'offset':offset});continue
        forward=scan_blocks(bs,n);reverse=scan_blocks([dict(x,mapping={v:k for k,v in x['mapping'].items()}) for x in bs],n)
        r=forward if forward['ratio']>=reverse['ratio'] else reverse
        results.append({'status':'bound','messages':[i,j],'offset':offset,'starts':[sa,sb],'shared_input_positions':same,
                        'relation_blocks':len(bs),'inverse_used':r is reverse,**r})
    return results

if __name__=='__main__':
    messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values());out=[]
    for trim in [1,2,3]:
        eq=assumptions(messages,trim);pts=make_plaintexts(messages,eq);start=time.time();rows=scan(messages,pts)
        best=sorted(rows,key=lambda r:r.get('ratio',100),reverse=True)
        result={'trim':trim,'seconds':time.time()-start,'assumed_equalities':eq,'alignments':rows,
                'excluded_support_5':any(r['status']!='bound' or r['ratio']>5 for r in rows)}
        out.append(result);print('trim',trim,'seconds',result['seconds'],'alignments',len(rows),'top',best[:4],flush=True)
    (ROOT/'shared_update_support.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
