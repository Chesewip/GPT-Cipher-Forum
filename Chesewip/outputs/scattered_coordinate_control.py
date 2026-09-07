"""Counterexample to interpreting coordinate coverage as plaintext support."""
from pathlib import Path
import random,json
from unknown_map_prism import routes
from coordinate_coverage_certificates import certify,candidate_witnesses
ROOT=Path(__file__).resolve().parent

def main():
    rng=random.Random(907413);alphabet=rng.sample(range(125),27)
    permutation=list(range(125));rng.shuffle(permutation)
    plaintext=[];ciphertext=[]
    for n in [99,103,118,102,137,124,119,120,114]:
        plain=alphabet+[rng.choice(alphabet) for _ in range(n-27)];rng.shuffle(plain)
        enc=[]
        for lo in range(0,n,7):
            block=plain[lo:lo+7]
            stream=[(x//power)%5 for power in [25,5,1] for x in block]
            enc.extend(permutation[25*stream[j]+5*stream[j+1]+stream[j+2]] for j in range(0,len(stream),3))
        plaintext.append(plain);ciphertext.append(enc)
    certificates=certify(routes(ciphertext,7),candidate_witnesses())
    assert all(x is not None for x in certificates)
    out=dict(status='Generated scope counterexample, not a fit to the eyes.',seed=907413,
             period=7,strip_first=False,reverse=False,input_alphabet=alphabet,
             input_support=27,observed_output_labels=len(set(sum(ciphertext,[]))),
             coordinate_code_to_output_label=permutation,plaintext=plaintext,ciphertext=ciphertext,
             axis_coverage_certificates=certificates,
             conclusion='All five values are required in every input coordinate, yet the actual input alphabet has only 27 triples. Its bounding prism has 125 cells.')
    (ROOT/'scattered_coordinate_control.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(out['conclusion'])

if __name__=='__main__':main()
