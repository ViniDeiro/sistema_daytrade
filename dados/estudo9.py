"""Estudo 9 (offline): regra 'reversão após vela grande, na 1ª vela do quadrante'. Limiar escolhido SÓ no treino do BTC (antes de 09/07/2026).
Validação: BTC 09/07-07/10, IDX 90d, ETH e SOL (1 mês). Depois: simulação de banca no IDX."""
import json, math, random
import numpy as np
from collections import defaultdict
from datetime import datetime
MIN=60_000; BE=1/1.96; PAY=0.96
SPLIT=int(datetime(2026,7,9).timestamp()*1000)
def load(kind):
    if kind=='idx':
        raw=sorted(json.load(open('dados/candles.json')),key=lambda c:c['t']); return np.array([c['t'] for c in raw]),np.array([c['o'] for c in raw]),np.array([c['c'] for c in raw])
    f={'btc':'dados/binance_BTCUSDT_1ano.json','eth':'dados/binance_ETHUSDT_1mes.json','sol':'dados/binance_SOLUSDT_1mes.json'}[kind]
    raw=json.load(open(f)); ks=sorted(int(k) for k in raw)
    return np.array(ks),np.array([raw[str(k)][0] for k in ks]),np.array([raw[str(k)][1] for k in ks])
def sf(k,n,p):
    if n==0: return 1.0
    z=(k-0.5-n*p)/math.sqrt(n*p*(1-p)); return 0.5*math.erfc(z/math.sqrt(2))
def trades(kind,thr):
    t,o,c=load(kind); n=len(t); col=np.sign(c-o).astype(int); body=np.abs(c-o)/o
    cs=np.concatenate([[0],np.cumsum(body)]); m60=np.full(n,np.nan); m60[60:]=(cs[60:n]-cs[:n-60])/60
    idx=np.arange(n); ok=np.zeros(n,bool); ok[61:]=((t[61:]-t[:-61])==61*MIN)&(m60[61:]>0)
    minute=np.array([datetime.fromtimestamp(x/1000).minute for x in t]); hour=np.array([datetime.fromtimestamp(x/1000).hour for x in t])
    sel=ok&(minute%5==0)&(body[idx-1]>=thr*np.where(m60>0,m60,1))&(col[idx-1]!=0)
    return t[sel],(col==-col[idx-1])[sel],hour[sel]
print("1) Escolha do limiar SÓ no treino do BTC (10/2025 a 09/07/2026):")
best=None
for thr in (1.5,2,2.5,3,3.5,4,5):
    t,h,_=trades('btc',thr); m=t<SPLIT; k=int(h[m].sum()); n=int(m.sum())
    print(f"   >= {thr}x: treino {100*k/n:.2f}% ({n}) p={sf(k,n,BE):.4f}")
    if n>=1500 and (best is None or k/n>best[1]): best=(thr,k/n,n)
THR=best[0]; print(f"   -> limiar escolhido pelo treino: {THR}x (acerto {100*best[1]:.2f}%, n={best[2]})\n")
print(f"2) Validação com limiar {THR}x (nenhum desses dados participou da escolha):")
for kind,lab in (('btc','BTC 09/07-07/10'),('idx','IDX 09/07-07/10 (Ebinex)'),('eth','ETH ~1 mês'),('sol','SOL ~1 mês')):
    t,h,_=trades(kind,THR)
    m=(t>=SPLIT) if kind=='btc' else np.ones(len(t),bool)
    k=int(h[m].sum()); n=int(m.sum())
    day=[datetime.fromtimestamp(x/1000).date() for x in t[m]]; dd=defaultdict(lambda:[0,0])
    for d_,hh in zip(day,h[m]): dd[d_][0]+=int(hh); dd[d_][1]+=1
    ks=list(dd); random.seed(5); b=[]
    for _ in range(2000):
        sm=[dd[random.choice(ks)] for _ in ks]; b.append(sum(x[0] for x in sm)/sum(x[1] for x in sm))
    b.sort()
    print(f"   {lab:<28}: {100*k/n:.2f}% ({n}, ~{n/len(ks):.1f}/dia) IC95% [{100*b[50]:.1f}, {100*b[1950]:.1f}] P(real<=51,02%)={sum(x<=BE for x in b)/2000:.3f}")
print("\n3) IDX por período de 30 dias e simulação de banca ($2.000, mão fixa), sem filtro de horário e com 08h-22h:")
t,h,hr=trades('idx',THR); t0,t1=t.min(),t.max(); 
tt=np.array(sorted(json.load(open('dados/candles.json')),key=lambda c:c['t'])[0]['t']),
allt=load('idx')[0]; T0,T1=allt.min(),allt.max(); P=(T1-T0)/3
for nome,mask in (("24h",np.ones(len(t),bool)),("08h-22h",(hr>=8)&(hr<22))):
    tr=t[mask]; hh=h[mask]
    per=[(int(((tr>=T0+P*i)&(tr<T0+P*(i+1)+(1 if i==2 else 0))&hh).sum()),int(((tr>=T0+P*i)&(tr<T0+P*(i+1)+(1 if i==2 else 0))).sum())) for i in range(3)]
    print(f"  [{nome}] acerto por período: "+" | ".join(f"{100*k/n:.1f}% ({n})" for k,n in per)+f" | total {100*hh.sum()/len(hh):.2f}% ({len(hh)}, {len(hh)/90:.1f}/dia)")
    for st in (20,40,100):
        eq=2000; pk=2000; dd_=0; low=2000; bust=False
        for x in hh:
            if eq<st: bust=True; break
            eq+= st*PAY if x else -st; pk=max(pk,eq); dd_=max(dd_,pk-eq); low=min(low,eq)
        print(f"     ${st:>3} fixo: resultado {eq-2000:+,.0f} em 90 dias ({(eq-2000)/90:+.1f}/dia) | menor banca {low:,.0f} | maior queda {dd_:,.0f} | {'QUEBROU' if bust else 'não quebrou'}")
