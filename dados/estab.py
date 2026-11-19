import math
src = open('dados/backtest.py').read().split('for hours in (48, 72)')[0]
exec(src)
def sf(k,n,p): return sum(math.comb(n,i)*p**i*(1-p)**(n-i) for i in range(k,n+1))
for strat,N in (('4x2',3),('p23',4)):
    print(f"\n{strat} gatilho N={N} — por bloco de 24h (do mais antigo ao mais recente), janela 72h")
    bl = blocks(strat,72); t0 = bl[0][0]
    for d in range(3):
        lo, hi = t0 + d*24*3600_000, t0 + (d+1)*24*3600_000
        # roda a simulação inteira e separa as entradas por dia
        streak=0; level=0; n=w=0; cyc=[]; start=None
        for B,tgt,ent in bl:
            if tgt=='D':
                if level==0: streak=0
                continue
            win0 = ent==tgt; opp = ent!=tgt and ent!='D'
            if level>0 or streak>=N:
                if level==0: start=B
                if lo<=B<hi: n+=1; w+=opp
                if opp: cyc.append((start,level+1)); level=0; streak=0
                elif level==4: cyc.append((start,0)); level=0; streak=0
                else: level+=1
            else: streak = streak+1 if win0 else 0
        dc=[l for s,l in cyc if lo<=s<hi]
        print(f"  dia {d+1}: {n} entradas, acerto {100*w/n:.0f}% ({w}/{n}) | ciclos {len(dc)}, loss de ciclo {sum(1 for l in dc if l==0)}")
    r=simulate(strat,72,N); n=r['trades']; k=r['trade_wins']
    print(f"  total: acerto {k}/{n}={100*k/n:.1f}% | p(acertar tanto por acaso se a chance real fosse 51%)={sf(k,n,0.51):.2f}")
    ncy=len(r['cycles']); pl=(1-(1-0.508)**5)
    for p in (0.48,0.50,0.51):
        q=(1-p)**5; print(f"  se a chance real por entrada fosse {p:.0%}: P(0 ciclos perdidos em {ncy} ciclos) = {(1-q)**ncy:.0%}")
