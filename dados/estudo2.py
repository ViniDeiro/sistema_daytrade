"""Estudo 2 (offline): o que está por trás do resultado de 'cores1'? Estabilidade por semana e por tamanho da vela anterior."""
import json, math
from collections import defaultdict
from datetime import datetime
MIN = 60_000; BE = 1 / 1.96
cs = sorted(json.load(open('dados/candles.json')), key=lambda c: c['t'])
by = {c['t']: c for c in cs}
col = lambda c: 'G' if c['c'] > c['o'] else 'R' if c['c'] < c['o'] else 'D'
ts = [c['t'] for c in cs]; t0 = ts[0]; cut = t0 + (ts[-1] - t0) // 2

def sf(k, n, p):
    z = (k - 0.5 - n*p) / math.sqrt(n*p*(1-p)); return 0.5 * math.erfc(z / math.sqrt(2))
def roi(h): return h * 1.96 - 1

# 1) direção da regra no treino: após G aposta no quê?
tr = defaultdict(lambda: [0, 0, 0])
for t in ts:
    p = by.get(t - MIN)
    if p is None or t >= cut: continue
    o = col(by[t]); tr[col(p)][0 if o == 'G' else 1 if o == 'R' else 2] += 1
print("Treino — depois de uma vela [cor] a próxima é (G/R/doji):")
for k, (g, r, x) in sorted(tr.items()): n = g + r + x; print(f"  após {k}: G {100*g/n:.1f}% | R {100*r/n:.1f}% | doji {100*x/n:.1f}%  (n={n})")

# regra: apostar na cor OPOSTA à da vela anterior (reversão) — checa por semana no mês inteiro
opp = {'G': 'R', 'R': 'G'}
wk = defaultdict(lambda: [0, 0])
allk = alln = 0
for t in ts:
    p = by.get(t - MIN)
    if p is None or col(p) == 'D': continue
    hit = col(by[t]) == opp[col(p)]; w = (t - t0) // (7 * 86400_000)
    wk[w][0] += hit; wk[w][1] += 1; allk += hit; alln += 1
print("\nRegra 'apostar na cor oposta à da vela anterior' — por semana (mão fixa, payout 96%):")
for w, (k, n) in sorted(wk.items()): print(f"  semana {w+1}: {k}/{n} = {100*k/n:.2f}%  ROI {100*roi(k/n):+.1f}%")
print(f"  MÊS: {allk}/{alln} = {100*allk/alln:.2f}%  ROI {100*roi(allk/alln):+.1f}%  (p vs 51,02% = {sf(allk, alln, BE):.4f})")

# 2) por tamanho da vela anterior (quintis calculados só no treino)
bodies = sorted(abs(by[t]['c'] - by[t]['o']) for t in ts if t < cut and col(by[t]) != 'D')
q = [bodies[int(len(bodies) * i / 5)] for i in range(1, 5)]
def bucket(b): return sum(b > x for x in q)
print("\nPor tamanho da vela anterior (quintil 0 = menor ... 4 = maior; limiares do treino):")
for per, lab in ((lambda t: t < cut, 'TREINO'), (lambda t: t >= cut, 'TESTE')):
    d = defaultdict(lambda: [0, 0])
    for t in ts:
        p = by.get(t - MIN)
        if p is None or col(p) == 'D' or not per(t): continue
        b = bucket(abs(p['c'] - p['o'])); d[b][0] += col(by[t]) == opp[col(p)]; d[b][1] += 1
    print(f"  {lab}: " + " | ".join(f"Q{b}: {100*k/n:.1f}% (n={n})" for b, (k, n) in sorted(d.items())))

# 3) a vela anterior grande + segunda anterior na mesma direção
print("\nTESTE — vela anterior no quintil mais alto (Q4) combinada com a cor da vela anterior:")
d = defaultdict(lambda: [0, 0])
for t in ts:
    p = by.get(t - MIN)
    if p is None or col(p) == 'D' or t < cut or bucket(abs(p['c'] - p['o'])) < 4: continue
    d[col(p)][0] += col(by[t]) == opp[col(p)]; d[col(p)][1] += 1
for c, (k, n) in sorted(d.items()): print(f"  após vela grande {c}: apostar {opp[c]} acerta {100*k/n:.1f}% (n={n}), p={sf(k,n,BE):.3f}")

# 4) sanidade: a abertura de uma vela é igual ao fechamento da anterior?
same = sum(1 for t in ts if (t - MIN) in by and abs(by[t]['o'] - by[t - MIN]['c']) < 1e-9)
print(f"\nSanidade: abertura == fechamento da vela anterior em {100*same/len(ts):.1f}% das velas")
# 5) quantas entradas por dia teria essa regra e quanto renderia por $22 de mão fixa (esperado)
n_day = alln / 30; ev = (allk / alln) * 0.96 - (1 - allk / alln)
print(f"Se entrasse em toda vela: ~{n_day:.0f} entradas/dia; valor esperado por $22: {22*ev:+.2f} -> {22*ev*n_day:+.0f} US$/dia (teórico, sem atraso de entrada)")
