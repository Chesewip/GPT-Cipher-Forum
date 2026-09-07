from pathlib import Path
p=Path('outputs/rotation_vote_search.py');s=p.read_text(encoding='utf-8-sig').replace('seed=20261105):','seed=20261105,temperature=1.4,block_moves=0):')
s=s.replace('votes,C,invalid=scores(messages,keys,prepared)', "if block_moves:\n                extra=[]\n                for _ in range(block_moves):\n                    a,c,e=sorted(rng.choice(np.arange(1,n+1),3,replace=False).tolist());extra.append(np.concatenate([key[:a],key[c:e],key[a:c],key[e:]]))\n                keys=np.concatenate([keys,np.array(extra)])\n            votes,C,invalid=scores(messages,keys,prepared)")
s=s.replace('temp=1.4*(1-step/steps)+0.1;', 'temp=temperature*(1-step/steps);')
s=s.replace("'comparisons':best['comparisons'],'invalid_top_selections'", "'comparisons':best['comparisons'],'temperature':temperature,'block_moves':block_moves,'invalid_top_selections'")
p.write_text(s,encoding='utf-8',newline='\r\n')
