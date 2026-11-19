"""Indicadores como filtro da regra 1 e sozinhos (offline, IDX, M1, 2 anos, 08–22h, $40, empate devolvido). Cortes definidos no ano 1; teste no ano 2."""
import numpy as np, json, math
from datetime import datetime
raw=json.load(open('dados/candles.json')); raw.sort(key=lambda c:c['t'])
t=np.array([x['t'] for x in raw]); o=np.array([x['o'] for x in raw]); c=np.array([x['c'] for x in raw]); n=len(t); MIN=60000
col=np.sign(c-o).astype(int); contig=np.zeros(n,bool); contig[1:]=(t[1:]-t[:-1])==MIN
run=np.zeros(n,int)
for i in range(1,n): run[i]=(run[i-1]+1 if (col[i]!=0 and contig[i] and col[i]==col[i-1]) else (1 if col[i]!=0 else 0))
idx=np.arange(n); pr=run[idx-1]
hour=np.array([datetime.fromtimestamp(x/1000).hour for x in t]); inwin=(hour>=8)&(hour<22)
CUT=datetime(2025,10,7,13,50).timestamp()*1000; y1=t<CUT; y2=~y1; BE=1/1.96
def roll(x,W):
    cs=np.concatenate([[0],np.cumsum(x)]); m=np.full(len(x),np.nan); m[W-1:]=(cs[W:]-cs[:-W])/W; return m
ma=roll(c,20); m2=roll(c*c,20); sd=np.sqrt(np.maximum(m2-ma*ma,1e-18))
pb=(c-(ma-2*sd))/(4*sd)                         # %B: 0 = banda inferior, 1 = banda superior
bw=4*sd/ma                                      # largura relativa das bandas (volatilidade)
d=np.diff(c,prepend=c[0]); g=roll(np.maximum(d,0),14); l=roll(np.maximum(-d,0),14); rsi=100-100/(1+g/np.maximum(l,1e-12))
last=idx-1; up=(col[last]>0)
pb_al=np.where(up,pb[last],1-pb[last]); rsi_al=np.where(up,rsi[last],100-rsi[last]); bw_l=bw[last]
el=contig&(col[last]!=0)&~np.isnan(pb[last])&~np.isnan(rsi[last])
r1=el&(pr>=4)&inwin&(col!=0); w1=(col==col[last]); w1r=(col==-col[last])
def sf(k,nn,p):
    z=(k-0.5-nn*p)/math.sqrt(nn*p*(1-p)); return 0.5*math.erfc(z/math.sqrt(2))
def tabela(nome,f,cuts,labels):
    cat=np.digitize(f,cuts); print(f"\n{nome}")
    print(f"   {'faixa':<30}{'ANO 1':>22}{'ANO 2':>22}")
    for q in range(len(cuts)+1):
        r=[]
        for per in (y1,y2):
            m=r1&per&(cat==q); nn=int(m.sum()); k=int((m&w1).sum()); r.append(f"{100*k/max(nn,1):.1f}% ({nn:,})")
        print(f"   {labels[q]:<30}{r[0]:>22}{r[1]:>22}")
print("REGRA 1 (4+ iguais, a favor) filtrada por indicadores calculados na última vela fechada")
tabela("1) Bollinger %B, na direção da sequência (1,0 = encostada na banda; >1 = fora da banda)",pb_al,[0.5,0.8,1.0,1.2],["até 0,5 (longe da banda)","0,5 a 0,8","0,8 a 1,0 (perto da banda)","1,0 a 1,2 (acima da banda)","acima de 1,2 (muito esticado)"])
qs=np.nanpercentile(bw_l[r1&y1],[25,50,75]); tabela(f"2) Largura das bandas = volatilidade (quartis do ano 1: {np.round(100*qs,3)}%)",bw_l,qs,["Q1: bandas estreitas","Q2","Q3","Q4: bandas largas"])
tabela("3) RSI(14) na direção da sequência (100 = muito esticado)",rsi_al,[60,70,80,90],["abaixo de 60","60 a 70","70 a 80","80 a 90","acima de 90"])
print("\nBOLLINGER SOZINHO (sem a regra 1): o que acontece na vela seguinte quando a última fechou FORA da banda?")
for nome,mask in (("fechou acima da banda superior",pb[last]>1.0),("fechou abaixo da banda inferior",pb[last]<0.0)):
    for lab,w in (("continua na mesma direção",None),):
        r=[]
        for per in (y1,y2):
            m=el&inwin&(col!=0)&mask&per; dirn=np.where(pb[last]>1,1,-1); k=int((m&(col==dirn)).sum()); nn=int(m.sum()); r.append(f"{100*k/nn:.1f}% ({nn:,})")
        print(f"   {nome}: continua {r[0]} (ano 1) | {r[1]} (ano 2)   [reversão = 100% − continuação − doji]")
