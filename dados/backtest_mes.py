"""Backtest de 1 mês (offline). Mesma regra do backtest.py, com datas, curva da banca e checagem de quebra."""
import json, math
from datetime import datetime
from collections import defaultdict
src = open('dados/backtest.py').read().split('def simulate')[0]
exec(src)                                       # reaproveita candles, col, blocks, STRATS, constantes

# --- falhas na sequência de velas
ts = sorted(candles)
gaps = [(ts[i], ts[i+1]) for i in range(len(ts)-1) if ts[i+1]-ts[i] != MIN]
print("Falhas na sequência de velas:", [(datetime.fromtimestamp(a/1000).strftime('%d/%m %H:%M'), (b-a)//MIN-1) for a, b in gaps], "(velas faltando)")

def sim(strat, hours, N):
    streak = 0; level = 0; eq = BANCA; peak = BANCA; mdd = 0; low = BANCA
    cycles = []; trades = tw = 0; start = None; bust = None
    curve = []                                   # (t, banca)
    for B, tgt, ent in blocks(strat, hours):
        if tgt == 'D':
            if level == 0: streak = 0
            continue
        win0 = ent == tgt; opp = ent != tgt and ent != 'D'
        if level > 0 or streak >= N:
            s = STAKES[level]
            if eq < s: bust = B; break           # sem banca para a próxima entrada
            if level == 0: start = B
            trades += 1
            if opp:
                tw += 1; eq += s * PAYOUT
                cycles.append((start, level + 1, s * PAYOUT - sum(STAKES[:level]))); level = 0; streak = 0
            else:
                eq -= s
                if level == len(STAKES) - 1: cycles.append((start, 0, -sum(STAKES))); level = 0; streak = 0
                else: level += 1
            peak = max(peak, eq); mdd = max(mdd, peak - eq); low = min(low, eq)
            curve.append((B, eq))
        else:
            streak = streak + 1 if win0 else 0
    return dict(cycles=cycles, eq=eq, mdd=mdd, low=low, trades=trades, tw=tw, curve=curve, bust=bust, open=level)

H = 30 * 24
d = lambda t: datetime.fromtimestamp(t/1000).strftime('%d/%m %H:%M')
print(f"Período: {d(min(candles))} -> {d(max(candles))}  (janela do backtest: {H}h)")
for strat, N in (('4x2', 3), ('p23', 4)):
    bl = [b for b in blocks(strat, H) if b[1] != 'D']
    opp = sum(1 for _, t, e in bl if e != t and e != 'D')
    r = sim(strat, H, N); cy = r['cycles']
    by = [sum(1 for _, l, _ in cy if l == k) for k in range(1, 6)]; loss = [c for c in cy if c[1] == 0]
    print(f"\n=========== {strat} | gatilho: {N} wins de 1ª seguidos ===========")
    print(f"Quadrantes: {len(bl)} | sem gatilho, entrada na cor oposta acerta {opp}/{len(bl)} = {100*opp/len(bl):.1f}%")
    print(f"Com gatilho: {r['trades']} entradas, {r['tw']} acertos = {100*r['tw']/r['trades']:.1f}% (equilíbrio 51,0%)")
    print(f"Ciclos fechados: {len(cy)} | win nível 1..5: {by} | ciclos PERDIDOS: {len(loss)} | ciclo aberto no fim: {'nível '+str(r['open']+1) if r['open'] else 'não'}")
    for t, _, pl in loss: print(f"   ciclo perdido iniciado em {d(t)}  ({pl:+.0f})")
    if r['bust']: print(f"   !!! BANCA INSUFICIENTE para a próxima entrada em {d(r['bust'])} — a simulação para aqui")
    print(f"BANCA FINAL: {r['eq']:.2f}  (resultado {r['eq']-BANCA:+.2f}) | menor banca: {r['low']:.2f} | maior queda: {r['mdd']:.2f} ({100*r['mdd']/BANCA:.0f}% da banca inicial)")
    # por semana (a partir do início da janela)
    t0 = blocks(strat, H)[0][0]
    wk = defaultdict(lambda: [0, 0, 0.0, 0, 0])      # ciclos, perdidos, pl, entradas, acertos
    for st, l, pl in cy:
        w = (st - t0) // (7 * 86400_000); wk[w][0] += 1; wk[w][1] += (l == 0); wk[w][2] += pl
    print("Por semana (ciclos / perdidos / resultado):", " | ".join(f"S{w+1}: {v[0]} / {v[1]} / {v[2]:+.0f}" for w, v in sorted(wk.items())))
    # banca ao fim de cada dia
    day = {}
    for t, eq in r['curve']: day[(t - t0) // 86400_000] = eq
    pr = BANCA; line = []
    for dd in range(0, 30):
        if dd in day: pr = day[dd]
        line.append(f"{pr:.0f}")
    print("Banca no fim de cada dia:", " ".join(line))
    # dias no vermelho / meta
    pdays = defaultdict(float)
    for st, l, pl in cy: pdays[(st - t0) // 86400_000] += pl
    vals = [pdays.get(i, 0.0) for i in range(30)]
    print(f"Resultado diário: média {sum(vals)/30:+.1f} | melhor {max(vals):+.0f} | pior {min(vals):+.0f} | dias >= +$200: {sum(v>=200 for v in vals)} de 30 | dias negativos: {sum(v<0 for v in vals)}")
    # sensibilidade ao gatilho
    row = []
    for k in range(0, 8):
        rr = sim(strat, H, k); nl = sum(1 for c in rr['cycles'] if c[1] == 0)
        row.append(f"N={k}: {rr['eq']-BANCA:+.0f} ({len(rr['cycles'])} ciclos, {nl} perdidos, queda máx {rr['mdd']:.0f}{', QUEBROU' if rr['bust'] else ''})")
    print("Sensibilidade ao gatilho:\n  " + "\n  ".join(row))
