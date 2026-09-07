from pathlib import Path
import json
root=Path('outputs')
for name in ['rotation_vote_control.json','rotation_vote_eyes.json','rotation_vote_control_near.json']:
    p=root/name;r=json.loads(p.read_text());r.update(temperature=1.4,temperature_floor=0.1,block_moves=0);p.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n')
for name in ['rotation_vote_control_refined.json','rotation_vote_eyes_refined.json']:
    p=root/name;r=json.loads(p.read_text());r['temperature_floor']=0;r['seed']=20261107;p.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\r\n')
