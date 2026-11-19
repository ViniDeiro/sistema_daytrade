"""Mesma regra ('>=4 velas iguais -> a próxima repete') em 1 ano de velas M1 PÚBLICAS. Offline. Uso: python3 dados/btc_ano.py BTCUSDT"""
import json, sys, random
from collections import defaultdict
from datetime import datetime
MIN=60_000; BE=1/1.96; PAY=0.96; BANCA=2000
sym=sys.argv[1] if len(sys.argv)>1 else 'BTCUSDT'
d={int(k):v for k,v in json.load(open(f'dados/binance_{sym}_1ano.json')).items()}; ts=sorted(d)
col=lambda t:(d[t][1]>d[t][0])-(d[t][1]<d[t][0])
loc=lambda t:datetime.fromtimestamp(t/1000)
E=[]                                              # (t, s, acertou)
for t in ts:
    if t-MIN not in d: continue
    c=col(t-MIN)
    if c==0: continue
    s=1
    while (t-(s+1)*MIN) in d and col(t-(s+1)*MIN)==c: s+=1
    E.append((t,s,col(t)==c))
print(f"{sym}: {len(ts)} velas | {loc(ts[0]):%d/%m/%Y} a {loc(ts[-1]):%d/%m/%Y}")
def rate(rows): return (100*sum(h for *_,h in rows)/len(rows) if rows else float('nan'), len(rows))
print("\nAcerto da continuação por tamanho da sequência (ano inteiro, 24h):")
for s in range(1,8):
    r=[x for x in E if (x[1]==s if s<7 else x[1]>=7)]; a,n=rate(r); print(f"  s={s}{'+' if s==7 else ' '}: {a:.2f}% ({n})")
for nome,filt in (("24 HORAS",lambda t:True),("08h-22h",lambda t:8<=loc(t).hour<22)):
    rows=[x for x in E if x[1]>=4 and filt(x[0])]
    a,n=rate(rows); days=len({loc(x[0]).date() for x in rows})
    # bootstrap por dia
    dd=defaultdict(lambda:[0,0])
    for t,s,h in rows: k=loc(t).date(); dd[k][0]+=h; dd[k][1]+=1
    ks=list(dd); random.seed(1); b=[]
    for _ in range(2000):
        sm=[dd[random.choice(ks)] for _ in ks]; b.append(sum(x[0] for x in sm)/sum(x[1] for x in sm))
    b.sort()
    print(f"\n=== {sym} | regra >=4 iguais | {nome}: {a:.2f}% em {n} entradas ({n/days:.0f}/dia) | IC95% [{100*b[50]:.2f}, {100*b[1950]:.2f}] | P(real<=51,02%)={sum(x<=BE for x in b)/2000:.3f}")
    mon=defaultdict(lambda:[0,0])
    for t,s,h in rows: k=loc(t).strftime('%Y-%m'); mon[k][0]+=h; mon[k][1]+=1
    print(f"   {'mês':<8}{'acerto':>8}{'entradas':>9}{'$20 (1%)':>11}{'$40 (2%)':>11}")
    pos=0
    for k in sorted(mon):
        h,n=mon[k]; u=h*PAY-(n-h)
        pos+= u>0
        print(f"   {k:<8}{100*h/n:>7.2f}%{n:>9}{20*u:>+11,.0f}{40*u:>+11,.0f}")
    tot=sum(h*PAY-(n-h) for h,n in mon.values())
    print(f"   meses positivos (1%): {pos}/{len(mon)} | total do ano: 1% ${20*tot:+,.0f} | 2% ${40*tot:+,.0f}")
    for st in (20,40):
        eq=BANCA; pk=BANCA; ddm=0; low=BANCA; bust=None
        for t,s,h in sorted(rows):
            if eq<st: bust=t; break
            eq+= st*PAY if h else -st; pk=max(pk,eq); ddm=max(ddm,pk-eq); low=min(low,eq)
        print(f"   banca $2.000 com ${st} fixo: final ${eq:,.0f} | menor ${low:,.0f} | maior queda ${ddm:,.0f} | {'QUEBROU em '+loc(bust).strftime('%d/%m/%Y') if bust else 'não quebrou'}")
