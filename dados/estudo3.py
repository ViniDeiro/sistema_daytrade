"""Estudo 3 (offline): continuação de tendência. Após uma sequência de s velas da mesma cor, apostar que a próxima repete a cor.
Mão fixa, doji = perda, payout 96% (equilíbrio 51,02%). Treino = 1ª metade do mês, teste = 2ª."""
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
roi = lambda h: 100 * (h * 1.96 - 1)

def streak(t):
    """tamanho da sequência de velas da mesma cor terminando em t-1 (só passado)."""
    c = col(by[t - MIN]) if (t - MIN) in by else 'D'
    if c == 'D': return 0, c
    s = 1
    while (t - (s + 1) * MIN) in by and col(by[t - (s + 1) * MIN]) == c: s += 1
    return s, c

# amostras: (t, s, cor anterior, acertou_continuação)
S = []
for t in ts:
    if (t - MIN) not in by: continue
    s, c = streak(t)
    if s == 0: continue
    S.append((t, s, c, col(by[t]) == c))

def line(rows, label):
    n = len(rows); k = sum(r[3] for r in rows)
    return f"{label}: {k}/{n} = {100*k/n:.2f}%  ROI {roi(k/n):+.1f}%  p={sf(k,n,BE):.3f}" if n else f"{label}: -"

print("Continuação da cor após uma sequência de EXATAMENTE s velas iguais (s>=7 agrupado):")
print(f"{'s':>3} | {'TREINO':<46}| {'TESTE':<46}")
for s in range(1, 8):
    f = (lambda r: r[1] == s) if s < 7 else (lambda r: r[1] >= 7)
    a = [r for r in S if r[0] < cut and f(r)]; b = [r for r in S if r[0] >= cut and f(r)]
    print(f"{s:>3} | {line(a, f'n={len(a)}'):<46}| {line(b, f'n={len(b)}'):<46}")

print("\nRegra H: 'após >=3 velas iguais, apostar que a próxima repete' — por semana:")
wk = defaultdict(list)
for r in S:
    if r[1] >= 3: wk[(r[0] - t0) // (7 * 86400_000)].append(r)
for w in sorted(wk): print("  " + line(wk[w], f"semana {w+1} (n={len(wk[w])})"))
allr = [r for r in S if r[1] >= 3]
print("  " + line(allr, "MÊS"))
print("  " + line([r for r in allr if r[0] >= cut], "TESTE (2ª metade)"))

print("\nMesma regra com sequência >=2 e >=4, mês e metades:")
for m in (2, 4, 5):
    rr = [r for r in S if r[1] >= m]
    print(f"  >= {m}: " + line([r for r in rr if r[0] < cut], 'treino') + " | " + line([r for r in rr if r[0] >= cut], 'teste'))

# quantas entradas por dia e valor esperado
n = len(allr); k = sum(r[3] for r in allr); h = k / n
ev = h * 0.96 - (1 - h)
print(f"\nRegra '>=3 iguais': {n/30:.0f} entradas/dia | EV por $22 = {22*ev:+.2f} | teórico {22*ev*n/30:+.0f} US$/dia (sem atraso de entrada, sem limite da corretora)")
# maior queda com mão fixa de $22 em sequência cronológica
eq = pk = dd = 0
for r in sorted(allr):
    eq += 22 * 0.96 if r[3] else -22; pk = max(pk, eq); dd = max(dd, pk - eq)
print(f"Mão fixa $22 em todas essas entradas: resultado do mês {eq:+.0f} | maior queda {dd:.0f}")
