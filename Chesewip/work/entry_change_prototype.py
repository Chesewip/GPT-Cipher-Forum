import json,math
from pathlib import Path
raw=list(json.loads(Path('outputs/ciphertext.json').read_text()).values())
def cost(a,b,n=83):
    result=[]
    for x in range(n):
        possible={x};c=0
        for ca,cb in zip(a,b):
            allowed={cb} if ca==x else set(range(n))-{cb}
            next_possible=possible&allowed
            if not next_possible:c+=1;possible=allowed
            else:possible=next_possible
        result.append(c)
    return sum(result),result
for N in [25,29,34,35,36,37,50,99]:
    a,b=raw[0][:N],raw[1][:N];f,rows=cost(a,b);r,_=cost(b,a)
    print(N,f,r,'s5',math.ceil(max(f,r)/5),'s3',math.ceil(max(f,r)/3),flush=True)
