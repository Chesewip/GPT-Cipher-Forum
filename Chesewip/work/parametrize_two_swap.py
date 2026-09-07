from pathlib import Path
p=Path('outputs/two_swap_prefix_repair.py');s=p.read_text(encoding='utf-8-sig').replace('import json,time','import json,time,argparse')
s=s.replace("source=json.loads((ROOT/'common_key_prefix_32_refined.json').read_text());", "ap=argparse.ArgumentParser();ap.add_argument('--source',default='common_key_prefix_32_refined.json');ap.add_argument('--output',default='two_swap_prefix_repair.json');args=ap.parse_args()\n    source=json.loads((ROOT/args.source).read_text());")
s=s.replace("'scope':'Two swaps; first move must repair at least one originally failed comparison and leave at most six disagreements, retaining at most the first 100 ranked moves. Not an exhaustive two-swap search.'", "'maximum_first_move_disagreements':int(bad.sum())+4,'source':args.source,'scope':'Two swaps; first move must repair at least one originally failed comparison, obey the recorded error threshold, and rank among at most 100 retained moves. Not an exhaustive two-swap search.'")
s=s.replace("(ROOT/'two_swap_prefix_repair.json')", "(ROOT/args.output)")
p.write_text(s,encoding='utf-8',newline='\r\n')
