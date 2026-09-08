"""Nonlinear Latin-codebook screen with variable boundary blocks.

Proofs use equality implications and five-value pigeonhole certificates.
No guessed key, equation, language, or plaintext-equality assumption is used.
"""
from pathlib import Path
import itertools,json,hashlib,time,random,struct,base64,zlib,argparse
from nonlinear_coordinate_closure import routed_triples,closure
ROOT=Path(__file__).resolve().parent

def pack_proof(result):
    result=dict(result);proof=result.pop('proof')
    raw=b''.join(struct.pack('<HHB',*row) for row in proof)
    result['proof_steps']=len(proof)
    result['proof_base64_zlib']=base64.b64encode(zlib.compress(raw,9)).decode('ascii')
    return result

def certificate(triples,labels,axes=(0,1,2)):
    base,_=closure(triples,labels,axes)
    if base['status']=='forced_output_collision':return pack_proof(base)
    for axis in range(3):
        variables=[3*label+axis for label in labels[:6]];branches=[]
        for a,b in itertools.combinations(variables,2):
            branch,_=closure(triples,labels,axes,assumptions=[(a,b)])
            if branch['status']!='forced_output_collision':break
            branch['assumption']=[a,b];branches.append(pack_proof(branch))
        if len(branches)==15:
            return dict(status='six_pairwise_distinct_coordinate_values',variables=variables,branches=branches)
    return pack_proof(base)

def nonlinear_table(seed):
    rng=random.Random(seed)
    while True:
        table=[[-1]*5 for _ in range(5)]
        for i in range(5):table[0][i]=i;table[i][0]=i
        def fill(pos=0):
            if pos==16:return True
            x,y=1+pos//4,1+pos%4
            choices=list(set(range(5))-set(table[x])-{table[i][y] for i in range(5)});rng.shuffle(choices)
            for v in choices:
                table[x][y]=v
                if fill(pos+1):return True
            table[x][y]=-1;return False
        assert fill()
        if any(table[table[x][y]][z]!=table[x][table[y][z]] for x,y,z in itertools.product(range(5),repeat=3)):
            return table

def control(seed,period,first,strip,reverse):
    rng=random.Random(seed);table=nonlinear_table(seed)
    alphabet=[25*x+5*y+table[x][y] for x,y in itertools.product(range(5),repeat=2)]
    permutation=list(range(125));rng.shuffle(permutation);plains=[];ciphers=[]
    for n in [99,103,118,102,137,124,119,120,114]:
        plain=alphabet+[rng.choice(alphabet) for _ in range(n-25)];rng.shuffle(plain)
        lo=0;length=first;cipher=[]
        while lo<n:
            block=plain[lo:lo+length];flat=[(v//w)%5 for w in [25,5,1] for v in block]
            cipher.extend(permutation[25*flat[j]+5*flat[j+1]+flat[j+2]] for j in range(0,len(flat),3))
            lo+=len(block);length=period
        if reverse:cipher=cipher[::-1]
        if strip:cipher=[rng.randrange(125)]+cipher
        plains.append(plain);ciphers.append(cipher)
    inverse=[0]*125
    for code,label in enumerate(permutation):inverse[label]=code
    return dict(seed=seed,table=table,period=period,first_block=first,strip_first=strip,reverse=reverse,
                plaintext=plains,ciphertext=ciphers,true_label_to_code=inverse)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--full-first-only',action='store_true');args=ap.parse_args()
    started=time.monotonic();raw_bytes=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(raw_bytes).values())
    out=dict(status='Nonlinear coordinate-dependency certificates; cipher unsolved.',
        ciphertext_sha256=hashlib.sha256(raw_bytes).hexdigest(),full_first_only=args.full_first_only,
        proof_encoding='base64(zlib(concatenated little-endian uint16 row1, uint16 row2, uint8 determined_axis))',
        model='Any two input coordinates uniquely determine the third; shared arbitrary injective output mapping; common period and first-block length; short final blocks.',
        cases=[],controls=[])
    path=ROOT/('latin_dependency_full_first.json' if args.full_first_only else 'latin_dependency_boundaries.json')
    def save():path.write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
    for strip in [False,True]:
        for reverse in [False,True]:
            labels=sorted(set(x for m in messages for x in m[int(strip):]))
            for period in range(2,max(map(len,messages))-int(strip)+1):
                firsts=[period] if args.full_first_only else range(1,period+1)
                for first in firsts:
                    triples=routed_triples(messages,period,first,strip,reverse)
                    result=certificate(triples,labels)
                    result.update(strip_first=strip,reverse=reverse,period=period,first_block=first)
                    out['cases'].append(result)
                if period%16==0:
                    print('View',strip,reverse,'period',period,'excluded',sum(c['status']!='closure_survives' for c in out['cases']),'/',len(out['cases']),flush=True)
            save()
    for spec in [(908200,2,2,False,False),(908201,7,3,True,False),(908202,13,5,True,True)]:
        c=control(*spec);triples=routed_triples(c['ciphertext'],c['period'],c['first_block'],c['strip_first'],c['reverse'])
        labels=sorted(set(v//3 for row in triples for v in row));result=certificate(triples,labels)
        assert result['status']=='closure_survives'
        c['closure_result']=result;out['controls'].append(c)
    out['seconds']=time.monotonic()-started;save()

if __name__=='__main__':main()
