"""Estudo 8 (offline): hipótese única -> na 1ª vela de cada quadrante de 5 min (minuto%5==0), se a vela anterior foi GRANDE
(corpo >= 2x a média das 60 anteriores), apostar na REVERSÃO. Estabilidade por trimestre (BTC) e por período (IDX). Controle: minuto%5 != 0."""
import json, math
import numpy as np
from datetime import datetime
MIN=60_000; BE=1/1.96
def load(kind):
    if kind=='idx':
        raw=sorted(json.load(open('dados/candles.json')),key=lambda c:c['t']); return np.array([c['t'] for c in raw]),np.array([c['o'] for c in raw]),np.array([c['c'] for c in raw])
    raw=json.load(open('dados/binance_BTCUSDT_1ano.json')); ks=sorted(int(k) for k in raw)
    return np.array(ks),np.array([raw[str(k)][0] for k in ks]),np.array([raw[str(k)][1] for k in ks])
def sf(k,n,p):
    z=(k-0.5-n*p)/math.sqrt(n*p*(1-p)); return 0.5*math.erfc(z/math.sqrt(2))
def run(kind,thr=2.0):
    t,o,c=load(kind); n=len(t); col=np.sign(c-o).astype(int); body=np.abs(c-o)/o
    cs=np.concatenate([[0],np.cumsum(body)]); m60=np.full(n,np.nan); m60[60:]=(cs[60:n]-cs[:n-60])/60
    idx=np.arange(n); ok=np.zeros(n,bool); ok[61:]=((t[61:]-t[:-61])==61*MIN)&(m60[61:]>0)
    minute=np.array([datetime.fromtimestamp(x/1000).minute for x in t])
    big=ok&(body[idx-1]>=thr*np.where(m60>0,m60,1))&(col[idx-1]!=0)
    hit=(col==-col[idx-1])                         # a vela de entrada fechou na cor OPOSTA à anterior (doji = perda)
    return t,big,hit,minute
print("Regra: após vela GRANDE (>=2x média das 60 anteriores), apostar na cor oposta. Equilíbrio 51,02%\n")
for kind in ('btc','idx'):
    t,big,hit,minute=run(kind)
    if kind=='btc':
        edges=np.linspace(t.min(),t.max()+1,5)               # 4 trimestres
        labs=[f"{datetime.fromtimestamp(edges[i]/1000):%d/%m/%y}-{datetime.fromtimestamp(edges[i+1]/1000):%d/%m/%y}" for i in range(4)]
    else:
        edges=np.linspace(t.min(),t.max()+1,4); labs=[f"{datetime.fromtimestamp(edges[i]/1000):%d/%m/%y}-{datetime.fromtimestamp(edges[i+1]/1000):%d/%m/%y}" for i in range(3)]
    print(f"== {kind.upper()} ==")
    for name,mask in (("1ª vela do quadrante (min%5==0)",minute%5==0),("demais velas (min%5!=0)",minute%5!=0)):
        line=[]; K=N=0
        for i in range(len(edges)-1):
            m=big&mask&(t>=edges[i])&(t<edges[i+1]); k=int(hit[m].sum()); nn=int(m.sum()); K+=k; N+=nn
            line.append(f"{labs[i]}: {100*k/nn:.1f}% ({nn})")
        print(f"  {name}: TOTAL {100*K/N:.2f}% ({N}) p={sf(K,N,BE):.3f}\n     "+" | ".join(line))
print("\nSensibilidade ao limiar de 'vela grande' (só 1ª vela do quadrante, BTC todo o ano | IDX 90d):")
for thr in (1.5,2.0,3.0,4.0):
    r=[]
    for kind in ('btc','idx'):
        t,big,hit,minute=run(kind,thr); m=big&(minute%5==0); r.append(f"{100*hit[m].sum()/m.sum():.2f}% ({int(m.sum())})")
    print(f"  >= {thr}x: BTC {r[0]} | IDX {r[1]}")
