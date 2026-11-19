"""Estudo 10 (offline): 1 ano de IDX (Ebinex). Duas regras, mês a mês, com banca. Compara com o BTC público nos mesmos meses."""
import json, math, random
import numpy as np
from collections import defaultdict
from datetime import datetime
MIN=60_000; BE=1/1.96; PAY=0.96; BANCA=2000
def load(kind):
    if kind=='idx':
        raw=sorted(json.load(open('dados/candles.json')),key=lambda c:c['t']); return np.array([c['t'] for c in raw]),np.array([c['o'] for c in raw]),np.array([c['c'] for c in raw])
    raw=json.load(open('dados/binance_BTCUSDT_1ano.json')); ks=sorted(int(k) for k in raw)
    return np.array(ks),np.array([raw[str(k)][0] for k in ks]),np.array([raw[str(k)][1] for k in ks])
def prep(kind):
    t,o,c=load(kind); n=len(t); col=np.sign(c-o).astype(int); body=np.abs(c-o)/o; idx=np.arange(n)
    hour=np.array([datetime.fromtimestamp(x/1000).hour for x in t]); minute=np.array([datetime.fromtimestamp(x/1000).minute for x in t])
    ym=np.array([datetime.fromtimestamp(x/1000).strftime('%Y-%m') for x in t])
    # sequência de velas iguais terminando em i-1
    run=np.zeros(n,int); contig=np.zeros(n,bool); contig[1:]=(t[1:]-t[:-1])==MIN
    for i in range(1,n):
        if col[i]!=0 and contig[i] and col[i]==col[i-1]: run[i]=run[i-1]+1
        else: run[i]=1 if col[i]!=0 else 0
    prev_run=np.zeros(n,int); prev_run[1:]=run[:-1]
    cs=np.concatenate([[0],np.cumsum(body)]); m60=np.full(n,np.nan); m60[60:]=(cs[60:n]-cs[:n-60])/60
    ok60=np.zeros(n,bool); ok60[61:]=((t[61:]-t[:-61])==61*MIN)&(m60[61:]>0)
    cont=(prev_run>=4)&contig&(col[idx-1]!=0)
    hit_c=(col==col[idx-1])
    rev=ok60&(minute%5==0)&(body[idx-1]>=3.0*np.where(m60>0,m60,1))&(col[idx-1]!=0)
    hit_r=(col==-col[idx-1])
    return dict(t=t,hour=hour,ym=ym,cont=cont,hit_c=hit_c,rev=rev,hit_r=hit_r)
def table(P,mask,hit,label,stakes=(20,40)):
    print(f"\n{label}")
    print(f"   {'mês':<8}{'acerto':>8}{'entradas':>9}"+"".join(f"{'$'+str(s):>10}" for s in stakes))
    mons=sorted(set(P['ym'][mask])); pos=0; tot=[0]*len(stakes); K=N=0
    for m in mons:
        sel=mask&(P['ym']==m); k=int(hit[sel].sum()); n=int(sel.sum())
        if n<30: continue
        u=k*PAY-(n-k); K+=k; N+=n; pos+=u>0
        for j,s in enumerate(stakes): tot[j]+=s*u
        print(f"   {m:<8}{100*k/n:>7.2f}%{n:>9}"+"".join(f"{s*u:>+10,.0f}" for s in stakes))
    print(f"   ANO: {100*K/N:.2f}% ({N}) | meses positivos {pos}/{len([m for m in mons if int((mask&(P['ym']==m)).sum())>=30])} | total "+" | ".join(f"${s}: {x:+,.0f}" for s,x in zip(stakes,tot)))
    return K,N
def bank(P,mask,hit,stake,start_filter=None):
    ii=np.where(mask)[0]; eq=BANCA; pk=BANCA; dd=0; low=BANCA; bust=None
    for i in ii:
        if eq<stake: bust=P['t'][i]; break
        eq+= stake*PAY if hit[i] else -stake; pk=max(pk,eq); dd=max(dd,pk-eq); low=min(low,eq)
    return eq,low,dd,bust
if __name__=='__main__':
    I=prep('idx'); B=prep('btc')
    t=I['t']; print(f"IDX: {len(t)} velas | {datetime.fromtimestamp(t[0]/1000):%d/%m/%Y} a {datetime.fromtimestamp(t[-1]/1000):%d/%m/%Y} ({(t[-1]-t[0])/86400_000:.0f} dias)")
    day=(I['hour']>=8)&(I['hour']<22)
    for nome,mask in (("24 HORAS",np.ones(len(t),bool)),("08h-22h",day)):
        table(I,I['cont']&mask,I['hit_c'],f"REGRA 1 — 4+ velas iguais, a próxima repete | IDX | {nome}")
    # comparação com BTC nos mesmos meses
    print("\nPrêmio do IDX sobre o BTC (regra 1, 24h), por mês:")
    mons=sorted(set(I['ym'])&set(B['ym']))
    for m in mons:
        si=I['cont']&(I['ym']==m); sb=B['cont']&(B['ym']==m)
        if si.sum()<200 or sb.sum()<200: continue
        a=100*I['hit_c'][si].mean(); b=100*B['hit_c'][sb].mean(); print(f"   {m}: IDX {a:.2f}% | BTC {b:.2f}% | diferença {a-b:+.2f}")
    for nome,mask in (("24 HORAS",np.ones(len(t),bool)),("08h-22h",day)):
        table(I,I['rev']&mask,I['hit_r'],f"REGRA 2 — reversão após vela grande (3x), 1ª vela do quadrante | IDX | {nome}")
    print("\nBanca de $2.000 desde o 1º dia do ano, regra 1, 08h-22h, mão fixa:")
    for pct in (1,2,3):
        s=BANCA*pct/100; eq,low,dd,bust=bank(I,I['cont']&day,I['hit_c'],s)
        print(f"   {pct}% (${s:.0f}): final {eq:,.0f} | menor {low:,.0f} | maior queda {dd:,.0f} | {'QUEBROU em '+datetime.fromtimestamp(bust/1000).strftime('%d/%m/%Y') if bust else 'não quebrou'}")
