"""Second-order conditional null diagnostic; watch for a nearly frozen null."""
from pathlib import Path
from collections import Counter
import json,random,time
from transition_pattern_audit import EulerSampler,prefix_lengths
from pattern_assumption_audit import max_recurrence
ROOT=Path(__file__).resolve().parent
messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values());protected=prefix_lengths(messages)
start=time.time();results=[];observed=max_recurrence(messages)
for mode in ['whole_message','fixed_shared_prefix']:
    rng=random.Random(20261020);cuts=[0]*len(messages) if mode=='whole_message' else [max(0,n-2) for n in protected]
    samplers=[EulerSampler(list(zip(m[cut:],m[cut+1:]))) for m,cut in zip(messages,cuts)]
    hist=Counter();changed=[];unique=set();per_message=[set() for _ in messages]
    for _ in range(1000):
        corpus=[]
        for i,(m,cut,sampler) in enumerate(zip(messages,cuts,samplers)):
            pairs=sampler.draw(rng);suffix=[pairs[0][0]]+[p[1] for p in pairs];sample=m[:cut]+suffix
            assert Counter(zip(m,m[1:],m[2:]))==Counter(zip(sample,sample[1:],sample[2:]))
            assert Counter(zip(m,m[1:]))==Counter(zip(sample,sample[1:]))
            assert m[:cut+2]==sample[:cut+2] and m[-2:]==sample[-2:]
            corpus.append(sample);per_message[i].add(tuple(sample))
        hist[max_recurrence(corpus)]+=1
        changed.append(sum(x!=y for m,v in zip(messages,corpus) for x,y in zip(m,v)))
        unique.add(tuple(tuple(m) for m in corpus))
    result={'mode':mode,'observed':observed,'trials':1000,'histogram':dict(sorted(hist.items())),
            'at_least_observed':sum(v for k,v in hist.items() if k>=observed),
            'mean_changed_positions':sum(changed)/len(changed),'maximum_changed_positions':max(changed),
            'distinct_corpora':len(unique),'distinct_sequences_per_message':[len(x) for x in per_message]}
    results.append(result);print(result,flush=True)
out={'results':results,'seconds':time.time()-start,'caveat':'Preserving triples can leave too few alternative sequences for an informative test. This diagnostic is not evidence for a second-order cipher.'}
(ROOT/'context2_pattern_audit.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
