"""Plano B (offline): estratégias populares da internet, testadas no IDX M1, 2 anos, 08–22h. Aposta a cor da PRÓXIMA vela. Empate devolvido, payout 96%.
Cada regra é definida SÓ com a vela anterior fechada e as anteriores. Ano 1 = descoberta; ano 2 = teste."""
import numpy as np, json, math
from datetime import datetime
from numpy.lib.stride_tricks import sliding_window_view as swv
raw=json.load(open('dados/candles.json')); raw.sort(key=lambda x:x['t'])
t=np.array([x['t'] for x in raw]); o=np.array([x['o'] for x in raw]); h=np.array([x['h'] for x in raw]); l=np.array([x['l'] for x in raw]); c=np.array([x['c'] for x in raw]); n=len(t); MIN=60000
col=np.sign(c-o).astype(int); idx=np.arange(n)
contig=np.zeros(n,bool); contig[2:]=((t[1:]-t[:-1])==MIN)[1:]&((t[1:]-t[:-1])==MIN)[:-1]
hour=np.array([datetime.fromtimestamp(x/1000).hour for x in t]); inwin=(hour>=8)&(hour<22)
CUT=datetime(2025,10,7,13,50).timestamp()*1000; y1=t<CUT; y2=~y1; BE=1/1.96
def sf(k,nn,p):
    if nn==0: return 1.0
    z=(k-0.5-nn*p)/math.sqrt(nn*p*(1-p)); return 0.5*math.erfc(z/math.sqrt(2))
def roll(x,W):
    cs=np.concatenate([[0],np.cumsum(x)]); m=np.full(len(x),np.nan); m[W-1:]=(cs[W:]-cs[:-W])/W; return m
def ema(x,span):
    a=2/(span+1); out=np.empty_like(x); out[0]=x[0]
    for i in range(1,len(x)): out[i]=a*x[i]+(1-a)*out[i-1]
    return out
ma20=roll(c,20); sd20=np.sqrt(np.maximum(roll(c*c,20)-ma20**2,1e-18)); up_b=ma20+2*sd20; lo_b=ma20-2*sd20
d=np.diff(c,prepend=c[0]); g=roll(np.maximum(d,0),14); ls=roll(np.maximum(-d,0),14); rsi=100-100/(1+g/np.maximum(ls,1e-12))
e5=ema(c,5); e20=ema(c,20); e12=ema(c,12); e26=ema(c,26); macd=e12-e26; sig=ema(macd,9); hist=macd-sig
def rmax(x,W):
    out=np.full(len(x),np.nan); out[W-1:]=swv(x,W).max(axis=1); return out
def rmin(x,W):
    out=np.full(len(x),np.nan); out[W-1:]=swv(x,W).min(axis=1); return out
hh14=rmax(h,14); ll14=rmin(l,14); k=100*(c-ll14)/np.maximum(hh14-ll14,1e-12); k=np.nan_to_num(k,nan=50.0); kd=roll(k,3); kd[:17]=np.nan
hi20=rmax(h,20); lo20=rmin(l,20)
j=idx-1                                  # última vela fechada antes da vela de entrada i
rng=np.maximum(h-l,1e-12); bodyabs=np.abs(c-o); upw=h-np.maximum(o,c); loww=np.minimum(o,c)-l
rules={}
def add(nome,sinal):                      # sinal: +1 compra, -1 venda, 0 nada (calculado em j)
    rules[nome]=sinal
S=np.zeros(n,int)
def at(x): return x[j]
# 1) Bollinger + RSI (reversão clássica)
add("Bollinger+RSI reversão (fora da banda e RSI<30/>70)", np.where((at(c)<at(lo_b))&(at(rsi)<30),1,np.where((at(c)>at(up_b))&(at(rsi)>70),-1,0)))
add("Bollinger+RSI rompimento (fora da banda e RSI>70/<30)", np.where((at(c)>at(up_b))&(at(rsi)>70),1,np.where((at(c)<at(lo_b))&(at(rsi)<30),-1,0)))
add("Bollinger reversão (fechou fora da banda)", np.where(at(c)<at(lo_b),1,np.where(at(c)>at(up_b),-1,0)))
add("RSI extremo reversão (<20 compra, >80 venda)", np.where(at(rsi)<20,1,np.where(at(rsi)>80,-1,0)))
add("RSI extremo continuação (>80 compra, <20 venda)", np.where(at(rsi)>80,1,np.where(at(rsi)<20,-1,0)))
# 2) pin bar (martelo / estrela cadente)
pin_up=(loww[j]>=2*bodyabs[j])&(loww[j]>=0.6*rng[j]); pin_dn=(upw[j]>=2*bodyabs[j])&(upw[j]>=0.6*rng[j])
add("Pin bar reversão (martelo compra / estrela venda)", np.where(pin_up&~pin_dn,1,np.where(pin_dn&~pin_up,-1,0)))
add("Pin bar continuação (contra o pavio)", np.where(pin_up&~pin_dn,-1,np.where(pin_dn&~pin_up,1,0)))
# 3) engolfo
bull=(col[j]>0)&(col[j-1]<0)&(c[j]>=o[j-1])&(o[j]<=c[j-1]); bear=(col[j]<0)&(col[j-1]>0)&(c[j]<=o[j-1])&(o[j]>=c[j-1])
add("Engolfo (de alta compra / de baixa venda)", np.where(bull,1,np.where(bear,-1,0)))
add("Engolfo ao contrário", np.where(bull,-1,np.where(bear,1,0)))
# 4) médias móveis
cross_up=(at(e5)>at(e20))&(e5[j-1]<=e20[j-1]); cross_dn=(at(e5)<at(e20))&(e5[j-1]>=e20[j-1])
add("Cruzamento EMA5/EMA20 (na vela do cruzamento)", np.where(cross_up,1,np.where(cross_dn,-1,0)))
add("Tendência EMA5>EMA20 (segue a tendência)", np.where(at(e5)>at(e20),1,-1))
add("Contra a tendência EMA5/EMA20", np.where(at(e5)>at(e20),-1,1))
# 5) MACD
add("MACD histograma cruza zero", np.where((at(hist)>0)&(hist[j-1]<=0),1,np.where((at(hist)<0)&(hist[j-1]>=0),-1,0)))
# 6) estocástico
add("Estocástico reversão (<20 / >80)", np.where(at(kd)<20,1,np.where(at(kd)>80,-1,0)))
add("Estocástico continuação (>80 compra / <20 venda)", np.where(at(kd)>80,1,np.where(at(kd)<20,-1,0)))
# 7) rompimento de máxima/mínima (Donchian 20)
brk_up=at(c)>np.where(j>=1,hi20[j-1],np.nan); brk_dn=at(c)<np.where(j>=1,lo20[j-1],np.nan)
add("Rompimento de máx/mín de 20 velas (continua)", np.where(brk_up,1,np.where(brk_dn,-1,0)))
add("Rompimento de máx/mín de 20 velas (falso rompimento)", np.where(brk_up,-1,np.where(brk_dn,1,0)))
# 8) três soldados (corpos crescentes) — parente da nossa regra
sold_up=(col[j]>0)&(col[j-1]>0)&(col[j-2]>0)&(bodyabs[j]>bodyabs[j-1])&(bodyabs[j-1]>bodyabs[j-2]); sold_dn=(col[j]<0)&(col[j-1]<0)&(col[j-2]<0)&(bodyabs[j]>bodyabs[j-1])&(bodyabs[j-1]>bodyabs[j-2])
add("Três soldados/corvos com corpos crescentes (continua)", np.where(sold_up,1,np.where(sold_dn,-1,0)))
# referência: nossa regra 1
run=np.zeros(n,int)
for i in range(1,n): run[i]=(run[i-1]+1 if (col[i]!=0 and col[i]==col[i-1]) else (1 if col[i]!=0 else 0))
add("REFERÊNCIA — regra atual: 4+ velas iguais (continua)", np.where(run[j]>=4,col[j],0))
base=contig&inwin&(col!=0)&~np.isnan(rsi[j])&~np.isnan(kd[j])&~np.isnan(hi20[j])
rows=[]
for nome,s in rules.items():
    m=base&(s!=0); r=[]
    for per in (y1,y2):
        mm=m&per; nn=int(mm.sum()); w=int((mm&(col==s)).sum()); r.append((100*w/max(nn,1),nn,sf(w,nn,BE)))
    w=int((m&(col==s)).sum()); nn=int(m.sum()); pl=40*(w*0.96-(nn-w)); rows.append((min(r[0][0],r[1][0]),nome,r,nn/731,pl))
rows.sort(reverse=True)
ntest=len(rows); bonf=0.05/ntest
print(f"{ntest} regras testadas | equilíbrio {100*BE:.2f}% | limiar Bonferroni p<{bonf:.4f}\n")
print(f"{'regra':<60}{'sinais/dia':>11}{'ANO 1 acerto (n)':>22}{'ANO 2 acerto (n)':>22}{'$40 em 2 anos':>16}")
for mn,nome,r,spd,pl in rows:
    flag=" <== passa nos 2 anos" if (r[0][0]>100*BE and r[1][0]>100*BE and r[0][2]<bonf and r[1][2]<0.05) else ""
    print(f"{nome:<60}{spd:>11.1f}{r[0][0]:>13.2f}% ({r[0][1]:>6,}){r[1][0]:>13.2f}% ({r[1][1]:>6,}){pl:>+16,.0f}{flag}")
