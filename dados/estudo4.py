"""Estudo 4 (offline): robustez da regra 'após >=k velas iguais, a próxima repete'.
Bootstrap por DIA (respeita a dependência entre amostras), resultado diário em mão fixa, queda máxima, horas do dia."""
import json, math, random
from collections import defaultdict
from datetime import datetime
MIN = 60_000; BE = 1 / 1.96; STAKE = 22; PAY = 0.96
cs = sorted(json.load(open('dados/candles.json')), key=lambda c: c['t'])
by = {c['t']: c for c in cs}
col = lambda c: 'G' if c['c'] > c['o'] else 'R' if c['c'] < c['o'] else 'D'
ts = [c['t'] for c in cs]
day = lambda t: datetime.fromtimestamp(t / 1000).strftime('%Y-%m-%d')

S = []                                      # (t, s, acertou)
for t in ts:
    if (t - MIN) not in by: continue
    c = col(by[t - MIN])
    if c == 'D': continue
    s = 1
    while (t - (s + 1) * MIN) in by and col(by[t - (s + 1) * MIN]) == c: s += 1
    S.append((t, s, col(by[t]) == c))

random.seed(7)
def analyze(k):
    rows = [r for r in S if r[1] >= k]
    d = defaultdict(lambda: [0, 0])
    for t, s, h in rows: d[day(t)][0] += h; d[day(t)][1] += 1
    days = sorted(d); n = sum(d[x][1] for x in days); hits = sum(d[x][0] for x in days)
    # bootstrap por dia
    boots = []
    for _ in range(4000):
        samp = [d[random.choice(days)] for _ in days]
        nn = sum(x[1] for x in samp); boots.append(sum(x[0] for x in samp) / nn)
    boots.sort(); lo, hi = boots[100], boots[3900]
    p_below = sum(b <= BE for b in boots) / len(boots)
    pl_days = [(x, d[x][0] * STAKE * PAY - (d[x][1] - d[x][0]) * STAKE, d[x][1]) for x in days]
    full = [p for p in pl_days if p[2] > 150 // k] if False else pl_days
    pos = sum(1 for _, p, _ in pl_days if p > 0)
    eq = pk = dd = 0
    for t, s, h in sorted(rows): eq += STAKE * PAY if h else -STAKE; pk = max(pk, eq); dd = max(dd, pk - eq)
    print(f"\n--- regra: >= {k} velas iguais -> apostar que repete ---")
    print(f"entradas {n} ({n/len(days):.0f}/dia) | acerto {100*hits/n:.2f}% | IC95% por dia-bootstrap [{100*lo:.2f}%, {100*hi:.2f}%] | P(acerto real <= 51,02%) ≈ {p_below:.3f}")
    print(f"mão fixa ${STAKE}: mês {sum(p for _,p,_ in pl_days):+.0f} | média/dia {sum(p for _,p,_ in pl_days)/len(days):+.0f} | dias positivos {pos}/{len(days)} | pior dia {min(p for _,p,_ in pl_days):+.0f} | melhor {max(p for _,p,_ in pl_days):+.0f} | maior queda {dd:.0f}")
    return rows

for k in (3, 4, 5, 6):
    rows = analyze(k)
    if k == 4:
        print("   por hora do dia (acerto%, n):")
        h = defaultdict(lambda: [0, 0])
        for t, s, a in rows: h[datetime.fromtimestamp(t/1000).hour][0] += a; h[datetime.fromtimestamp(t/1000).hour][1] += 1
        print("   " + " ".join(f"{x:02d}h:{100*h[x][0]/h[x][1]:.0f}" for x in sorted(h)))
        # resultado diário completo para ver a regularidade
        d = defaultdict(lambda: [0, 0])
        for t, s, a in rows: d[day(t)][0] += a; d[day(t)][1] += 1
        print("   P/L por dia ($22): " + " ".join(f"{(d[x][0]*STAKE*PAY-(d[x][1]-d[x][0])*STAKE):+.0f}" for x in sorted(d)))
