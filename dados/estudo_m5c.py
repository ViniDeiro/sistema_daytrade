"""M5 (parte 3, offline): gatilho de velas M1 iguais, mas a ENTRADA só na abertura de uma vela M5 e vitória pela cor dessa vela M5 (mecânica de expiração M5)."""
import json, math
import numpy as np
from datetime import datetime
src=open('dados/estudo_m5.py').read().split("def sf(")[0]
exec(src.replace('print(f"Velas M5','pass #'))
BEq=1/1.96
def sf(k,nn,p):
    if nn==0: return 1.0
    z=(k-0.5-nn*p)/math.sqrt(nn*p*(1-p)); return 0.5*math.erfc(z/math.sqrt(2))
col1=np.sign(c-o).astype(int); n1=len(t)
contig1=np.zeros(n1,bool); contig1[1:]=(t[1:]-t[:-1])==MIN
run1=np.zeros(n1,int)
for i in range(1,n1): run1[i]=(run1[i-1]+1 if (col1[i]!=0 and contig1[i] and col1[i]==col1[i-1]) else (1 if col1[i]!=0 else 0))
# para cada vela M5 (índice i), a última vela M1 antes da abertura dela é first[i]-1 (se contígua)
f=first; prevM1=f-1; okp=(prevM1>=0)&(t[f]-t[np.maximum(prevM1,0)]==MIN)
rl=np.where(okp,run1[np.maximum(prevM1,0)],0); dr=np.where(okp,col1[np.maximum(prevM1,0)],0)
hr=hour
print("Gatilho: k+ velas M1 iguais imediatamente antes da abertura da vela M5; aposta que a vela M5 inteira fecha na mesma cor.")
print(f"{'k':>3}{'ANO 1':>34}{'ANO 2':>34}{'entradas/dia (08–22h)':>24}")
for k in (3,4,5,6,7,8):
    out=[]; epd=0
    for per in (isA,isB):
        m=(rl>=k)&(dr!=0)&per&(hr>=8)&(hr<22)&(col!=0)
        w=int((m&(col==dr)).sum()); nn=int(m.sum()); out.append(f"{100*w/nn:.2f}% ({nn:,}) p={sf(w,nn,BEq):.3f}"); epd=nn/ (365 if per is isA else 365)
    print(f"{k:>3}{out[0]:>34}{out[1]:>34}{epd:>24.1f}")
# resultado em dinheiro, $40, k=4..6 (24 meses)
print("\nResultado com $40 por entrada, 08–22h, empate devolvido (payout 96%; confirmar o do M5):")
for k in (4,5,6):
    for pn,per in (("ano 1",isA),("ano 2",isB)):
        m=(rl>=k)&(dr!=0)&per&(hr>=8)&(hr<22)&(col!=0); w=int((m&(col==dr)).sum()); nn=int(m.sum()); pl=40*(w*0.96-(nn-w))
        print(f"   k={k} {pn}: {nn:,} entradas, {w:,} wins ({100*w/nn:.2f}%) -> {pl:+,.0f} em 12 meses ({nn/365:.1f}/dia, {pl/365:+.0f}/dia)")
# mês a mês, k=5
print("\nk=5, mês a mês ($40):")
mm={}
for i in np.where((rl>=5)&(dr!=0)&(hr>=8)&(hr<22)&(col!=0))[0]:
    key=dts[i].strftime('%Y-%m'); w=(col[i]==dr[i]); mm.setdefault(key,[0,0.0,0]); mm[key][0]+=int(w); mm[key][2]+=1; mm[key][1]+= 38.4 if w else -40
pos=0
for k_ in sorted(mm): pos+= mm[k_][1]>0
print("  "+" | ".join(f"{k_[2:]}: {100*v[0]/v[2]:.0f}% {v[1]:+,.0f}" for k_,v in sorted(mm.items())))
print(f"  meses positivos: {pos} de {len(mm)}")
