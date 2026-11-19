"""Simulação de banca (offline): regra '>=4 velas iguais -> repete', $22 fixo, payout 96%, a partir do 1º dia dos 90."""
import json
from collections import defaultdict
from datetime import datetime
MIN=60_000; ST=22; PAY=0.96
cs=sorted(json.load(open('dados/candles.json')),key=lambda c:c['t']); by={c['t']:c for c in cs}; ts=[c['t'] for c in cs]
col=lambda c:1 if c['c']>c['o'] else -1 if c['c']<c['o'] else 0
day=lambda t:datetime.fromtimestamp(t/1000).strftime('%Y-%m-%d')
tr=[]                                              # (t, resultado em $)
for t in ts:
    if t-MIN not in by: continue
    c=col(by[t-MIN])
    if c==0: continue
    s=1
    while (t-(s+1)*MIN) in by and col(by[t-(s+1)*MIN])==c: s+=1
    if s>=4: tr.append((t, ST*PAY if col(by[t])==c else -ST))
def run(bank0, trades):
    eq=bank0; low=bank0; pk=bank0; dd=0; bust=None
    for t,r in trades:
        if eq<ST: bust=t; break
        eq+=r; low=min(low,eq); pk=max(pk,eq); dd=max(dd,pk-eq)
    return eq,low,dd,bust
d=lambda t:datetime.fromtimestamp(t/1000).strftime('%d/%m')
print(f"Entradas em 90 dias: {len(tr)} | sequência máxima de perdas seguidas: ", end='')
m=c=0
for _,r in tr:
    c=c+1 if r<0 else 0; m=max(m,c)
print(f"{m} (= ${m*ST} só nessa sequência)")
print("\nComeçando no 1º dia (09/07), $22 fixo, sem aumentar a entrada:")
for b in (1000,2000,3000,4000):
    eq,low,dd,bust=run(b,tr)
    print(f"  banca inicial ${b}: final ${eq:,.0f} | menor valor da banca ${low:,.0f} | maior queda ${dd:,.0f} ({100*dd/b:.0f}% da inicial) | {'QUEBROU em '+d(bust) if bust else 'não quebrou'}")
# o pior dia como 1º dia
byday=defaultdict(list)
for t,r in tr: byday[day(t)].append((t,r))
worst=min(byday,key=lambda x:sum(r for _,r in byday[x]))
print(f"\nPior dia: {worst}: {sum(r for _,r in byday[worst]):+.0f}  -> com $2.000 a banca fecharia em ${2000+sum(r for _,r in byday[worst]):,.0f}")
# janelas de 30 dias começando em cada dia: quantas quebram?
days=sorted(byday)
print("\nSe a gente tivesse começado em QUALQUER dia e operado 30 dias seguidos (61 inícios possíveis):")
for b in (2000,3000,4000):
    res=[]
    for i in range(0,len(days)-30):
        tt=[x for dd_ in days[i:i+30] for x in byday[dd_]]
        eq,low,dd,bust=run(b,tt); res.append((eq-b,bust is not None,low))
    pos=sum(1 for r in res if r[0]>0); bu=sum(1 for r in res if r[1])
    print(f"  banca ${b}: {len(res)} janelas | terminaram no positivo {pos} | quebraram {bu} | pior resultado de 30 dias {min(r[0] for r in res):+,.0f} | melhor {max(r[0] for r in res):+,.0f} | menor banca já vista ${min(r[2] for r in res):,.0f}")
