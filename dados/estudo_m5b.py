"""Estudo M5 (parte 2, offline): (1) sequência de velas iguais em M5; (2) busca só no período recente; (3) gatilho M1 (4+ iguais) com expiração de 5 min."""
import json, math
import numpy as np
from datetime import datetime
src=open('dados/estudo_m5.py').read().split("def sf(")[0]
exec(src.replace('print(f"Velas M5','pass #'))
PAYV=0.96; BEq=1/(1+PAYV)
def sf(k,nn,p):
    if nn==0: return 1.0
    z=(k-0.5-nn*p)/math.sqrt(nn*p*(1-p)); return 0.5*math.erfc(z/math.sqrt(2))
print("\n=== (1) M5: depois de s velas iguais seguidas, a próxima repete? (equilíbrio 51,02%)")
print(f"{'s':>3}{'ANO 1':>26}{'ANO 2':>26}")
for s in range(1,9):
    row=[]
    for per in (isA,isB):
        m=valid1&per&(np.minimum(pr,8)==s) if s<8 else valid1&per&(pr>=8)
        dec=m&(col!=0); k=int((dec&(col==col[idx-1])).sum()); nn=int(dec.sum()); row.append(f"{100*k/nn:.2f}% ({nn})  p={sf(k,nn,BEq):.2f}")
    print(f"{s:>3}{row[0]:>26}{row[1]:>26}")
# --- (2) busca no período recente: descoberta jan-jun/2026, teste jul-out/2026
dA=datetime(2026,1,1).timestamp()*1000; dB=datetime(2026,7,1).timestamp()*1000
isR1=(T>=dA)&(T<dB); isR2=T>=dB
rules=[]
for name,(mask,cat) in cats.items():
    for cid in np.unique(cat[mask]):
        sel=mask&(cat==cid); a=sel&isR1&(col!=0); G=int((a&(col>0)).sum()); R=int((a&(col<0)).sum()); nA=G+R
        if nA<800: continue
        side=1 if G>=R else -1; kA=G if side>0 else R
        b_=sel&isR2&(col!=0); nB=int(b_.sum()); kB=int((b_&(col==side)).sum())
        rules.append((kA/nA,nA,sf(kA,nA,BEq),kB/nB if nB else 0,nB,kB,name,int(cid),side))
rules.sort(reverse=True); nt=len(rules); bonf=0.05/nt
print(f"\n=== (2) Busca só no período recente: descoberta jan–jun/2026, teste jul–out/2026 ({nt} regras, Bonferroni p<{bonf:.1e})")
for r in rules[:8]: print(f"   {r[6]:<28} id={r[7]:>3} lado={'G' if r[8]>0 else 'R'}: descoberta {100*r[0]:.2f}% ({r[1]}) p={r[2]:.4f} -> TESTE {100*r[3]:.2f}% ({r[4]})")
sig=[r for r in rules if r[2]<bonf and r[0]>BEq]
if sig:
    kB=sum(r[5] for r in sig); nB=sum(r[4] for r in sig); print(f"   passaram no Bonferroni: {len(sig)} | no teste (jul–out): {100*kB/nB:.2f}% em {nB} entradas")
else: print("   nenhuma passou no Bonferroni")
# --- (3) gatilho M1 (>=4 iguais) com expiração de 5 min: entra na abertura da vela M1 seguinte; vence se o fechamento 5 min depois está na direção da sequência
col1=np.sign(c-o).astype(int); n1=len(t)
contig1=np.zeros(n1,bool); contig1[1:]=(t[1:]-t[:-1])==MIN
run1=np.zeros(n1,int)
for i in range(1,n1): run1[i]=(run1[i-1]+1 if (col1[i]!=0 and contig1[i] and col1[i]==col1[i-1]) else (1 if col1[i]!=0 else 0))
hr1=np.array([datetime.fromtimestamp(x/1000).hour for x in t])
ok5=np.zeros(n1,bool); ok5[:-5]=(t[5:]-t[:-5])==5*MIN          # as 5 velas seguintes existem
res={}
for per_name,per in (("ano 1",t<cut),("ano 2",t>=cut)):
    for k in (4,5,6):
        m=(run1>=k)&ok5&per&(hr1>=8)&(hr1<22)
        ii=np.where(m)[0]; ii=ii[ii+5<n1]
        entry=o[ii+1]; exitp=c[ii+5]; d=col1[ii]
        move=np.sign(exitp-entry)*d
        dec=move!=0; wins=int((move[dec]>0).sum()); nn=int(dec.sum())
        res[(per_name,k)]=(wins,nn)
print("\n=== (3) Gatilho M1 (k+ velas M1 iguais) com ENTRADA na abertura da vela seguinte e EXPIRAÇÃO de 5 minutos (08–22h)")
for k in (4,5,6):
    out=[]
    for pn in ("ano 1","ano 2"): w,nn=res[(pn,k)]; out.append(f"{pn}: {100*w/nn:.2f}% ({nn:,}) p={sf(w,nn,BEq):.2f}")
    print(f"   k={k}: "+" | ".join(out))
print("   (para comparar: a mesma regra com expiração de 1 minuto: ano 1 54,7%, ano 2 53,8%)")
