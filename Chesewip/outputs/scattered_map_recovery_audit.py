"""Recovery calibration and explicitly non-exclusionary Eye searches."""
from pathlib import Path
import json,random,hashlib,time,argparse
from scattered_map_search import search
ROOT=Path(__file__).resolve().parent
LENGTHS=[99,103,118,102,137,124,119,120,114]

def make_control(seed):
    rng=random.Random(seed);alphabet=rng.sample(range(125),27)
    assert all({(v//w)%5 for v in alphabet}==set(range(5)) for w in [25,5,1])
    permutation=list(range(125));rng.shuffle(permutation);plaintext=[];ciphertext=[]
    for n in LENGTHS:
        plain=alphabet+[rng.choice(alphabet) for _ in range(n-27)];rng.shuffle(plain)
        enc=[]
        for lo in range(0,n,7):
            block=plain[lo:lo+7];stream=[(v//w)%5 for w in [25,5,1] for v in block]
            enc.extend(permutation[25*stream[j]+5*stream[j+1]+stream[j+2]] for j in range(0,len(stream),3))
        plaintext.append(plain);ciphertext.append(enc)
    inverse=[0]*125
    for code,label in enumerate(permutation):inverse[label]=code
    return dict(seed=seed,alphabet=alphabet,plaintext=plaintext,ciphertext=ciphertext,
                true_output_label_to_code=inverse,observed_labels=len(set(sum(ciphertext,[]))),runs=[])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=['controls','eyes'],default='controls');args=ap.parse_args()
    started=time.monotonic();out=dict(status='Recovery calibration; failed searches are not exclusions.',
        phase=args.phase,objective='occupied cells minus 0.1 * sum(count * log(count))',controls=[],runs=[])
    path=ROOT/('scattered_map_recovery_'+args.phase+'.json')
    def save():path.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    if args.phase=='controls':
        for ci,seed in enumerate([907413,907440,907441]):
            c=make_control(seed);out['controls'].append(c)
            for swaps in [0,5,10,20,40]:
                r=search(c['ciphertext'],7,7,False,False,907450+100*ci+swaps,100000,
                         c['true_output_label_to_code'],swaps,temperature_start=.05)
                r['initial_wrong_key_entries']=sum(a!=b for a,b in zip(r['initial_key'],c['true_output_label_to_code']))
                r['final_wrong_key_entries']=sum(a!=b for a,b in zip(r['best_key'],c['true_output_label_to_code']))
                c['runs'].append(r);save()
                print('Control',seed,'warm swaps',swaps,'support',r['best_support'],'wrong entries',r['final_wrong_key_entries'],flush=True)
            for ti,temp in enumerate([.2,.8,3.0]):
                r=search(c['ciphertext'],7,7,False,False,907500+100*ci+ti,200000,temperature_start=temp)
                c['runs'].append(r);save()
                print('Control',seed,'blind temp',temp,'support',r['best_support'],flush=True)
    else:
        raw_bytes=(ROOT/'ciphertext.json').read_bytes();messages=list(json.loads(raw_bytes).values())
        out['ciphertext_sha256']=hashlib.sha256(raw_bytes).hexdigest()
        out['scope']='Fixed periods 2,3,5,7,11,13; shared full first block; first symbol omitted, forward reading. Two blind restarts per period.'
        for period in [2,3,5,7,11,13]:
            for restart,temp in enumerate([.8,3.0]):
                r=search(messages,period,period,True,False,908000+10*period+restart,200000,temperature_start=temp)
                out['runs'].append(r);save()
                print('Eyes period',period,'restart',restart,'support',r['best_support'],flush=True)
    out['seconds']=time.monotonic()-started;save()

if __name__=='__main__':main()
