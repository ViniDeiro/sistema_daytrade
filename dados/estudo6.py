"""Estudo 6 (offline): a regra de continuação nos 3 meses. Os 2 meses mais antigos NÃO foram usados para descobrir a regra."""
import json, math, random
from collections import defaultdict
from datetime import datetime
MIN=60_000; BE=1/1.96; ST=22; PAY=0.96
cs=sorted(json.load(open('dados/candles.json')),key=lambda c:c['t']); by={c['t']:c for c in cs}; ts=[c['t'] for c in cs]
col=lambda c:1 if c['c']>c['o'] else -1 if c['c']<c['o'] else 0
day=lambda t:datetime.fromtimestamp(t/1000).strftime('%Y-%m-%d')
t0,t1=ts[0],ts[-1]; P=(t1-t0)/3
per=lambda t:min(2,int((t-t0)//P))
names=[f"{datetime.fromtimestamp((t0+P*i)/1000):%d/%m} a {datetime.fromtimestamp((t0+P*(i+1))/1000):%d/%m}" for i in range(3)]
S=[]
for t in ts:
    if t-MIN not in by: continue
    c=col(by[t-MIN])
    if c==0: continue
    s=1
    while (t-(s+1)*MIN) in by and col(by[t-(s+1)*MIN])==c: s+=1
    S.append((t,s,col(by[t])==c))
random.seed(3)
def ci(rows):
    d=defaultdict(lambda:[0,0])
    for t,s,h in rows: d[day(t)][0]+=h; d[day(t)][1]+=1
    ks=list(d); b=[]
    for _ in range(3000):
        sm=[d[random.choice(ks)] for _ in ks]; b.append(sum(x[0] for x in sm)/sum(x[1] for x in sm))
    b.sort(); return b[75],b[2925],sum(x<=BE for x in b)/len(b)
print(f"Velas: {len(cs)} | de {datetime.fromtimestamp(t0/1000):%d/%m/%Y} a {datetime.fromtimestamp(t1/1000):%d/%m/%Y}")
for label,f in (("s=1 (1 vela)",lambda s:s==1),("s=2",lambda s:s==2),("s=3",lambda s:s==3),("EXATAMENTE 4",lambda s:s==4),(">=4 iguais",lambda s:s>=4),(">=5 iguais",lambda s:s>=5)):
    print(f"\n{label}")
    for p in range(3):
        rows=[r for r in S if per(r[0])==p and f(r[1])]; n=len(rows); h=sum(r[2] for r in rows)
        lo,hi,pb=ci(rows)
        days=len({day(r[0]) for r in rows}); pl=h*ST*PAY-(n-h)*ST
        print(f"  {names[p]}{'  <-- mês em que a regra foi descoberta' if p==2 else ''}: {100*h/n:.2f}% ({n}) IC95% [{100*lo:.1f}, {100*hi:.1f}] P(<=51,02%)={pb:.3f} | $22 fixo: {pl:+.0f} ({pl/days:+.0f}/dia)")
rows=[r for r in S if r[1]>=4]
n=len(rows); h=sum(r[2] for r in rows); lo,hi,pb=ci(rows)
print(f"\n>=4 iguais nos 90 dias: {100*h/n:.2f}% ({n}) IC95% [{100*lo:.1f}, {100*hi:.1f}] P(<=51,02%)={pb:.3f}")
old=[r for r in rows if per(r[0])<2]; h2=sum(r[2] for r in old); lo,hi,pb=ci(old)
print(f">=4 iguais SÓ nos 2 meses mais antigos (teste limpo): {100*h2/len(old):.2f}% ({len(old)}) IC95% [{100*lo:.1f}, {100*hi:.1f}] P(<=51,02%)={pb:.3f}")
# semanas e dias
wk=defaultdict(lambda:[0,0]); dy=defaultdict(lambda:[0,0])
for t,s,hh in rows: w=(t-t0)//(7*86400_000); wk[w][0]+=hh; wk[w][1]+=1; dy[day(t)][0]+=hh; dy[day(t)][1]+=1
ww=[100*a/b for a,b in wk.values() if b>200]
print(f"Semanas: {len(ww)} completas | acerto semanal: min {min(ww):.1f}% | máx {max(ww):.1f}% | semanas acima de 51,02%: {sum(x>BE*100 for x in ww)}/{len(ww)}")
pls=[a*ST*PAY-(b-a)*ST for a,b in dy.values()]
print(f"Dias: {len(pls)} | positivos {sum(p>0 for p in pls)} | pior dia {min(pls):+.0f} | melhor {max(pls):+.0f} | média {sum(pls)/len(pls):+.0f}")
eq=pk=dd=0
for t,s,hh in sorted(rows): eq+=ST*PAY if hh else -ST; pk=max(pk,eq); dd=max(dd,pk-eq)
print(f"90 dias, $22 fixo: resultado {eq:+.0f} | maior queda {dd:.0f}")
