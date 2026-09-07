from pathlib import Path
p=Path('outputs/permutation_action_fold.py')
s=p.read_text(encoding='utf-8-sig').replace('def solve(pts,cts):','def solve(pts,cts,include_forced=False):')
s=s.replace("out['folded_edges']=sum(len(f.adj[i]) for i in roots)//2", """out['folded_edges']=sum(len(f.adj[i]) for i in roots)//2
        if include_forced:
            by_source={};back={v:k for k,v in alphabet.items()};top=f.root(top)
            for label,target in f.adj[top].items():
                if label>0:by_source.setdefault(f.root(target),[]).append(back[label])
            out['forced_equal_operations']=[v for v in by_source.values() if len(v)>1]
            out['forced_fixed_output_operations']=by_source.get(top,[])""")
p.write_text(s,encoding='utf-8',newline='\r\n')
