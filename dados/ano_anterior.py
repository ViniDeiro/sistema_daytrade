"""Ano anterior do IDX (out/2024–out/2025): mesma regra (4+ iguais), 08h–22h, entrada $40, empate devolvido. Offline."""
import numpy as np, json
from collections import defaultdict
from datetime import datetime
exec(open('dados/estudo10.py').read().split("if __name__")[0])
I=prep('idx'); t,o,c=load('idx'); col=np.sign(c-o).astype(int)
CUT=datetime(2025,10,7,13,50)         # início do ano que já tínhamos
m=I['cont']&((I['hour']>=8)&(I['hour']<22))
ent=[(datetime.fromtimestamp(t[i]/1000), 0 if col[i]==0 else (1 if I['hit_c'][i] else -1)) for i in np.where(m)[0]]
val=lambda r,s: s*0.96 if r==1 else (-s if r==-1 else 0)
new=[(d,r) for d,r in ent if d<CUT]; old=[(d,r) for d,r in ent if d>=CUT]
print(f"IDX total: {len(t):,} velas | de {datetime.fromtimestamp(t[0]/1000):%d/%m/%Y} a {datetime.fromtimestamp(t[-1]/1000):%d/%m/%Y}")
def tabela(E,titulo,stake=40):
    mon=defaultdict(lambda:[0.0,0,0,set()])
    for d,r in E: k=d.strftime('%Y-%m'); mon[k][0]+=val(r,stake); mon[k][1]+=(r==1); mon[k][2]+=(r!=0); mon[k][3].add(d.date())
    print(f"\n{titulo}"); print(f"{'Mês':<20}{'Acerto':>8}{'Resultado':>13}")
    rows=[]
    for k in sorted(mon):
        p,w,n,ds=mon[k]; rows.append((k,p,len(ds),100*w/n)); lab=f"{k} ({len(ds)} dias)" if len(ds)<27 else k
        print(f"{lab:<20}{100*w/n:>7.1f}%{p:>+13,.0f}")
    pos=[r for r in rows if r[1]>0]; neg=[r for r in rows if r[1]<=0]; full=[r for r in pos if r[2]>=27]
    W=sum(1 for d,r in E if r==1); N=sum(1 for d,r in E if r!=0)
    print(f"-> acerto do período: {100*W/N:.2f}% ({N:,} entradas) | meses positivos {len(pos)}/{len(rows)} | negativos: {[(k,round(p)) for k,p,_,_ in neg]}")
    if full: mn=min(full,key=lambda r:r[1]); print(f"-> menor lucro entre positivos completos: {mn[0]} {mn[1]:+,.0f} | melhor mês: {max(rows,key=lambda r:r[1])[0]} {max(rows,key=lambda r:r[1])[1]:+,.0f} | total {sum(r[1] for r in rows):+,.0f}")
    return rows
r_new=tabela(new,"ANO ANTERIOR (10/2024 a 10/2025) — $40, 08h–22h, empate devolvido")
r_old=tabela(old,"ANO QUE JÁ TÍNHAMOS (10/2025 a 10/2026) — para comparar")
