"""Backtest offline (não acessa a Ebinex). Estratégia 'contra o win de primeira':
espera N quadrantes seguidos com win de primeira e entra CONTRA a cor-alvo na vela de entrada;
se perder, sobe um nível do Martingale no quadrante seguinte (máx. 5 entradas). Sem informação do futuro."""
import json, sys
MIN = 60_000
PAYOUT = 0.96
STAKES = [22, 50, 112, 251, 565]
BANCA = 2000
candles = {c['t']: c for c in json.load(open('dados/candles.json'))}
tmax = max(candles)

def col(c): return 'G' if c['c'] > c['o'] else 'R' if c['c'] < c['o'] else 'D'
STRATS = {'4x2': (1, 3), 'p23': (0, 1)}      # (índice da vela-alvo, índice da vela de entrada)

def blocks(strat, hours):
    ref, ent = STRATS[strat]
    last = (tmax // (5 * MIN)) * 5 * MIN
    while last + (ent + 1) * MIN > tmax + MIN: last -= 5 * MIN          # só velas já fechadas
    first = last - int(hours * 3600_000)
    first = (first // (5 * MIN)) * 5 * MIN
    out = []
    for B in range(first, last + 1, 5 * MIN):
        r, e = candles.get(B + ref * MIN), candles.get(B + ent * MIN)
        if r is None or e is None: continue
        out.append((B, col(r), col(e)))
    return out

def simulate(strat, hours, N, stakes=STAKES):
    streak = 0; level = 0; eq = BANCA; peak = BANCA; mdd = 0
    cycles = []; trades = 0; trade_wins = 0; started = 0
    cyc_start = None
    for B, tgt, ent in blocks(strat, hours):
        if tgt == 'D':                          # sem cor-alvo: não há o que operar
            if level == 0: streak = 0
            continue
        win0 = ent == tgt
        opposite = ent != tgt and ent != 'D'
        trade = level > 0 or streak >= N
        if trade:
            if level == 0: started += 1; cyc_start = B
            s = stakes[level]; trades += 1
            if opposite:
                trade_wins += 1; eq += s * PAYOUT
                pl = s * PAYOUT - sum(stakes[:level])
                cycles.append((cyc_start, level + 1, pl)); level = 0; streak = 0
            else:
                eq -= s
                if level == len(stakes) - 1:
                    cycles.append((cyc_start, 0, -sum(stakes))); level = 0; streak = 0
                else: level += 1
            peak = max(peak, eq); mdd = max(mdd, peak - eq)
        else:
            streak = streak + 1 if win0 else 0
    return dict(cycles=cycles, eq=eq, mdd=mdd, trades=trades, trade_wins=trade_wins, open_level=level, started=started)

def fmt(res, hours):
    cy = res['cycles']; n = len(cy)
    by = [sum(1 for _, l, _ in cy if l == k) for k in range(1, 6)]
    loss = sum(1 for _, l, _ in cy if l == 0)
    net = res['eq'] - BANCA
    return n, by, loss, net

for hours in (48, 72):
    print(f"\n================ ÚLTIMAS {hours}h ================")
    for strat, N in (('4x2', 3), ('p23', 4)):
        # taxa incondicional de entrada na cor oposta (todos os quadrantes)
        bl = [b for b in blocks(strat, hours) if b[1] != 'D']
        allopp = sum(1 for _, t, e in bl if e != t and e != 'D'); doji = sum(1 for _, t, e in bl if e == 'D')
        r = simulate(strat, hours, N)
        n, by, loss, net = fmt(r, hours)
        print(f"\n{strat}  | gatilho: {N} wins de 1ª seguidos | {len(bl)} quadrantes, dojis na vela de entrada: {doji}")
        print(f"  Sem gatilho, a vela de entrada fecha na cor OPOSTA em {allopp}/{len(bl)} = {100*allopp/len(bl):.1f}% dos quadrantes (equilíbrio 51,0%)")
        tw = r['trade_wins']; tt = r['trades']
        print(f"  Com gatilho: {tt} entradas, {tw} acertos = {100*tw/tt:.1f}%" if tt else "  Com gatilho: nenhuma entrada")
        print(f"  Ciclos fechados: {n} (win no nível 1..5: {by} | loss de ciclo: {loss}) | ciclo aberto no fim: nível {r['open_level']+1 if r['open_level'] else '-'}")
        print(f"  RESULTADO: {net:+.2f} US$ | banca final {r['eq']:.2f} | maior queda da banca (drawdown): {r['mdd']:.2f}")
        print(f"  Por dia: {net/(hours/24):+.2f} US$/dia, {n/(hours/24):.1f} ciclos/dia")
        # sensibilidade ao gatilho
        row = []
        for k in (0, 1, 2, 3, 4, 5):
            rr = simulate(strat, hours, k); nn, bb, ll, nt = fmt(rr, hours)
            row.append(f"N={k}: {nt:+.0f} (ciclos {nn}, loss {ll}, dd {rr['mdd']:.0f})")
        print("  Sensibilidade ao gatilho ->", " | ".join(row))

# risco teórico por ciclo se cada entrada tivesse chance p de acertar
print("\n---- Risco teórico de ciclo perdido (5 entradas seguidas erradas) ----")
for p in (0.46, 0.50, 0.54, 0.58):
    q = (1 - p) ** 5
    ev = 0
    for k in range(5):
        ev += (1 - p) ** k * p * (STAKES[k] * PAYOUT - sum(STAKES[:k]))
    ev -= q * sum(STAKES)
    print(f"  chance de acerto por entrada {p:.0%}: P(perder o ciclo)={100*q:.1f}% (1 a cada {1/q:.0f} ciclos) | valor esperado por ciclo = {ev:+.2f} US$")
