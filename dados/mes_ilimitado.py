src = open('dados/backtest_mes.py').read().split("H = 30 * 24")[0]
exec(src.replace("print(\"Falhas","pass #"))
BANCA = 10**9                                      # banca "infinita": mede o que o mês teria dado sem quebrar
H = 30*24
t0g = blocks('4x2', H)[0][0]
for strat, N in (('4x2', 3), ('p23', 4)):
    r = sim(strat, H, N); cy = r['cycles']
    by = [sum(1 for _, l, _ in cy if l == k) for k in range(1, 6)]; loss = [c for c in cy if c[1] == 0]
    print(f"\n== {strat} N={N} | banca ilimitada ==")
    print(f"entradas {r['trades']}, acertos {r['tw']} = {100*r['tw']/r['trades']:.1f}% | ciclos {len(cy)} (win 1..5: {by}) | PERDIDOS: {len(loss)}")
    print(f"RESULTADO DO MÊS: {r['eq']-BANCA:+.0f} | maior queda (capital necessário só para atravessar): {r['mdd']:.0f}")
    print("ciclos perdidos em:", ", ".join(datetime.fromtimestamp(t/1000).strftime('%d/%m %Hh%M') for t,_,_ in loss))
    # lucro acumulado por semana
    wk=defaultdict(float)
    for st,l,pl in cy: wk[(st-t0g)//(7*86400_000)]+=pl
    print("lucro por semana:", {f"S{k+1}": round(v) for k,v in sorted(wk.items())})
    # esperado se a chance de acerto fosse a observada sem gatilho
    p = 0.50 if strat=='4x2' else 0.472
    ev = sum((1-p)**k*p*(STAKES[k]*PAYOUT-sum(STAKES[:k])) for k in range(5)) - (1-p)**5*sum(STAKES)
    print(f"valor esperado por ciclo se a chance por entrada fosse {p:.1%} (a observada sem gatilho): {ev:+.2f} -> em {len(cy)} ciclos: {ev*len(cy):+.0f}")
