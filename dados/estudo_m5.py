"""Busca de estratégia em velas de 5 MINUTOS (offline, IDX). Descoberta no ANO 1 (10/2024-10/2025); validação no ANO 2 (10/2025-10/2026).
Aposta: a cor da PRÓXIMA vela M5, entrando na abertura dela (expiração de 5 min). Empate = devolvido. Payout 96% (a confirmar para M5)."""
import json, math
import numpy as np
from datetime import datetime
MIN = 60_000; M5 = 5 * MIN
PAY = 0.96; BE = 1 / (1 + PAY)

raw = sorted(json.load(open('dados/candles.json')), key=lambda c: c['t'])
t = np.array([c['t'] for c in raw]); o = np.array([c['o'] for c in raw]); h = np.array([c['h'] for c in raw]); l = np.array([c['l'] for c in raw]); c = np.array([c['c'] for c in raw])
b = t // M5
ub, first, cnt = np.unique(b, return_index=True, return_counts=True)
ok = cnt == 5                                          # só blocos de 5 velas completas
first = first[ok]; ub = ub[ok]
T = ub * M5
O = o[first]; C = c[first + 4]
Hh = np.maximum.reduceat(h, first)[:]                  # máximo por bloco (cuidado: reduceat usa os índices iniciais)
Ll = np.minimum.reduceat(l, first)[:]
# reduceat sobre 'first' filtrado pode ultrapassar o bloco; recalcula de forma segura
Hh = np.array([h[i:i + 5].max() for i in first]); Ll = np.array([l[i:i + 5].min() for i in first])
n = len(T)
col = np.sign(C - O).astype(int)
body = np.abs(C - O) / O
contig = np.zeros(n, bool); contig[1:] = (T[1:] - T[:-1]) == M5
clv = np.where(Hh > Ll, (C - Ll) / np.where(Hh > Ll, Hh - Ll, 1), 0.5)
cs = np.concatenate([[0], np.cumsum(body)])
m12 = np.full(n, np.nan); m12[12:] = (cs[12:n] - cs[0:n - 12]) / 12     # média do corpo das 12 velas anteriores a i
dts = [datetime.fromtimestamp(x / 1000) for x in T]
hour = np.array([d.hour for d in dts]); minute = np.array([d.minute for d in dts])
cut = datetime(2025, 10, 7, 13, 50).timestamp() * 1000
isA = T < cut; isB = ~isA
print(f"Velas M5: {n:,} | ano 1 (descoberta): {isA.sum():,} | ano 2 (validação): {isB.sum():,} | dojis M5: {100*np.mean(col==0):.2f}%")

idx = np.arange(n)
prev = lambda k: col[idx - k]
valid1 = contig & (col[idx - 1] != 0)
# sequência de velas iguais terminando em i-1
run = np.zeros(n, int)
for i in range(1, n): run[i] = (run[i - 1] + 1 if (col[i] != 0 and contig[i] and col[i] == col[i - 1]) else (1 if col[i] != 0 else 0))
pr = np.zeros(n, int); pr[1:] = run[:-1]
ratio = np.where(m12 > 0, body[idx - 1] / np.where(m12 > 0, m12, 1), np.nan)
sz = np.digitize(np.nan_to_num(ratio, nan=1.0), [0.5, 1.0, 2.0])      # 0..3
cb = np.digitize(clv[idx - 1], [0.2, 0.4, 0.6, 0.8])                   # 0..4: onde a vela anterior fechou dentro da própria faixa
cb2 = np.digitize(clv[idx - 2], [0.2, 0.4, 0.6, 0.8])
up = (prev(1) > 0).astype(int)

def nodoji(k): return np.all([prev(j) != 0 for j in range(1, k + 1)], axis=0)
cats = {}
cats['sequencia (tamanho+cor)'] = (valid1, np.minimum(pr, 8) * 2 + up)
for k in range(2, 7):
    mk = nodoji(k) & contig; code = sum(((prev(j) > 0).astype(int) << (j - 1)) for j in range(1, k + 1)); cats[f'padrao {k} cores'] = (mk, code)
cats['tamanho x cor'] = (valid1 & ~np.isnan(ratio), sz * 2 + up)
cats['hora x cor'] = (valid1, hour * 2 + up)
cats['minuto da hora x cor'] = (valid1, (minute // 5) * 2 + up)
cats['fechamento na faixa x cor'] = (valid1, cb * 2 + up)
cats['fechamento x tamanho x cor'] = (valid1 & ~np.isnan(ratio), (cb * 4 + sz) * 2 + up)
cats['sequencia x tamanho'] = (valid1 & ~np.isnan(ratio), ((np.minimum(pr, 5) * 4 + sz) * 2 + up))
mk2 = nodoji(2) & contig
cats['2 cores x fechamento'] = (mk2, ((prev(1) > 0).astype(int) * 2 + (prev(2) > 0).astype(int)) * 5 + cb)
cats['sequencia x faixa horaria'] = (valid1, (np.minimum(pr, 6) * 4 + hour // 6) * 2 + up)

def sf(k, nn, p):
    if nn == 0: return 1.0
    z = (k - 0.5 - nn * p) / math.sqrt(nn * p * (1 - p)); return 0.5 * math.erfc(z / math.sqrt(2))
rules = []
for name, (mask, cat) in cats.items():
    for cid in np.unique(cat[mask]):
        sel = mask & (cat == cid)
        a = sel & isA & (col != 0); G = int((a & (col > 0)).sum()); R = int((a & (col < 0)).sum()); nA = G + R
        if nA < 1500: continue
        side = 1 if G >= R else -1; kA = G if side > 0 else R
        bsel = sel & isB & (col != 0); nB = int(bsel.sum()); kB = int((bsel & (col == side)).sum())
        rules.append(dict(fam=name, cid=int(cid), side=side, nA=nA, hA=kA / nA, pA=sf(kA, nA, BE), nB=nB, hB=(kB / nB if nB else float('nan')), pB=sf(kB, nB, BE), kB=kB))
ntests = len(rules); bonf = 0.05 / ntests
print(f"\nRegras testadas (n>=1500 no ano 1): {ntests} | limiar Bonferroni p<{bonf:.1e} | equilíbrio com payout {int(100*PAY)}%: {100*BE:.2f}%")
rules.sort(key=lambda r: -r['hA'])
print(f"\n{'família':<30}{'id':>5}{'lado':>5}{'ANO 1: acerto (n)':>22}{'p':>9}   {'ANO 2: acerto (n)':>22}{'p':>7}")
for r in rules[:15]:
    print(f"{r['fam']:<30}{r['cid']:>5}{('G' if r['side']>0 else 'R'):>5}{100*r['hA']:>13.2f}% ({r['nA']:>5}){r['pA']:>9.4f}   {100*r['hB']:>13.2f}% ({r['nB']:>5}){r['pB']:>7.3f}")
sig = [r for r in rules if r['pA'] < bonf and r['hA'] > BE]
print(f"\nRegras que passam no ano 1 (acerto > equilíbrio e p < Bonferroni): {len(sig)}")
if sig:
    kB = sum(r['kB'] for r in sig); nB = sum(r['nB'] for r in sig)
    print(f"  Conjunto delas no ANO 2: {100*kB/nB:.2f}% em {nB} entradas (equilíbrio {100*BE:.2f}%) | ROI por entrada: {100*((kB/nB)*(1+PAY)-1):+.2f}%")
    for r in sig[:10]: print(f"   {r['fam']} id={r['cid']} lado={'G' if r['side']>0 else 'R'}: ano1 {100*r['hA']:.2f}% -> ano2 {100*r['hB']:.2f}% ({r['nB']})")
top = [r for r in rules if r['hA'] > 0.525]
print(f"\nRegras com acerto > 52,5% no ano 1: {len(top)}; no ano 2 acima de {100*BE:.2f}%: {sum(1 for r in top if r['hB'] > BE)}; acima de 52,5%: {sum(1 for r in top if r['hB'] > 0.525)}")
# sensibilidade ao payout
print("\nEquilíbrio conforme o payout do M5 (a confirmar na plataforma):", " | ".join(f"{int(100*p)}%: {100/(1+p):.1f}%" for p in (0.96, 0.92, 0.90, 0.88, 0.85)))
