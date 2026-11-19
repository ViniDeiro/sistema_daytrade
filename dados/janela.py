"""Backtest (offline) só no horário 08h-22h (horário local), 90 dias, regra '>=4 velas iguais -> repete', payout 96%.
Parte 1: intervalos entre sinais. Parte 2: banca $2.000 com entrada de 1% a 5% (valor fixo, % da banca inicial) e a variante % da banca atual."""
import json, statistics
from collections import defaultdict
from datetime import datetime
MIN=60_000; PAY=0.96; BANCA=2000
cs=sorted(json.load(open('dados/candles.json')),key=lambda c:c['t']); by={c['t']:c for c in cs}; ts=[c['t'] for c in cs]
col=lambda c:1 if c['c']>c['o'] else -1 if c['c']<c['o'] else 0
hr=lambda t:datetime.fromtimestamp(t/1000).hour
day=lambda t:datetime.fromtimestamp(t/1000).strftime('%Y-%m-%d')
t0,t1=ts[0],ts[-1]; P=(t1-t0)/3; per=lambda t:min(2,int((t-t0)//P))
names=[f"{datetime.fromtimestamp((t0+P*i)/1000):%d/%m}-{datetime.fromtimestamp((t0+P*(i+1))/1000):%d/%m}" for i in range(3)]
E_=[]                                  # entradas: (t, streak, acertou)
for t in ts:
    if t-MIN not in by or not (8<=hr(t)<22): continue
    c=col(by[t-MIN])
    if c==0: continue
    s=1
    while (t-(s+1)*MIN) in by and col(by[t-(s+1)*MIN])==c: s+=1
    if s>=4: E_.append((t,s,col(by[t])==c))
ndays=len({day(t) for t in ts if 8<=hr(t)<22})
print(f"Horário 08h-22h | {ndays} dias | entradas: {len(E_)} ({len(E_)/ndays:.0f}/dia) | acerto {100*sum(h for *_,h in E_)/len(E_):.2f}%")
# --- Parte 1: intervalos
def gaps(lst):
    g=[(b-a)//MIN for a,b in zip(lst,lst[1:]) if day(a)==day(b)]   # só dentro do mesmo dia
    g.sort(); q=lambda p:g[int(p*(len(g)-1))]
    return f"mín {g[0]} min | mediana {q(.5)} | 75% até {q(.75)} | 90% até {q(.9)} | 99% até {q(.99)} | máx {g[-1]} min"
print("\n1) Intervalo entre ENTRADAS consecutivas (toda vela com >=4 iguais conta):\n   "+gaps([t for t,*_ in E_]))
new=[t for t,s,_ in E_ if s==4]
print(f"2) Intervalo entre NOVOS SINAIS (só quando a sequência chega a 4; {len(new)} sinais, {len(new)/ndays:.0f}/dia):\n   "+gaps(new))
long=[(b-a)//MIN for a,b in zip(new,new[1:]) if day(a)==day(b)]
print(f"   sinais com menos de 5 min do anterior: {100*sum(x<5 for x in long)/len(long):.0f}% | com mais de 30 min sem sinal: {100*sum(x>30 for x in long)/len(long):.1f}% dos intervalos")
byday=defaultdict(int)
for t in new: byday[day(t)]+=1
v=sorted(byday.values()); print(f"   novos sinais por dia (08-22h): mín {v[0]} | mediana {v[len(v)//2]} | máx {v[-1]}")
# --- Parte 2
def sim(pct, mode):
    eq=BANCA; low=BANCA; pk=BANCA; dd=0; bust=None; mon=[0.0,0.0,0.0]; dpl=defaultdict(float)
    for t,s,h in E_:
        st = BANCA*pct/100 if mode=='fixo' else eq*pct/100
        if eq<st or eq<1: bust=t; break
        r=st*PAY if h else -st; eq+=r; mon[per(t)]+=r; dpl[day(t)]+=r
        low=min(low,eq); pk=max(pk,eq); dd=max(dd,pk-eq)
    return eq,low,dd,bust,mon,dpl
for mode,titulo in (('fixo','VALOR FIXO (% da banca inicial de $2.000; a entrada não muda)'),('comp','% DA BANCA ATUAL (a entrada cresce/encolhe com a banca)')):
    print(f"\n3) {titulo}")
    print(f"{'%':<4}{'entrada':>8} | "+" | ".join(f"{n:>11}" for n in names)+f" | {'TOTAL':>8} | {'banca final':>11} | {'menor banca':>11} | {'maior queda':>11} | {'pior dia':>8} | quebrou?")
    for pct in (1,2,3,4,5):
        eq,low,dd,bust,mon,dpl=sim(pct,mode)
        print(f"{pct:<4}{('$%d'%(BANCA*pct/100) if mode=='fixo' else 'var.'):>8} | "+" | ".join(f"{m:>+11,.0f}" for m in mon)+f" | {sum(mon):>+8,.0f} | {eq:>11,.0f} | {low:>11,.0f} | {dd:>11,.0f} | {min(dpl.values()):>+8,.0f} | {'SIM em '+datetime.fromtimestamp(bust/1000).strftime('%d/%m') if bust else 'não'}")
