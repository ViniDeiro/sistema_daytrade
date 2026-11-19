"""Robustez ao dia de início (offline), 1 ano de IDX, regra 1 (4+ iguais), mão fixa. Cada dia do ano como início; opera N dias seguidos."""
import numpy as np
from collections import defaultdict
from datetime import datetime
exec(open('dados/estudo10.py').read().split("if __name__")[0])
I=prep('idx'); t=I['t']; day=(I['hour']>=8)&(I['hour']<22)
for nome,mask in (("08h-22h",day),("24 horas",np.ones(len(t),bool))):
    ii=np.where(I['cont']&mask)[0]; by=defaultdict(list)
    for i in ii: by[datetime.fromtimestamp(t[i]/1000).date()].append(bool(I['hit_c'][i]))
    days=sorted(by); print(f"\n=== Regra 1, {nome}: {len(days)} dias; início em cada dia, 30 dias seguidos, banca $2.000 ===")
    print(f"{'%':<3}{'entrada':>8} | {'inícios':>7} | {'terminam +':>10} | {'quebram':>7} | {'menor banca':>11} | {'pior 30d':>9} | {'mediana':>8} | {'melhor':>8}")
    for pct in (1,2,3,4,5):
        st=2000*pct/100; res=[]
        for k in range(0,len(days)-29):
            eq=2000; low=2000; bust=False
            for d_ in days[k:k+30]:
                for h in by[d_]:
                    if eq<st: bust=True; break
                    eq+= st*0.96 if h else -st; low=min(low,eq)
                if bust: break
            res.append((eq-2000,bust,low))
        pl=sorted(r[0] for r in res)
        print(f"{pct:<3}{'$'+str(int(st)):>8} | {len(res):>7} | {sum(r[0]>0 for r in res):>10} | {sum(r[1] for r in res):>7} | {min(r[2] for r in res):>11,.0f} | {pl[0]:>+9,.0f} | {pl[len(pl)//2]:>+8,.0f} | {pl[-1]:>+8,.0f}")
