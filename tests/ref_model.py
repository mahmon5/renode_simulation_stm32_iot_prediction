import math, random, subprocess
from collections import deque 

class MA:
    def __init__(self,n=5): self.q = deque(maxlen=n)
    def ma_update(self,x): 
        self.q.append(x)
        return int(sum(self.q)/len(self.q))
    
def pitch_cdeg(ax,az): return int((math.atan2(ax,az) * 180 * 100) / math.pi)


random.seed(42)
N=1000
pairs = [(random.randint(-1000,1000),random.randint(-1000,1000)) 
          for _ in range(N)]

entree = "".join(f"{ax},{az}\n" for ax,az in pairs)
res = subprocess.run(
    ["./test_core"],
    input=entree,
    capture_output=True,
    text=True,
    check=True
)

c_out = [tuple(map(int,l.split(","))) for l in res.stdout.strip().splitlines()]

Qx = MA()
Qz = MA()

ref = []
for ax, az in pairs:
    fx = Qx.ma_update(ax)
    fz = Qz.ma_update(az)
    pitch = pitch_cdeg(ax, az)
    fpitch = pitch_cdeg(fx,fz)
    ref.append((ax,az,fx,fz,pitch,fpitch))


assert len(c_out) == len(ref), f"recue={len(c_out)} , attendue={len(ref)}"

ma_faux = 0
ecart_max = 0
ecart_non_nul = 0
for c,r in zip(c_out,ref):
    
        if c[:4] != r[:4]:
            ma_faux +=1
        for i in (4,5):
            d = abs(c[i] - r[i])
            ecart_max = max(ecart_max,d)
            ecart_non_nul += d>0
    
print(f"Lignes comparées        : {N}")
print(f"Moyenne glissante fausse: {ma_faux}")
print(f"Angles différents       : {ecart_non_nul}")
print(f"Écart max sur l'angle   : {ecart_max} centi-degré")
print("OK" if ma_faux == 0 and ecart_max <= 1 else "ECHEC")
        
            