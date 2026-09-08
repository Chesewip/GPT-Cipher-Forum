"""Bounded weaker screen: one coordinate is any function of the other two."""
from pathlib import Path
import json,hashlib,itertools,random,time
from nonlinear_coordinate_closure import routed_triples
from latin_dependency_screen import certificate
ROOT=Path(__file__).resolve().parent

def function_control(seed,axis,period):
    rng=random.Random(seed);table=[[rng.randrange(5) for _ in range(5)] for _ in range(5)]
    assert set(sum(table,[]))==set(range(5))
    assert not all(len(set(row))==5 for row in table)
    others=[j for j in range(3) if j!=axis];alphabet=[]
    for x,y in itertools.product(range(5),repeat=2):
        triple=[None]*3;triple[others[0]]=x;triple[others[1]]=y;triple[axis]=table[x][y]
        alphabet.append(25*triple[0]+5*triple[1]+triple[2])
    permutation=list(range(125));rng.shuffle(permutation);plains=[];ciphers=[]
    for n in [99,103,118,102,137,124,119,120,114]:
        plain=alphabet+[rng.choice(alphabet) for _ in range(n-25)];rng.shuffle(plain);cipher=[]
        for lo in range(0,n,period):
            block=plain[lo:lo+period];flat=[(v//w)%5 for w in [25,5,1] for v in block]
            cipher.extend(permutation[25*flat[j]+5*flat[j+1]+flat[j+2]] for j in range(0,len(flat),3))
        plains.append(plain);ciphers.append(cipher)
    inverse=[0]*125
    for code,label in enumerate(permutation):inverse[label]=code
    return dict(seed=seed,axis=axis,period=period,table=table,plaintext=plains,ciphertext=ciphers,true_label_to_code=inverse)

def main():
    started=time.monotonic();data=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(data).values())
    out=dict(status='Weaker functional-dependency screen; closure survivors are unresolved.',
        ciphertext_sha256=hashlib.sha256(data).hexdigest(),cases=[],controls=[])
    for axis in range(3):
        for strip in [False,True]:
            for reverse in [False,True]:
                labels=sorted(set(x for m in messages for x in m[int(strip):]))
                for period in range(2,max(map(len,messages))-int(strip)+1):
                    triples=routed_triples(messages,period,period,strip,reverse)
                    r=certificate(triples,labels,axes=(axis,))
                    r.update(axis=axis,strip_first=strip,reverse=reverse,period=period,first_block=period)
                    out['cases'].append(r)
        print('Axis',axis,'excluded',sum(c['status']!='closure_survives' for c in out['cases']),'/',len(out['cases']),flush=True)
    for args in [(908210,0,2),(908211,1,7),(908212,2,13)]:
        c=function_control(*args);triples=routed_triples(c['ciphertext'],c['period'],c['period'])
        labels=sorted(set(v//3 for row in triples for v in row));r=certificate(triples,labels,axes=(c['axis'],))
        assert r['status']=='closure_survives';c['closure_result']=r;out['controls'].append(c)
    out['seconds']=time.monotonic()-started
    (ROOT/'one_coordinate_function_screen.json').write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')

if __name__=='__main__':main()
