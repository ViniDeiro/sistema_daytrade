"""Análise offline (não acessa a Ebinex). Lê dados/candles.json e dados/ciclos.json.
Pergunta: existe alguma condição ANTES da entrada em que o win de primeira acerta mais que o ponto de equilíbrio (51%)?
Rigor: p-valor binomial exato, correção por múltiplos testes, e validação fora da amostra (escolhe no período A, testa no B)."""
import json, math, sys
from collections import defaultdict
from datetime import datetime

BE = 1 / 1.96            # ponto de equilíbrio com payout de 96%
MIN = 60_000
candles = {c['t']: c for c in json.load(open('dados/candles.json'))}
ciclos = json.load(open('dados/ciclos.json'))

def col(c):
    return 'G' if c['c'] > c['o'] else 'R' if c['c'] < c['o'] else 'D'

def binom_sf(k, n, p):      # P(X >= k)
    return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))

def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    ph = k / n; d = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / d
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)

def pct(x): return f"{100*x:.0f}%"

# tercis do corpo da vela de referência (calculados em todo o período)
bodies = sorted(abs(c['c'] - c['o']) for c in candles.values())
T1, T2 = bodies[len(bodies) // 3], bodies[2 * len(bodies) // 3]
def size(c):
    b = abs(c['c'] - c['o']); return 'pequena' if b <= T1 else 'media' if b <= T2 else 'grande'

def rel(c, alvo):
    x = col(c); return 'doji' if x == 'D' else ('igual' if x == alvo else 'oposta')

def build(sid):
    rows = [r for r in ciclos[sid] if r['resultado'][:3] in ('win', 'los')]
    ref = 1 if sid == '4x2' else 0
    out = []
    for i, r in enumerate(rows):
        B = r['t']; alvo = r['alvo']
        f = {'alvo': alvo, 'faixa_horaria': f"{datetime.fromtimestamp(B/1000).hour//6*6:02d}h-{datetime.fromtimestamp(B/1000).hour//6*6+5:02d}h",
             'quarto_hora': f"min {datetime.fromtimestamp(B/1000).minute//15*15:02d}-{datetime.fromtimestamp(B/1000).minute//15*15+14:02d}"}
        f['tam_vela_ref'] = size(candles[B + ref * MIN])
        # contexto: quadrante anterior contíguo
        prev = rows[i - 1] if i > 0 and rows[i - 1]['t'] == B - 5 * MIN else None
        if prev:
            f['ant_win0'] = 'sim' if prev['resultado'] == 'win0' else 'nao'
            f['ant_resultado'] = prev['resultado']
            pc = candles.get(B - 1 * MIN)
            if pc: f['ult_vela_ant_vs_alvo'] = rel(pc, alvo)
            a, z = candles.get(B - 5 * MIN), candles.get(B - 1 * MIN)
            if a and z:
                d = z['c'] - a['o']; f['dir_quadrante_ant_vs_alvo'] = 'igual' if (d > 0) == (alvo == 'G') and d != 0 else 'oposta'
            if i > 1 and rows[i - 2]['t'] == B - 10 * MIN:
                f['ant2_win0'] = ('sim' if rows[i - 2]['resultado'] == 'win0' else 'nao') + '/' + f['ant_win0']
        # sequência de win0 / não-win0 anteriores (contíguos)
        s = 0; j = i - 1
        while j >= 0 and rows[j]['t'] == rows[j + 1]['t'] - 5 * MIN and rows[j]['resultado'] == 'win0': s += 1; j -= 1
        f['seq_win0_ant'] = str(min(s, 3)) + ('+' if s >= 3 else '')
        s = 0; j = i - 1
        while j >= 0 and rows[j]['t'] == rows[j + 1]['t'] - 5 * MIN and rows[j]['resultado'] != 'win0': s += 1; j -= 1
        f['seq_nao_win0_ant'] = str(min(s, 3)) + ('+' if s >= 3 else '')
        # dentro do quadrante, antes da entrada
        if sid == '4x2':
            f['vela1_vs_alvo'] = rel(candles[B], alvo)
            f['vela3_vs_alvo'] = rel(candles[B + 2 * MIN], alvo)
            f['vela1+3_vs_alvo'] = f['vela1_vs_alvo'] + '/' + f['vela3_vs_alvo']
        out.append((r, f))
    return out

def stats(items):
    n = len(items); k = sum(1 for r, f in items if r['resultado'] == 'win0')
    return n, k

summary = {}
def report_baseline(sid, data, label):
    n, k = stats(data)
    res = defaultdict(int)
    for r, f in data: res[r['resultado']] += 1
    lo, hi = wilson(k, n)
    print(f"  {label}: {n} ciclos | win1ª {res['win0']} ({pct(k/n)}, IC95% {pct(lo)}-{pct(hi)}) | G1 {res['win1']} | G2 {res['win2']} | loss {res['loss']} ({pct(res['loss']/n)}) | p(win1ª>51%)={binom_sf(k,n,BE):.2f}")

for sid in ('4x2', 'p23'):
    data = build(sid)
    t0 = data[0][0]['t']; tmax = data[-1][0]['t']
    cut = tmax - 24 * 3600_000
    A = [x for x in data if x[0]['t'] <= cut]       # 24h mais antigas
    Bp = [x for x in data if x[0]['t'] > cut]        # últimas 24h
    print(f"\n==================== {sid} ====================")
    print("Baseline (ponto de equilíbrio do win de 1ª = 51%):")
    report_baseline(sid, Bp, 'últimas 24h')
    report_baseline(sid, A, '24h anteriores')
    report_baseline(sid, data, '48h total')

    # tabela univariada nas 48h
    groups = defaultdict(list)
    for r, f in data:
        for key, v in f.items(): groups[(key, v)].append((r, f))
    tested = [(kv, g) for kv, g in groups.items() if len(g) >= 40]
    ntests = len(tested); bonf = 0.05 / ntests
    print(f"\nCondições testadas (n>=40, 48h): {ntests}  -> limiar de significância corrigido (Bonferroni) p<{bonf:.4f}")
    rows = []
    for (key, v), g in tested:
        n, k = stats(g); rows.append((k / n, n, k, key, v, binom_sf(k, n, BE)))
    rows.sort(reverse=True)
    print("  Top 8 melhores condições (48h, dentro da amostra):")
    for rate, n, k, key, v, p in rows[:8]:
        print(f"    {key}={v:<22} n={n:<4} win1ª={pct(rate)}  p(>51%)={p:.3f} {'<-- sig.' if p<bonf else ''}")
    print("  Top 3 piores:")
    for rate, n, k, key, v, p in rows[-3:]:
        print(f"    {key}={v:<22} n={n:<4} win1ª={pct(rate)}")

    # validação fora da amostra: escolhe no período X (n>=25, win1ª>=55%), mede no período Y
    for (ptrain, ptest, nm) in ((A, Bp, 'escolhe nas 24h antigas -> testa nas últimas 24h'), (Bp, A, 'escolhe nas últimas 24h -> testa nas 24h antigas')):
        g1 = defaultdict(list); g2 = defaultdict(list)
        for r, f in ptrain:
            for key, v in f.items(): g1[(key, v)].append((r, f))
        for r, f in ptest:
            for key, v in f.items(): g2[(key, v)].append((r, f))
        picks = []
        for kv, g in g1.items():
            if len(g) >= 25:
                n, k = stats(g)
                if k / n >= 0.55 and kv in g2 and len(g2[kv]) >= 15: picks.append((k / n, n, kv))
        picks.sort(reverse=True)
        if not picks: print(f"  Validação ({nm}): nenhuma condição passou o filtro"); continue
        tn = tk = 0; kept = 0
        for rate, n, kv in picks:
            n2, k2 = stats(g2[kv]); tn += n2; tk += k2
            if k2 / n2 > BE: kept += 1
        print(f"  Validação ({nm}): {len(picks)} condições com win1ª>=55% no treino; no teste só {kept} ficaram acima de 51%; média no teste = {pct(tk/tn)} (n total {tn}, repetições contam)")
        for rate, n, kv in picks[:4]:
            n2, k2 = stats(g2[kv]); print(f"      {kv[0]}={kv[1]:<20} treino {pct(rate)} (n={n})  ->  teste {pct(k2/n2)} (n={n2})")

    # EV do ciclo completo com as entradas 16/37/84 (exemplo)
    st = [16, 37, 84]; prof = {'win0': 16 * .96, 'win1': 37 * .96 - 16, 'win2': 84 * .96 - 53, 'loss': -sum(st)}
    for label, dd in (('últimas 24h', Bp), ('48h', data)):
        n = len(dd); ev = sum(prof[r['resultado']] for r, f in dd) / n
        tot = sum(prof[r['resultado']] for r, f in dd)
        print(f"  Ciclo completo com entradas 16/37/84, {label}: média {ev:+.2f}$/ciclo, total {tot:+.0f}$ em {n} ciclos (win1ª=+{prof['win0']:.2f}, G1=+{prof['win1']:.2f}, G2=+{prof['win2']:.2f}, loss={prof['loss']:.0f})")

# maior sequência de losses completos e de não-win0
for sid in ('4x2', 'p23'):
    rs = [r['resultado'] for r in ciclos[sid] if r['resultado'][:3] in ('win', 'los')]
    best = cur = 0; bestn = curn = 0
    for x in rs:
        cur = cur + 1 if x == 'loss' else 0; best = max(best, cur)
        curn = curn + 1 if x != 'win0' else 0; bestn = max(bestn, curn)
    print(f"\n{sid}: maior sequência de LOSS completo = {best} | maior sequência sem win de 1ª = {bestn} (48h)")
