"""Mescla de padrões (offline, IDX 2 anos, 08–22h, $40, empate devolvido). Descoberta ano 1 -> teste ano 2 quando há escolha."""
import numpy as np, math
from collections import defaultdict
from datetime import datetime
raw=__import__('json').load(open('dados/candles.json')); raw.sort(key=lambda c:c['t'])
t=np.array([c['t'] for c in raw]); o=np.array([c['o'] for c in raw]); c=np.array([c['c'] for c in raw]); n=len(t); MIN=60000
col=np.sign(c-o).astype(int); body=np.abs(c-o)/o
contig=np.zeros(n,bool); contig[1:]=(t[1:]-t[:-1])==MIN
run=np.zeros(n,int)
for i in range(1,n): run[i]=(run[i-1]+1 if (col[i]!=0 and contig[i] and col[i]==col[i-1]) else (1 if col[i]!=0 else 0))
idx=np.arange(n); pr=run[idx-1]
dts=[datetime.fromtimestamp(x/1000) for x in t]; hour=np.array([d.hour for d in dts]); minute=np.array([d.minute for d in dts]); day=np.array([d.date() for d in dts])
inwin=(hour>=8)&(hour<22); CUT=datetime(2025,10,7,13,50).timestamp()*1000; y1=t<CUT; y2=~y1; BE=1/1.96
cs=np.concatenate([[0],np.cumsum(body)]); m60=np.full(n,np.nan); m60[60:]=(cs[60:n]-cs[:n-60])/60
ok60=np.zeros(n,bool); ok60[61:]=((t[61:]-t[:-61])==61*MIN)&(m60[61:]>0)
el=contig&(col[idx-1]!=0)
# regra 1
r1=el&(pr>=4)&inwin&(col!=0); w1=(col==col[idx-1])
# regra 2: 1ª vela do quadrante, vela anterior grande (>=3x), aposta contrária
r2=ok60&(minute%5==0)&(body[idx-1]>=3*np.where(m60>0,m60,1))&(col[idx-1]!=0)&inwin&(col!=0); w2=(col==-col[idx-1])
def pl(m,w): return np.where(w[m],38.4,-40.0)
def daily(m,w):
    d=defaultdict(float)
    for i in np.where(m)[0]: d[day[i]]+= 38.4 if w[i] else -40
    return d
print("1) PADRÃO EM PARALELO: regra 2 (reversão após vela grande, 1ª vela do quadrante de 5 min)")
for nome,per in (("ano 1 (nunca usado p/ descobrir)",y1),("ano 2",y2)):
    m=r2&per; k=int((m&w2).sum()); nn=int(m.sum()); print(f"   {nome}: {100*k/nn:.2f}% em {nn:,} entradas ({nn/365:.1f}/dia) -> $40: {40*(k*0.96-(nn-k)):+,.0f}")
d1=daily(r1,w1); d2=daily(r2,w2); days=sorted(set(d1)|set(d2)); a=np.array([d1.get(k,0) for k in days]); b=np.array([d2.get(k,0) for k in days])
def dd(x): e=np.cumsum(x); return (np.maximum.accumulate(e)-e).max()
print(f"   correlação diária entre regra 1 e regra 2: {np.corrcoef(a,b)[0,1]:+.2f}")
print(f"   só regra 1: total {a.sum():+,.0f}, pior dia {a.min():+,.0f}, maior queda {dd(a):,.0f} | só regra 2: total {b.sum():+,.0f}, pior dia {b.min():+,.0f}, maior queda {dd(b):,.0f} | AS DUAS: total {(a+b).sum():+,.0f}, pior dia {(a+b).min():+,.0f}, maior queda {dd(a+b):,.0f}")
# 2) filtros dentro da regra 1: quartis (definidos no ano 1)
print("\n2) FILTROS dentro da regra 1 — acerto por quartil (cortes definidos no ano 1)")
net=np.where(el,np.abs(c-o[idx-pr])/o[idx-pr] if False else 0,0)
# força da sequência: variação líquida (fechamento da última - abertura da 1ª da sequência) relativa à média de corpos
start=idx-pr; netmove=np.abs(c[idx-1]-o[np.maximum(start,0)])/o[np.maximum(start,0)]
strength=np.where(ok60,netmove/np.where(m60>0,m60,1),np.nan)
lastbody=np.where(ok60,body[idx-1]/np.where(m60>0,m60,1),np.nan)
feats={"força da sequência (movimento líquido / corpo médio)":strength,"corpo da última vela da sequência (vs média)":lastbody}
for nome,f in feats.items():
    base=r1&ok60&~np.isnan(f); qs=np.nanpercentile(f[base&y1],[25,50,75]); cat=np.digitize(f,qs)
    print(f"   {nome}  (cortes ano 1: {np.round(qs,2)})")
    for q in range(4):
        r=[]
        for per in (y1,y2):
            m=base&per&(cat==q); k=int((m&w1).sum()); nn=int(m.sum()); r.append(f"{100*k/nn:.1f}% ({nn:,})")
        print(f"      quartil {q+1}: ano1 {r[0]} | ano2 {r[1]}")
# 3) dependência do resultado anterior (sequência de entradas da regra 1)
print("\n3) O QUE FAZER DEPOIS DE UMA PERDA? acerto da regra 1 conforme o resultado das entradas anteriores (sequência cronológica)")
ii=np.where(r1)[0]; res=np.array([1 if w1[i] else 0 for i in ii]); tt=t[ii]
for L in (1,2,3,4):
    sel=[k for k in range(L,len(res)) if res[k-L:k].sum()==0]          # as L anteriores foram perdas
    selw=[k for k in range(L,len(res)) if res[k-L:k].sum()==L]         # as L anteriores foram wins
    print(f"   depois de {L} perda(s) seguida(s): {100*res[sel].mean():.1f}% ({len(sel):,}) | depois de {L} win(s) seguido(s): {100*res[selw].mean():.1f}% ({len(selw):,}) | geral {100*res.mean():.1f}%")
