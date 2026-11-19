"""Estudo 5 (offline): filtro de tendência. Regra base: após >=4 velas iguais, apostar que a próxima repete.
Tendência = sinal de (fechamento anterior - fechamento N velas atrás). 'A favor' = cor da sequência igual à tendência."""
import json, math
from datetime import datetime
MIN=60_000; BE=1/1.96
cs=sorted(json.load(open('dados/candles.json')),key=lambda c:c['t']); by={c['t']:c for c in cs}; ts=[c['t'] for c in cs]
cut=ts[0]+(ts[-1]-ts[0])//2
col=lambda c:1 if c['c']>c['o'] else -1 if c['c']<c['o'] else 0
def sf(k,n,p):
    z=(k-0.5-n*p)/math.sqrt(n*p*(1-p)); return 0.5*math.erfc(z/math.sqrt(2))
def run(N):
    r={('a','tr'):[0,0],('a','te'):[0,0],('c','tr'):[0,0],('c','te'):[0,0]}
    for t in ts:
        if t-MIN not in by or t-(N+1)*MIN not in by: continue
        c=col(by[t-MIN])
        if c==0: continue
        s=1
        while (t-(s+1)*MIN) in by and col(by[t-(s+1)*MIN])==c: s+=1
        if s<4: continue
        tr=by[t-MIN]['c']-by[t-(N+1)*MIN]['c']
        if tr==0: continue
        side='a' if (tr>0)==(c>0) else 'c'; per='tr' if t<cut else 'te'
        r[(side,per)][0]+= col(by[t])==c; r[(side,per)][1]+=1
    return r
print("Regra '>=4 velas iguais'. Acerto% (n) — treino | teste. Equilíbrio 51,02%\n")
print(f"{'tendência (velas)':<20}{'A FAVOR da tendência':<40}{'CONTRA a tendência':<40}")
for N in (15,30,60,120,240,480):
    r=run(N); f=lambda k,p:(lambda h,n:f"{100*h/n:.1f}% ({n})")(*r[(k,p)])
    print(f"{N:<20}{f('a','tr')+' | '+f('a','te'):<40}{f('c','tr')+' | '+f('c','te'):<40}")
