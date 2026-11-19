"""Teste focado na tese: 'depois de N wins de 1ª seguidos, o próximo não é win de 1ª'."""
import json, math
MIN=60_000
ciclos=json.load(open('dados/ciclos.json'))
def cdf(k,n,p): return sum(math.comb(n,i)*p**i*(1-p)**(n-i) for i in range(0,k+1))   # P(X<=k)
for sid in ('4x2','p23'):
    rows=[r for r in ciclos[sid] if r['resultado'][:3] in('win','los')]
    cut=rows[-1]['t']-24*3600_000
    print(f"\n{sid}")
    for N in (1,2,3,4):
        for nm,sel in (('48h',lambda r:True),('antigas',lambda r:r['t']<=cut),('últimas24h',lambda r:r['t']>cut)):
            n=k=0
            for i in range(N,len(rows)):
                if not sel(rows[i]): continue
                if all(rows[i-j]['t']==rows[i-j+1]['t']-5*MIN and rows[i-j]['resultado']=='win0' for j in range(1,N+1)) if True else False:
                    n+=1; k+= rows[i]['resultado']=='win0'
            if n: print(f"  após >={N} win1ª seguidos [{nm:<10}]: próximo win1ª {k}/{n} = {100*k/n:.0f}%", end='')
            if n and nm=='48h':
                base=sum(r['resultado']=='win0' for r in rows)/len(rows)
                print(f"  | p(ser tão baixo por acaso, base {100*base:.0f}%)={cdf(k,n,base):.3f}", end='')
            if n: print()
