from pathlib import Path
from collections import Counter,defaultdict
import json,itertools
from transition_pattern_audit import prefix_lengths
from pattern_assumption_audit import max_recurrence
ROOT=Path(__file__).resolve().parent

def enumerate_context_trails(sequence):
    pairs=list(zip(sequence,sequence[1:]));remaining=Counter(zip(pairs,pairs[1:]));out=defaultdict(set)
    for u,v in remaining:out[u].add(v)
    results=[];trail=[pairs[0]]
    def visit(v,left):
        if not left:
            if v==pairs[-1]:results.append([trail[0][0]]+[p[1] for p in trail])
            return
        for w in sorted(out[v]):
            if remaining[v,w]:
                remaining[v,w]-=1;trail.append(w);visit(w,left-1);trail.pop();remaining[v,w]+=1
    visit(pairs[0],len(pairs)-1)
    return results

messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values());protected=prefix_lengths(messages);cases=[]
for mode in ['whole_message','fixed_shared_prefix']:
    cuts=[0]*len(messages) if mode=='whole_message' else [max(0,n-2) for n in protected]
    options=[]
    for m,c in zip(messages,cuts):
        variants=[m[:c]+s for s in enumerate_context_trails(m[c:])]
        assert tuple(m) in {tuple(v) for v in variants}
        assert len(variants)==len(set(tuple(v) for v in variants))
        for v in variants:assert Counter(zip(m,m[1:],m[2:]))==Counter(zip(v,v[1:],v[2:]))
        options.append(variants)
    hist=Counter(max_recurrence(corpus) for corpus in itertools.product(*options))
    cases.append({'mode':mode,'exact_distinct_sequences_per_message':[len(v) for v in options],
                  'exact_corpus_count':sum(hist.values()),'exact_statistic_histogram':dict(hist)})
    print(cases[-1])
(ROOT/'checked_context2_enumeration.json').write_text(json.dumps({'cases':cases},indent=2)+'\n',encoding='utf-8',newline='\r\n')
