"""Independent replay of coordinate-dependency proofs; standard library only.

Reconstructs input rows by scattering output coordinates, then checks each
recorded implication. No discovery code, table enumeration or key search.
"""
from pathlib import Path
from collections import Counter
import itertools,json,hashlib,base64,zlib,struct
ROOT=Path(__file__).resolve().parent
TRIPLES=list(itertools.product(range(5),repeat=3))

class Equality:
    def __init__(self):self.parents=list(range(375));self.ranks=[0]*375
    def find(self,x):
        while x!=self.parents[x]:x=self.parents[x]
        return x
    def join(self,x,y):
        x=self.find(x);y=self.find(y)
        if x==y:return
        if self.ranks[x]<self.ranks[y]:x,y=y,x
        self.parents[y]=x
        if self.ranks[x]==self.ranks[y]:self.ranks[x]+=1

def routing(messages,p,first,strip,reverse):
    out=[]
    for raw in messages:
        seq=raw[int(strip):]
        if reverse:seq=seq[::-1]
        end=min(first,len(seq));start=0
        while start<len(seq):
            block=seq[start:end];n=len(block);rows=[[None]*3 for _ in block]
            for j,label in enumerate(block):
                for digit in range(3):
                    axis,pos=divmod(3*j+digit,n);rows[pos][axis]=3*label+digit
            out.extend(rows);start=end;end=min(len(seq),end+p)
    return out

def unpack(result):
    if 'proof' in result:return result['proof']
    raw=zlib.decompress(base64.b64decode(result['proof_base64_zlib'],validate=True))
    assert len(raw)==result['proof_steps']*5
    return list(struct.iter_unpack('<HHB',raw))

def replay(rows,labels,result,axes,assumption=None,true_values=None):
    eq=Equality()
    if assumption is not None:
        assert len(assumption)==2 and all(0<=v<375 for v in assumption)
        eq.join(*assumption)
    steps=unpack(result)
    for i,j,axis in steps:
        assert axis in axes and 0<=i<len(rows) and 0<=j<len(rows)
        other=[d for d in range(3) if d!=axis]
        assert all(eq.find(rows[i][d])==eq.find(rows[j][d]) for d in other)
        if true_values is not None:assert true_values[rows[i][axis]]==true_values[rows[j][axis]]
        eq.join(rows[i][axis],rows[j][axis])
    if result['status']=='forced_output_collision':
        a,b=result['pair'];assert a!=b and a in labels and b in labels
        assert all(eq.find(3*a+d)==eq.find(3*b+d) for d in range(3))
    else:
        assert result['status']=='closure_survives'
        signatures=[tuple(eq.find(3*label+d) for d in range(3)) for label in labels]
        assert len(set(signatures))==len(labels)
        # Check fixed point, without treating different roots as different values.
        for axis in axes:
            lookup={};others=[d for d in range(3) if d!=axis]
            for row in rows:
                key=tuple(eq.find(row[d]) for d in others);value=eq.find(row[axis])
                if key in lookup:assert lookup[key]==value
                else:lookup[key]=value
    return len(steps)

def check_result(rows,labels,result,axes):
    if result['status']!='six_pairwise_distinct_coordinate_values':return replay(rows,labels,result,axes),0
    variables=result['variables'];assert len(variables)==len(set(variables))==6
    assert all(v//3 in labels and 0<=v<375 for v in variables)
    expected={tuple(sorted(pair)) for pair in itertools.combinations(variables,2)}
    assert len(result['branches'])==15
    assert {tuple(sorted(b['assumption'])) for b in result['branches']}==expected
    steps=0
    for branch in result['branches']:
        assert branch['status']=='forced_output_collision'
        steps+=replay(rows,labels,branch,axes,assumption=branch['assumption'])
    return steps,15

def verify_control(c,axes):
    p=c['period'];first=c.get('first_block',p);strip=c.get('strip_first',False);reverse=c.get('reverse',False)
    key=c['true_label_to_code'];assert sorted(key)==list(range(125))
    values=[digit for code in key for digit in TRIPLES[code]]
    rows=routing(c['ciphertext'],p,first,strip,reverse)
    actual=[25*values[row[0]]+5*values[row[1]]+values[row[2]] for row in rows]
    assert actual==sum(c['plaintext'],[]) and len(set(actual))==25
    determined=2 if len(axes)==3 else axes[0]
    arguments=[d for d in range(3) if d!=determined]
    assert all(TRIPLES[v][determined]==c['table'][TRIPLES[v][arguments[0]]][TRIPLES[v][arguments[1]]] for v in actual)
    # Independently verify each functional dependency on actual generated points.
    for axis in axes:
        lookup={};others=[d for d in range(3) if d!=axis]
        for code in actual:
            t=TRIPLES[code];k=(t[others[0]],t[others[1]])
            if k in lookup:assert lookup[k]==t[axis]
            else:lookup[k]=t[axis]
    labels=sorted(set(v//3 for row in rows for v in row))
    assert c['closure_result']['status']=='closure_survives'
    replay(rows,labels,c['closure_result'],axes,true_values=values)
    return len(actual)

def main():
    data=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(data).values());sha=hashlib.sha256(data).hexdigest()
    boundary_bytes=(ROOT/'latin_dependency_boundaries.json').read_bytes();boundary=json.loads(boundary_bytes)
    refinement=json.loads((ROOT/'latin_boundary_refinement.json').read_text(encoding='utf-8'))
    assert boundary['ciphertext_sha256']==refinement['ciphertext_sha256']==sha
    assert refinement['parent_sha256']==hashlib.sha256(boundary_bytes).hexdigest()
    expected=[(s,r,p,f) for s in [False,True] for r in [False,True]
              for p in range(2,max(map(len,messages))-int(s)+1) for f in range(1,p+1)]
    signature=lambda c:(c['strip_first'],c['reverse'],c['period'],c['first_block'])
    assert [signature(c) for c in boundary['cases']]==expected
    replacements={signature(c):c for c in refinement['cases']}
    assert set(replacements)=={signature(c) for c in boundary['cases'] if c['status']=='closure_survives'}
    steps=0;branches=0;kinds=Counter()
    for i,c in enumerate(boundary['cases']):
        rows=routing(messages,c['period'],c['first_block'],c['strip_first'],c['reverse'])
        labels=sorted(set(v//3 for row in rows for v in row))
        if c['status']=='closure_survives':
            replay(rows,labels,c,(0,1,2));c=replacements[signature(c)]
        assert c['status'] in ['forced_output_collision','six_pairwise_distinct_coordinate_values']
        n,b=check_result(rows,labels,c,(0,1,2));steps+=n;branches+=b;kinds[c['status']]+=1
        if (i+1)%4096==0:print('Boundary cases verified',i+1,flush=True)
    control_symbols=0
    for c in boundary['controls']:
        table=c['table'];assert all(sorted(row)==list(range(5)) for row in table)
        assert all(sorted(table[x][y] for x in range(5))==list(range(5)) for y in range(5))
        assert any(table[table[x][y]][z]!=table[x][table[y][z]] for x,y,z in itertools.product(range(5),repeat=3))
        assert not any(all((a*x+b*y+table[x][y])%5==d for x,y in itertools.product(range(5),repeat=2)) for a,b,d in itertools.product(range(1,5),range(1,5),range(5)))
        control_symbols+=verify_control(c,(0,1,2))
    weaker=json.loads((ROOT/'one_coordinate_function_screen.json').read_text(encoding='utf-8'));assert weaker['ciphertext_sha256']==sha
    expected_weak=[(axis,s,r,p) for axis in range(3) for s in [False,True] for r in [False,True]
                   for p in range(2,max(map(len,messages))-int(s)+1)]
    assert [(c['axis'],c['strip_first'],c['reverse'],c['period']) for c in weaker['cases']]==expected_weak
    weak=Counter()
    for c in weaker['cases']:
        rows=routing(messages,c['period'],c['period'],c['strip_first'],c['reverse'])
        labels=sorted(set(v//3 for row in rows for v in row))
        check_result(rows,labels,c,(c['axis'],));weak[c['status']]+=1
    for c in weaker['controls']:control_symbols+=verify_control(c,(c['axis'],))
    # Replay the original closure-only full-first-block pilot as historical data.
    pilot=json.loads((ROOT/'nonlinear_coordinate_closure.json').read_text(encoding='utf-8'));assert pilot['ciphertext_sha256']==sha
    for c in pilot['cases']:
        rows=routing(messages,c['period'],c['period'],c['strip_first'],c['reverse'])
        replay(rows,sorted(set(v//3 for row in rows for v in row)),c,(0,1,2))
    out=dict(status='Verified nonlinear dependency exclusions; no plaintext recovered.',
        latin_boundary_configurations=len(expected),final_certificate_kinds=dict(kinds),
        conditional_equality_branches_verified=branches,latin_equality_implications_verified=steps,
        weaker_function_configurations=len(expected_weak),weaker_results=dict(weak),
        generated_controls_verified=6,generated_plaintext_symbols_replayed=control_symbols,
        historical_closure_pilot_cases_verified=len(pilot['cases']),
        scope='Every final exclusion certificate replayed independently. Weaker closure survivors are not model fits. Refinement graph edges outside the final 15-branch clique certificates are discovery metadata.')
    (ROOT/'checked_nonlinear_dependencies.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
