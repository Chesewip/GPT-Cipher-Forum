"""Exact affine-plane input-codebook obstruction with unknown output mapping.

Every input triple satisfies a*x+b*y+z=d in F5, with a,b nonzero.
Finds row-equation combinations forcing two distinct output labels to the same
coordinate triple. A failed certificate search is not an exclusion.
"""
from pathlib import Path
import itertools,json,hashlib,time,random,argparse,base64,zlib
import numpy as np
ROOT=Path(__file__).resolve().parent

def equations(messages,period,first,strip,reverse,a,b):
    rows=[];locations=[]
    for message,raw in enumerate(messages):
        seq=raw[int(strip):]
        if reverse:seq=seq[::-1]
        lo=0;length=first
        while lo<len(seq):
            block=seq[lo:lo+length];n=len(block)
            for pos in range(n):
                row={375:-1}
                for axis,coef in enumerate((a,b,1)):
                    j,digit=divmod(axis*n+pos,3);var=3*block[j]+digit
                    row[var]=row.get(var,0)+coef
                rows.append(row);locations.append([message,lo,pos,n])
            lo+=n;length=period
    used=sorted({k for r in rows for k,v in r.items() if v%5})
    index={v:j for j,v in enumerate(used)}
    matrix=np.zeros((len(rows),len(used)),dtype=np.int16)
    for i,row in enumerate(rows):
        for var,value in row.items():
            if var in index:matrix[i,index[var]]=value%5
    return matrix,used,locations

def rowspace_certificates(matrix,variables,pair=(0,1),line_b=None):
    target_terms=[]
    if line_b is None:
        for d in range(3):target_terms.append({3*pair[0]+d:1,3*pair[1]+d:4})
    else:
        for label in range(1,6):
            target_terms.extend([{3*label+1:1,1:4},{3*label:line_b,3*label+2:1,0:-line_b,2:4}])
    index={v:i for i,v in enumerate(variables)}
    if any(v not in index for target in target_terms for v in target):return None
    targets=np.zeros((len(variables),len(target_terms)),dtype=np.int16)
    for j,target in enumerate(target_terms):
        for v,coef in target.items():targets[index[v],j]=coef%5
    # Solve M.T * weights = coordinate differences, all three RHS together.
    aug=np.concatenate([matrix.T.copy(),targets],axis=1);n=matrix.shape[0];rank=0;pivots=[]
    inverse=[0,1,3,2,4]
    for col in range(n):
        candidates=np.flatnonzero(aug[rank:,col])
        if not len(candidates):continue
        chosen=rank+int(candidates[0]);aug[[rank,chosen]]=aug[[chosen,rank]]
        aug[rank]=(aug[rank]*inverse[int(aug[rank,col])])%5
        active=np.flatnonzero(aug[:,col]);active=active[active!=rank]
        aug[active]=(aug[active]-aug[active,col,None]*aug[rank])%5
        pivots.append(col);rank+=1
        if rank==len(variables):break
    if np.any(aug[rank:,n:]):return None
    weights=np.zeros((len(target_terms),n),dtype=np.int16)
    for row,col in enumerate(pivots):weights[:,col]=aug[row,n:]
    assert np.array_equal((weights@matrix)%5,targets.T)
    return dict(kind='coordinate_collision' if line_b is None else 'six_labels_on_five_point_line',
                pair=list(pair) if line_b is None else None,line_b=line_b,
                equation_rank=rank,unknown_coordinates_and_rhs=len(variables),
                targets=target_terms,weight_rows=len(target_terms),
                weights_encoding='base64(zlib(row-major uint8 residues modulo 5))',
                weights_base64_zlib=base64.b64encode(zlib.compress(weights.astype(np.uint8).tobytes(),9)).decode('ascii'))

def plane_control(seed,period,a,b):
    rng=random.Random(seed);rhs=rng.randrange(5)
    alphabet=[25*x+5*y+((rhs-a*x-b*y)%5) for x,y in itertools.product(range(5),repeat=2)]
    permutation=list(range(125));rng.shuffle(permutation);plainrows=[];cipherrows=[]
    for n in [99,103,118,102,137,124,119,120,114]:
        plain=alphabet+[rng.choice(alphabet) for _ in range(n-25)];rng.shuffle(plain);cipher=[]
        for lo in range(0,n,period):
            block=plain[lo:lo+period];flat=[(v//w)%5 for w in (25,5,1) for v in block]
            cipher.extend(permutation[25*flat[j]+5*flat[j+1]+flat[j+2]] for j in range(0,len(flat),3))
        plainrows.append(plain);cipherrows.append(cipher)
    inverse=[0]*125
    for code,label in enumerate(permutation):inverse[label]=code
    return dict(seed=seed,period=period,a=a,b=b,rhs=rhs,plaintext=plainrows,ciphertext=cipherrows,
                true_label_to_code=inverse)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--max-period',type=int,default=137);args=ap.parse_args()
    started=time.monotonic();raw_bytes=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(raw_bytes).values())
    out=dict(status='Finite affine-plane input-codebook test; no plaintext recovered.',
        ciphertext_sha256=hashlib.sha256(raw_bytes).hexdigest(),
        scope='All nonzero a,b for a*x+b*y+z=d mod 5; d unknown. Shared period 2..maximum retained length, full first blocks, forward/reversed body, first symbol retained or omitted. Arbitrary shared injective output mapping.',
        max_period=args.max_period,cases=[],controls=[])
    path=ROOT/'affine_plane_codebook.json'
    def save():path.write_text(json.dumps(out,separators=(',',':'))+'\n',encoding='utf-8',newline='\r\n')
    for strip in [False,True]:
        for reverse in [False,True]:
            for period in range(2,min(args.max_period,max(map(len,messages))-int(strip))+1):
                for a,b in itertools.product(range(1,5),repeat=2):
                    matrix,variables,_=equations(messages,period,period,strip,reverse,a,b)
                    take=min(512,len(matrix));cert=rowspace_certificates(matrix[:take],variables)
                    if cert is None:take=len(matrix);cert=rowspace_certificates(matrix,variables)
                    if cert is None and period==2 and a==b*b%5:
                        cert=rowspace_certificates(matrix,variables,line_b=b)
                    out['cases'].append(dict(strip_first=strip,reverse=reverse,period=period,a=a,b=b,equations_used=take,
                        status='injective_mapping_impossible' if cert else 'no_certificate',certificate=cert))
                if period%8==0:
                    save();print('View',strip,reverse,'period',period,'certificates',sum(c['certificate'] is not None for c in out['cases']),'/',len(out['cases']),flush=True)
            save()
    for spec in [(908100,2,1,1),(908101,7,1,2),(908102,13,3,4)]:
        c=plane_control(*spec);matrix,variables,_=equations(c['ciphertext'],c['period'],c['period'],False,False,c['a'],c['b'])
        solution=[c['rhs'] if v==375 else (c['true_label_to_code'][v//3]//(25,5,1)[v%3])%5 for v in variables]
        assert not np.any((matrix@np.array(solution,dtype=np.int16))%5)
        assert rowspace_certificates(matrix,variables) is None
        c['known_key_satisfies_all_equations']=True;c['false_collision_certificate_rejected']=True
        out['controls'].append(c);save()
    out['seconds']=time.monotonic()-started;save()

if __name__=='__main__':main()
