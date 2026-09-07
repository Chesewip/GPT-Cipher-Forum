"""Audit pattern evidence separately from the plaintext-equality hypothesis.

Fixed-pattern probabilities are descriptive, not discovery-adjusted p-values.
The simulation preserves a shared-prefix tree and forbids adjacent repeats;
it is a null model, not a model of every plausible cipher.
"""
from pathlib import Path
from collections import Counter,defaultdict
import json,math,random,time
from progressive_reduction import RUNS
from synchronized_isomorph import test
ROOT=Path(__file__).resolve().parent

def signature(seq):
    labels={};return tuple(labels.setdefault(c,len(labels)) for c in seq)

def pattern_summary(messages,run):
    i,s,j,t,n=run;pat=signature(messages[i][s:s+n]);k=len(set(pat))
    locations=[];distinct=set()
    for mi,m in enumerate(messages):
        for p in range(len(m)-n+1):
            seq=tuple(m[p:p+n])
            if signature(seq)==pat:locations.append([mi,p]);distinct.add(seq)
    logprob=sum(math.log10(83-v) for v in range(k))-math.log10(83)-(n-1)*math.log10(82)
    return {'run':run,'length':n,'distinct_symbols':k,'repeat_constraints':n-k,
            'fixed_pattern_negative_log10_probability_no_doubles':-logprob,
            'occurrences':locations,'distinct_literal_strings':len(distinct)}

def max_recurrence(messages,n=9,minimum_repeats=3):
    buckets=defaultdict(set)
    for m in messages:
        for p in range(len(m)-n+1):
            seq=tuple(m[p:p+n]);pat=signature(seq)
            if n-len(set(pat))>=minimum_repeats:buckets[pat].add(seq)
    return max(map(len,buckets.values()),default=0)

def prefix_classes(messages):
    out=[]
    for t in range(max(map(len,messages))):
        groups=defaultdict(list)
        for i,m in enumerate(messages):
            if t>=len(m):continue
            if t==0:groups[('first',i)].append(i)
            else:groups[tuple(m[1:t+1])].append(i)
        out.append(list(groups.values()))
    return out

def null_corpus(classes,lengths,rng):
    msgs=[[] for _ in lengths]
    for t,groups in enumerate(classes):
        used_first=set()
        for group in groups:
            forbidden={msgs[i][-1] for i in group} if t else used_first
            c=rng.choice([c for c in range(83) if c not in forbidden])
            if not t:used_first.add(c)
            for i in group:msgs[i].append(c)
    return msgs

def main():
    start=time.time();messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    summaries=[pattern_summary(messages,r) for r in RUNS]
    subsets={'three_longest':[0,1,9], 'all_length_at_least_14':[i for i,r in enumerate(RUNS) if r[-1]>=14],
             'all_except_three_message_length_12_matches':[i for i in range(len(RUNS)) if i not in [7,8]],
             'all':list(range(len(RUNS)))}
    checks={}
    for name,ids in subsets.items():
        checks[name]={'run_indices':ids,'top_cycle_statuses':[test(messages,L,[RUNS[i] for i in ids])['status'] for L in range(1,9)]}
        print(name,checks[name]['top_cycle_statuses'],flush=True)
    classes=prefix_classes(messages);rng=random.Random(20260929);observed=max_recurrence(messages);null=[]
    for trial in range(2000):
        null.append(max_recurrence(null_corpus(classes,list(map(len,messages)),rng)))
    exceed=sum(x>=observed for x in null)
    out={'pattern_summaries':summaries,'conditional_exclusion_sensitivity':checks,
         'global_length_9_statistic':{'definition':'Maximum number of distinct literal strings sharing any length-9 equality pattern with at least 3 repeat constraints.',
            'observed':observed,'null_trials':len(null),'null_histogram':dict(Counter(null)),
            'null_exceedances':exceed,'monte_carlo_p_estimate_add_one':(exceed+1)/(len(null)+1),
            'caveat':'This compares against the stated random null only. It does not prove repeated plaintext or identify the cipher.'},
         'seconds':time.time()-start}
    (ROOT/'pattern_assumption_audit.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print(out['global_length_9_statistic']);print('seconds',out['seconds'])

if __name__=='__main__':main()
