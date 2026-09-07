"""Transition-preserving null audit of repeated equality patterns.

Uniform Euler trails of each observed directed transition multigraph are
sampled using loop-erased random walks for last-exit trees, followed by
random local edge orders. Start/end, symbol counts and bigram counts stay
fixed. An optional fixed prefix preserves the observed shared beginnings.
"""
from pathlib import Path
from collections import Counter,defaultdict
import random,json,time,argparse,itertools
from pattern_assumption_audit import max_recurrence
ROOT=Path(__file__).resolve().parent

class EulerSampler:
    def __init__(self,sequence):
        self.seq=list(sequence);self.start=sequence[0];self.end=sequence[-1]
        self.edges=list(zip(sequence,sequence[1:]));self.out=defaultdict(list)
        for e,(u,v) in enumerate(self.edges):self.out[u].append(e)
        self.vertices=set(sequence)
    def draw(self,rng):
        if not self.edges:return self.seq.copy()
        tree={self.end};last={}
        # Wilson's loop-erased random walk algorithm, rooted at the end vertex.
        for origin in sorted(self.vertices):
            v=origin
            while v not in tree:
                e=rng.choice(self.out[v]);last[v]=e;v=self.edges[e][1]
            v=origin
            while v not in tree:
                tree.add(v);v=self.edges[last[v]][1]
        ordered={}
        for v,edges in self.out.items():
            remaining=[e for e in edges if v==self.end or e!=last[v]]
            rng.shuffle(remaining)
            if v!=self.end:remaining.append(last[v])
            ordered[v]=remaining
        cursor=Counter();v=self.start;result=[v]
        for _ in self.edges:
            e=ordered[v][cursor[v]];cursor[v]+=1;v=self.edges[e][1];result.append(v)
        assert v==self.end
        return result

def verify():
    rng=random.Random(20261018);checks=0;distribution=[]
    # Enumerate labeled-edge Euler trails; repeated edges give equal multiplicity per symbol sequence.
    for seq in [[0,1,0,2,0,1,2],[0,1,2,0,2,1,0],[0,1,0,2,1,2,0,3]]:
        sampler=EulerSampler(seq);valid=set()
        for order in itertools.permutations(range(len(sampler.edges))):
            v=seq[0];trail=[v]
            for e in order:
                u,w=sampler.edges[e]
                if u!=v:break
                trail.append(w);v=w
            else:valid.add(tuple(trail))
        samples=Counter()
        for _ in range(12000):
            trial=sampler.draw(rng);assert tuple(trial) in valid
            assert Counter(zip(trial,trial[1:]))==Counter(sampler.edges)
            samples[tuple(trial)]+=1;checks+=1
        assert set(samples)==valid
        expected=12000/len(valid);chi=sum((count-expected)**2/expected for count in samples.values())
        distribution.append({'distinct_trails':len(valid),'samples':12000,'chi_square_descriptive':chi,
                             'maximum_absolute_probability_error':max(abs(count/12000-1/len(valid)) for count in samples.values())})
    return {'enumerated_trail_membership_checks':checks,'small_distribution_checks':distribution}

def prefix_lengths(messages):
    protected=[1]*len(messages)
    for i,m in enumerate(messages):
        for j,v in enumerate(messages[:i]):
            t=1
            while t<min(len(m),len(v)) and m[t]==v[t]:t+=1
            protected[i]=max(protected[i],t);protected[j]=max(protected[j],t)
    return protected

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--trials',type=int,default=2000);args=ap.parse_args()
    start=time.time();out=verify();messages=list(json.loads((ROOT/'ciphertext.json').read_text()).values())
    observed=max_recurrence(messages);protected=prefix_lengths(messages);cases=[]
    for mode in ['whole_message','fixed_shared_prefix']:
        rng=random.Random(20261019);cuts=[0]*len(messages) if mode=='whole_message' else [n-1 for n in protected]
        samplers=[EulerSampler(m[cut:]) for m,cut in zip(messages,cuts)];hist=Counter();changes=[];distinct_corpora=set()
        for trial in range(args.trials):
            corpus=[m[:cut]+sampler.draw(rng) for m,cut,sampler in zip(messages,cuts,samplers)]
            for original,sampled,cut in zip(messages,corpus,cuts):
                assert len(original)==len(sampled) and original[0]==sampled[0] and original[-1]==sampled[-1]
                assert Counter(original)==Counter(sampled)
                assert Counter(zip(original,original[1:]))==Counter(zip(sampled,sampled[1:]))
                assert original[:cut+1]==sampled[:cut+1]
            statistic=max_recurrence(corpus);hist[statistic]+=1
            changes.append(sum(x!=y for m,v in zip(messages,corpus) for x,y in zip(m,v)))
            distinct_corpora.add(tuple(tuple(m) for m in corpus))
            if (trial+1)%500==0:print(mode,trial+1,dict(sorted(hist.items())),flush=True)
        exceed=sum(v for k,v in hist.items() if k>=observed)
        cases.append({'mode':mode,'observed':observed,'trials':args.trials,'histogram':dict(sorted(hist.items())),
                      'at_least_observed':exceed,'add_one_estimate':(exceed+1)/(args.trials+1),
                      'mean_changed_positions':sum(changes)/len(changes),'minimum_changed_positions':min(changes),
                      'distinct_corpora':len(distinct_corpora),'frozen_prefix_lengths':[c+1 for c in cuts]})
    out.update(cases=cases,seconds=time.time()-start,
               statistic='Maximum number of distinct literal strings sharing any length-9 equality pattern with at least three repeat constraints.',
               caveat='Conditional null audit, not a probability that a cipher hypothesis is correct. This statistic was chosen during the investigation; model selection across the investigation is not corrected.')
    (ROOT/'transition_pattern_audit.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8',newline='\r\n')
    print('seconds',out['seconds']);print(cases)
