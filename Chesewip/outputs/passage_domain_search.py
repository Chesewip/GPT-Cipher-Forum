"""Combine passage-equation support, permutation and alphabet-cap propagation.

Blind searches use no true-key entries. An explicitly assisted diagnostic uses
the old 27-pin masks. Bounded search failure is never an exclusion.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,time,sys
from verify_frozen_candidates import rows_for,f,decode,heldout
from propagate_feedback_domains import canonical
ROOT=Path(__file__).resolve().parent
FULL=(1<<83)-1

def members(bits):
    while bits:
        low=bits&-bits;yield low.bit_length()-1;bits-=low

def sums(a,b):
    if not a or not b:return 0
    if a==FULL or b==FULL:return FULL
    if a.bit_count()>b.bit_count():a,b=b,a
    out=0
    for x in members(a):
        out|=((b<<x)|(b>>(83-x)))&FULL
        if out==FULL:break
    return out

def equations(messages,eq,name):
    original=rows_for(messages,eq)
    if name=='add':original=[[(r[j]+r[83+j])%83 for j in range(83)] for r in original]
    width=83 if name=='add' else 166
    matrix=[r.copy()+[int(i==j) for j in range(len(original))] for i,r in enumerate(original)]
    pivot=0
    for col in range(width):
        found=next((i for i in range(pivot,len(matrix)) if matrix[i][col]),None)
        if found is None:continue
        matrix[pivot],matrix[found]=matrix[found],matrix[pivot]
        scale=pow(matrix[pivot][col],81,83);matrix[pivot]=[v*scale%83 for v in matrix[pivot]]
        for i,row in enumerate(matrix):
            if i==pivot or not row[col]:continue
            scale=row[col];matrix[i]=[(v-scale*w)%83 for v,w in zip(row,matrix[pivot])]
        pivot+=1
    return dict(original_rows=original,rows=[r[:width] for r in matrix[:pivot]],combinations=[r[width:] for r in matrix[:pivot]])

class Problem:
    def __init__(self,messages,eq,name):
        self.messages=messages;self.name=name;self.linear=equations(messages,eq,name)
        self.edges=sorted({(m[t-1],m[t]) for m in messages[:6] for t in range(2,len(m))})
        self.incident=[[e for e in self.edges if j in e] for j in range(83)]
        self.fn=[f(name,x) for x in range(83)];self.terms=[]
        self.degree=Counter(x for edge in self.edges for x in edge)
        for row in self.linear['rows']:
            terms=[]
            for j in range(83):
                a=row[j];b=row[j+83] if len(row)>83 else 0
                if a or b:
                    terms.append((j,[(a*x+b*self.fn[x])%83 for x in range(83)]));self.degree[j]+=10
            self.terms.append(terms)

    def initial(self,pins):
        domains=[set(range(83)) for _ in range(83)]
        for j,v in pins:domains[j]={v}
        if self.name=='add':domains[0]={0};domains[1]={1}
        return domains

    def propagate(self,domains,record=False,alphabet=True):
        trace=[];reason_counts=Counter();rounds=0
        def remove(j,values,reason,witness=None):
            for value in sorted(values):
                domains[j].remove(value);reason_counts[reason]+=1
                if record:trace.append(dict(label=j,value=value,reason=reason,witness=witness))
        def result(status,why=None):
            return dict(status=status,contradiction=why,domains=[sorted(d) for d in domains],trace=trace,
                reason_counts=dict(reason_counts),rounds=rounds,singletons=sum(len(d)==1 for d in domains))
        while True:
            rounds+=1;before=sum(map(len,domains))
            fixed={j:next(iter(d)) for j,d in enumerate(domains) if len(d)==1}
            if len(set(fixed.values()))!=len(fixed):return result('contradiction','duplicate_fixed_values')
            for j in range(83):
                if len(domains[j])>1:remove(j,domains[j]&set(fixed.values()),'permutation')
                if not domains[j]:return result('contradiction','empty_domain')
            for index,terms in enumerate(self.terms):
                possibilities=[]
                for j,h in terms:
                    mask=0
                    for x in domains[j]:mask|=1<<h[x]
                    possibilities.append(mask)
                prefix=[1]
                for mask in possibilities:prefix.append(sums(prefix[-1],mask))
                suffix=[1]*(len(terms)+1)
                for t in reversed(range(len(terms))):suffix[t]=sums(possibilities[t],suffix[t+1])
                for t,(j,h) in enumerate(terms):
                    others=sums(prefix[t],suffix[t+1])
                    if others==FULL:continue
                    bad={x for x in domains[j] if not (others>>((-h[x])%83)&1)}
                    remove(j,bad,'passage_row',index)
                    if not domains[j]:return result('contradiction','empty_domain')
            if alphabet:
                for j in range(83):
                    fixed={i:next(iter(d)) for i,d in enumerate(domains) if len(d)==1}
                    codes={(fixed[b]-self.fn[fixed[a]])%83 for a,b in self.edges if a in fixed and b in fixed}
                    if len(codes)>27:return result('contradiction','codebook_overflow')
                    if len(domains[j])==1:continue
                    bad=[]
                    for value in domains[j]:
                        local=set(codes);trial=dict(fixed);trial[j]=value
                        for a,b in self.incident[j]:
                            if a in trial and b in trial:local.add((trial[b]-self.fn[trial[a]])%83)
                        if len(local)>27:bad.append(value)
                    remove(j,bad,'alphabet_cap')
                    if not domains[j]:return result('contradiction','empty_domain')
            if sum(map(len,domains))==before:return result('fixed_point')

    def search(self,node_limit=120,seconds=20):
        started=time.monotonic();nodes=0;cuts=0;best=0;answer=None;answer_path=None;limited=False
        def visit(domains,path):
            nonlocal nodes,cuts,best,answer,answer_path,limited
            if nodes>=node_limit or time.monotonic()-started>=seconds:limited=True;return False
            nodes+=1;r=self.propagate(domains);best=max(best,r['singletons'])
            if r['status']=='contradiction':cuts+=1;return False
            if r['singletons']==83:
                key=[next(iter(d)) for d in domains]
                if len(set(key))==83:
                    answer=key;answer_path=path;return True
            j=min((j for j,d in enumerate(domains) if len(d)>1),key=lambda j:(len(domains[j]),-self.degree[j],j))
            for value in sorted(domains[j]):
                child=[d.copy() for d in domains];child[j]={value}
                if visit(child,path+[[j,value]]):return True
                if limited:return False
            return False
        visit(self.initial([]),[])
        out=dict(status='candidate' if answer is not None else 'budget_exhausted' if limited else 'tree_exhausted',
            node_limit=node_limit,seconds_budget=seconds,nodes=nodes,contradiction_nodes=cuts,max_singletons_seen=best,
            elapsed_seconds=time.monotonic()-started,branching='smallest domain, highest degree, then label; increasing values')
        if answer is not None:
            d=decode(self.messages,self.name,answer);out.update(key=answer,branch_choices=answer_path,codebook=sorted({v for row in d[:6] for v in row[2:]}))
        return out

def main():
    raw=(ROOT/'frozen_candidate_search.json').read_bytes();source=json.loads(raw)
    prior_raw=(ROOT/'joint_feedback_constraints.json').read_bytes();prior=json.loads(prior_raw)
    out=dict(executed_date='2026-09-08',source_sha256=hashlib.sha256(raw).hexdigest(),
        mask_parent_sha256=hashlib.sha256(prior_raw).hexdigest(),status='Combined passage/alphabet calibration; no Eye decipherment.',controls=[])
    def save():(ROOT/'passage_domain_search.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
    for c,old in zip(source['controls'],prior['controls']):
        p=Problem(c['ciphertext'],source['early_equalities'],c['name']);r=dict(name=c['name'],seed=c['seed'],equations=p.linear)
        out['controls'].append(r)
        r['blind_root']=p.propagate(p.initial([]),record=True);r['blind_search']=p.search()
        if 'key' in r['blind_search']:
            candidate=r['blind_search'];r['heldout']=heldout(c['ciphertext'],source['late_equalities'],c['name'],candidate['key'],candidate['codebook'])
        print(c['name'],'blind root',r['blind_root']['singletons'],'search',r['blind_search']['status'],'nodes',r['blind_search']['nodes'],flush=True);save()
        truth=canonical(c['name'],c['true_key']);missing=set(old['hide_order'][:56]);pins=[[j,v] for j,v in enumerate(truth) if j not in missing]
        r['assisted_27_pins']=dict(pins=pins)
        for mode,alphabet in [('passages_only',False),('passages_and_alphabet',True)]:
            result=p.propagate(p.initial(pins),record=True,alphabet=alphabet)
            assert all(truth[j] in d for j,d in enumerate(result['domains']))
            r['assisted_27_pins'][mode]=result
            if result['singletons']==83:
                key=[d[0] for d in result['domains']];d=decode(c['ciphertext'],c['name'],key);codes=sorted({v for row in d[:6] for v in row[2:]})
                result['heldout']=heldout(c['ciphertext'],source['late_equalities'],c['name'],key,codes)
            print(c['name'],mode,'fixed entries',result['singletons'],flush=True)
        save()

def extend():
    raw=(ROOT/'frozen_candidate_search.json').read_bytes();source=json.loads(raw)
    prior=(ROOT/'passage_domain_search.json').read_bytes()
    out=dict(executed_date='2026-09-08',source_sha256=hashlib.sha256(raw).hexdigest(),
        parent_sha256=hashlib.sha256(prior).hexdigest(),controls=[])
    for c in source['controls']:
        p=Problem(c['ciphertext'],source['early_equalities'],c['name'])
        result=p.search(node_limit=20000,seconds=30)
        row=dict(name=c['name'],seed=c['seed'],result=result)
        if 'key' in result:row['heldout']=heldout(c['ciphertext'],source['late_equalities'],c['name'],result['key'],result['codebook'])
        out['controls'].append(row)
        (ROOT/'passage_domain_extended.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
        print(c['name'],'extended',result['status'],'nodes',result['nodes'],'seconds',round(result['elapsed_seconds'],2),flush=True)

if __name__=='__main__':
    if '--extend' in sys.argv:extend()
    else:main()
