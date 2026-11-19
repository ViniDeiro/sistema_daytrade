"""Estudo 1 (offline): a cor de uma vela M1 é previsível a partir das anteriores?
Escolhe a regra na 1ª metade do mês (treino) e mede SÓ na 2ª metade (teste). Mão fixa, payout 96% (equilíbrio 51,02%)."""
import json, math
from collections import defaultdict
from datetime import datetime
MIN = 60_000; BE = 1 / 1.96; PAY = 0.96
cs = sorted(json.load(open('dados/candles.json')), key=lambda c: c['t'])
col = lambda c: 'G' if c['c'] > c['o'] else 'R' if c['c'] < c['o'] else 'D'
colors = {c['t']: col(c) for c in cs}
ts = [c['t'] for c in cs]
cut = ts[0] + (ts[-1] - ts[0]) // 2
print(f"Treino: {datetime.fromtimestamp(ts[0]/1000):%d/%m} a {datetime.fromtimestamp(cut/1000):%d/%m} | Teste: {datetime.fromtimestamp(cut/1000):%d/%m} a {datetime.fromtimestamp(ts[-1]/1000):%d/%m}")
dojis = sum(1 for v in colors.values() if v == 'D'); print(f"velas: {len(cs)}, dojis: {dojis} ({100*dojis/len(cs):.2f}%), verdes: {100*sum(v=='G' for v in colors.values())/len(cs):.1f}%")

def sf(k, n, p):                                   # P(X>=k), com aproximação normal para n grande
    if n < 200: return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k, n+1))
    z = (k - 0.5 - n*p) / math.sqrt(n*p*(1-p)); return 0.5 * math.erfc(z / math.sqrt(2))

def features(t, name, k=0):
    """Só usa velas ANTERIORES a t (a vela t é o resultado)."""
    if name == 'cores':
        p = [colors.get(t - i*MIN) for i in range(1, k+1)]
        return None if None in p else ''.join(reversed(p))
    d = datetime.fromtimestamp(t/1000)
    if name == 'pos': return f"min%5={d.minute % 5}"
    if name == 'hora': return f"{d.hour:02d}h"
    if name == 'pos+2cores':
        p = [colors.get(t - i*MIN) for i in (1, 2)]
        return None if None in p else f"min%5={d.minute % 5}|{p[1]}{p[0]}"
    if name == 'pos+3cores':
        p = [colors.get(t - i*MIN) for i in (1, 2, 3)]
        return None if None in p else f"min%5={d.minute % 5}|{p[2]}{p[1]}{p[0]}"

def study(name, k=0):
    tr = defaultdict(lambda: [0, 0, 0]); te = defaultdict(lambda: [0, 0, 0])   # [G, R, outras]
    for t in ts:
        f = features(t, name, k)
        if f is None or t not in colors: continue
        o = colors[t]; d = tr if t < cut else te
        d[f][0 if o == 'G' else 1 if o == 'R' else 2] += 1
    rules = []
    for f, (g, r, x) in tr.items():
        n = g + r + x
        if n < 100: continue
        side = 'G' if g >= r else 'R'; hit = max(g, r) / n
        rules.append((hit, n, f, side))
    rules.sort(reverse=True)
    tot_n = tot_k = 0; rows = []
    for hit, n, f, side in rules:
        g, r, x = te.get(f, [0, 0, 0]); m = g + r + x; kk = g if side == 'G' else r
        tot_n += m; tot_k += kk; rows.append((f, side, hit, n, kk / m if m else 0, m))
    sel = rules[:max(1, len(rules)//4)]                       # só o quartil de regras que mais acertou no treino
    sn = sk = 0
    for hit, n, f, side in sel:
        g, r, x = te.get(f, [0, 0, 0]); sn += g + r + x; sk += g if side == 'G' else r
    return rows, (tot_k, tot_n), (sk, sn), len(rules)

print(f"\nEquilíbrio (payout 96%): {100*BE:.2f}% | cada ponto percentual acima disso vale ~{100*(2*0.0196):.1f}% de ROI por entrada\n")
print(f"{'conjunto de regras':<26}{'regras':>7}  {'TESTE: todas as regras':<30}{'TESTE: 25% melhores do treino':<34}")
for name, k in [('cores', 1), ('cores', 2), ('cores', 3), ('cores', 4), ('cores', 5), ('cores', 6), ('cores', 7), ('pos', 0), ('hora', 0), ('pos+2cores', 0), ('pos+3cores', 0)]:
    rows, (tk, tn), (sk, sn), nr = study(name, k)
    label = f"{name}{k if k else ''}"
    print(f"{label:<26}{nr:>7}  {tk}/{tn} = {100*tk/tn:5.2f}% (p={sf(tk,tn,BE):.2f})    {sk}/{sn} = {100*sk/sn:5.2f}% (p={sf(sk,sn,BE):.2f})")

print("\nMelhores regras individuais do treino e o que aconteceu no teste (padrão com k=5):")
rows, *_ = study('cores', 5)
for f, side, hit, n, th, m in rows[:6]:
    print(f"  após {f} -> apostar {side}: treino {100*hit:.1f}% (n={n}) | TESTE {100*th:.1f}% (n={m})")
