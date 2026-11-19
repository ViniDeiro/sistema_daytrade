"""MEMX/USDT (Ebinex): a regra '4+ velas iguais -> repete', em 3 períodos de 30 dias, comparada ao IDX nas mesmas datas. Offline."""
import json, math
import numpy as np
from datetime import datetime
exec(open('dados/estudo10.py').read().split("if __name__")[0])
_old=load
def load(kind):
    if kind=='memx':
        raw=sorted(json.load(open('dados/MEMXUSDT_candles.json')),key=lambda c:c['t']); return np.array([c['t'] for c in raw]),np.array([c['o'] for c in raw]),np.array([c['c'] for c in raw])
    return _old(kind)
M=prep('memx'); I=prep('idx'); tM=M['t']
print(f"MEMX: {len(tM)} velas | {datetime.fromtimestamp(tM[0]/1000):%d/%m/%Y} a {datetime.fromtimestamp(tM[-1]/1000):%d/%m/%Y}")
t,o,c=load('memx'); print(f"  dojis (fechou = abriu): {100*np.mean(c==o):.2f}% (IDX: {100*np.mean(load('idx')[2]==load('idx')[1]):.2f}%) | velas/dia: {len(tM)/((tM[-1]-tM[0])/86400000):.0f} de 1440")
t0,t1=tM.min(),tM.max(); P=(t1-t0)/3
def sf(k,n,p):
    z=(k-0.5-n*p)/math.sqrt(n*p*(1-p)); return 0.5*math.erfc(z/math.sqrt(2))
for nome,mk in (("24 horas",lambda P_: np.ones(len(P_['t']),bool)),("08h-22h",lambda P_: (P_['hour']>=8)&(P_['hour']<22))):
    print(f"\n=== Regra 1 (4+ iguais) — {nome} ===")
    print(f"{'período':<18}{'MEMX acerto':>14}{'entradas':>10}{'$20 fixo':>11}   | {'IDX (mesmas datas)':>22}")
    K=N=0
    for i in range(3):
        a,b=t0+P*i,t0+P*(i+1)+(1 if i==2 else 0)
        mm=M['cont']&mk(M)&(M['t']>=a)&(M['t']<b); mi=I['cont']&mk(I)&(I['t']>=a)&(I['t']<b)
        k=int(M['hit_c'][mm].sum()); n=int(mm.sum()); u=20*(k*PAY-(n-k)); K+=k; N+=n
        ki=int(I['hit_c'][mi].sum()); ni=int(mi.sum())
        print(f"{datetime.fromtimestamp(a/1000):%d/%m}-{datetime.fromtimestamp(b/1000):%d/%m}      {100*k/n:>10.2f}% {n:>10}{u:>+11,.0f}   | {100*ki/ni:>9.2f}% ({ni})")
    print(f"TOTAL MEMX: {100*K/N:.2f}% em {N} entradas ({N/90:.0f}/dia) | equilíbrio {100*BE:.2f}% | p(acaso, acima do equilíbrio)={sf(K,N,BE):.4f}")
# por tamanho da sequência
col=np.sign(c-o).astype(int); n=len(col); contig=np.zeros(n,bool); contig[1:]=(t[1:]-t[:-1])==60000
run=np.zeros(n,int)
for i in range(1,n): run[i]=(run[i-1]+1 if (col[i]!=0 and contig[i] and col[i]==col[i-1]) else (1 if col[i]!=0 else 0))
pr=np.zeros(n,int); pr[1:]=run[:-1]; idx=np.arange(n); el=contig&(col[idx-1]!=0); hit=(col==col[idx-1])&el
print("\nAcerto por tamanho da sequência antes da entrada (MEMX, 3 meses, 24h):")
print("  "+" | ".join(f"s={s}: {100*hit[(pr==s)&el].mean():.1f}% ({int(((pr==s)&el).sum())})" for s in range(1,9)))
# regra 2
for nome,mk in (("24h",np.ones(len(tM),bool)),("08-22h",(M['hour']>=8)&(M['hour']<22))):
    mm=M['rev']&mk; k=int(M['hit_r'][mm].sum()); n_=int(mm.sum())
    print(f"Regra 2 (reversão após vela grande) {nome}: {100*k/max(n_,1):.2f}% em {n_} entradas")
# maior sequência de perdas e maior queda (08-22h, $20)
mm=M['cont']&((M['hour']>=8)&(M['hour']<22)); ii=np.where(mm)[0]; lost=~M['hit_c'][ii]
cur=best=0; eq=pk=dd=0
for k,x in zip(ii,lost):
    cur=cur+1 if x else 0; best=max(best,cur); eq+= -20 if x else 20*PAY; pk=max(pk,eq); dd=max(dd,pk-eq)
print(f"MEMX 08-22h $20: resultado {eq:+,.0f} em 90 dias | maior queda ${dd:,.0f} | maior sequência de perdas {best}")
