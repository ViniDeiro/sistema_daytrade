"""Estudo 7 (offline, sem requisições): busca de padrões no BTC (treino: antes de 09/07/2026) e validação em
(A) BTC 09/07-07/10 (nunca visto) e (B) IDX 09/07-07/10 (nunca visto). Mão fixa, doji = perda, payout 96% (equilíbrio 51,02%).
Regra = condição observável ANTES da vela de entrada -> apostar G ou R (lado escolhido pela maioria no treino)."""
import json, math
import numpy as np
from collections import defaultdict
from datetime import datetime
MIN = 60_000; BE = 1 / 1.96
SPLIT = int(datetime(2026, 7, 9, 0, 0).timestamp() * 1000)

def load(kind):
    if kind == 'idx':
        raw = sorted(json.load(open('dados/candles.json')), key=lambda c: c['t'])
        return np.array([c['t'] for c in raw]), np.array([c['o'] for c in raw]), np.array([c['c'] for c in raw])
    raw = json.load(open('dados/binance_BTCUSDT_1ano.json')); ks = sorted(int(k) for k in raw)
    return np.array(ks), np.array([raw[str(k)][0] for k in ks]), np.array([raw[str(k)][1] for k in ks])

def samples(kind):
    """Retorna dict: regra -> arrays (t, acertou_G) — tudo pré-computado com velas ANTERIORES à vela de entrada i."""
    t, o, c = load(kind); n = len(t)
    col = np.sign(c - o).astype(int)                 # 1 verde, -1 vermelha, 0 doji
    body = np.abs(c - o) / o
    cs = np.concatenate([[0], np.cumsum(body)])
    m60 = np.full(n, np.nan); m60[60:] = (cs[60:n] - cs[0:n-60]) / 60       # média das 60 velas ANTERIORES a i (i-60..i-1)
    contig = np.zeros(n, bool); contig[8:] = (t[8:] - t[:-8]) == 8 * MIN      # 8 velas anteriores contíguas
    hour = np.array([datetime.fromtimestamp(x / 1000).hour for x in t]); minute = np.array([datetime.fromtimestamp(x / 1000).minute for x in t])
    idx = np.arange(n)
    out = defaultdict(lambda: ([], []))
    ok = contig & ~np.isnan(m60) & (m60 > 0)
    last = lambda k: col[idx - k]                      # cor da vela i-k
    ratio = np.where(ok, body[idx - 1] / np.where(m60 > 0, m60, 1), 0)
    rb = np.digitize(ratio, [0.5, 1.0, 2.0])           # 0..3
    net5 = np.where(ok, (c[idx - 1] - o[idx - 5]) / o[idx - 5] / np.where(m60 > 0, m60 * math.sqrt(5), 1), 0)
    zb = np.digitize(net5, [-2, -1, 0, 1, 2])          # 0..5
    keys = {}
    def add(name, mask, key):
        sel = ok & mask
        for i in idx[sel]: pass
    # padrões de cores (sem doji) k=2..7
    nodoji = lambda k: np.all([last(j) != 0 for j in range(1, k + 1)], axis=0)
    strings = {}
    for k in range(2, 8):
        m = nodoji(k) & ok
        code = sum(((last(j) > 0).astype(int) << (j - 1)) for j in range(1, k + 1))
        strings[k] = (m, code)
    rules = []
    def emit(rname, mask, code):
        sel = np.where(mask & ok)[0]
        for cd in np.unique(code[sel]):
            ii = sel[code[sel] == cd]
            rules.append(((rname, int(cd)), t[ii], col[ii]))
    for k in range(2, 8): emit(f'cores{k}', *strings[k])
    m2 = nodoji(2); c2 = ((last(1) > 0).astype(int)) + 2 * (last(2) > 0)
    m3 = nodoji(3); c3 = c2 + 4 * (last(3) > 0)
    emit('cores2+tamanho_ult', m2, c2 * 4 + rb)
    emit('cores3+tamanho_ult', m3, c3 * 4 + rb)
    m1 = last(1) != 0
    emit('ult+deriva5', m1, (last(1) > 0).astype(int) * 6 + zb)
    emit('hora+ult', m1, hour * 2 + (last(1) > 0).astype(int))
    emit('min%5+cores2', m2, (minute % 5) * 4 + c2)
    emit('min%15+cores2', m2, (minute % 15) * 4 + c2)
    emit('min%5+ult+tamanho', m1, (minute % 5) * 8 + (last(1) > 0).astype(int) * 4 + rb)
    return rules

btc = samples('btc'); idx = samples('idx')
print(f"regras candidatas (padrões x famílias): BTC {len(btc)} | IDX {len(idx)}")
idxd = {r[0]: r for r in idx}

def stat(tt, cc, side, lo, hi):
    m = (tt >= lo) & (tt < hi)
    n = int(m.sum()); k = int((cc[m] == side).sum()); return k, n
def sf(k, n, p):
    if n == 0: return 1.0
    z = (k - 0.5 - n * p) / math.sqrt(n * p * (1 - p)); return 0.5 * math.erfc(z / math.sqrt(2))

TOP = 4_000_000_000_000
tmin = 0
rows = []
for key, tt, cc in btc:
    k, n = stat(tt, cc, 1, 0, SPLIT)
    if n < 1500: continue
    g = int(((cc[tt < SPLIT]) == 1).sum()); r = int(((cc[tt < SPLIT]) == -1).sum())
    side = 1 if g >= r else -1
    k, n = stat(tt, cc, side, 0, SPLIT)
    rows.append((k / n, n, key, side, sf(k, n, BE)))
rows.sort(reverse=True)
ntests = len(rows); bonf = 0.05 / ntests
print(f"regras com n>=1500 no treino: {ntests} | limiar de significância corrigido p<{bonf:.2e}")
print("\nMelhores 10 regras do TREINO do BTC (10/2025 -> 09/07/2026):")
print(f"{'regra':<34}{'lado':>5}{'treino':>14}{'p':>10} | {'BTC teste (09/07-07/10)':>26} | {'IDX (09/07-07/10)':>22}")
sel = []
for hit, n, key, side, p in rows[:10] + [r for r in rows[10:] if r[4] < bonf]:
    tb = [x for x in btc if x[0] == key][0];
    kb, nb = stat(tb[1], tb[2], side, SPLIT, TOP)
    ti = idxd.get(key)
    ki, ni = stat(ti[1], ti[2], side, SPLIT, TOP) if ti else (0, 0)
    if p < bonf and hit > BE: sel.append((key, side, kb, nb, ki, ni))
    print(f"{str(key):<34}{('G' if side>0 else 'R'):>5}{100*hit:>8.2f}% ({n:>5}){p:>10.4f} | {100*kb/max(nb,1):>8.2f}% ({nb:>6})  p={sf(kb,nb,BE):.2f} | {100*ki/max(ni,1):>8.2f}% ({ni:>5}) p={sf(ki,ni,BE):.2f}")
print(f"\nRegras que passam no treino do BTC (acerto>51,02% e p<{bonf:.1e}): {len(sel)}")
if sel:
    kb = sum(s[2] for s in sel); nb = sum(s[3] for s in sel); ki = sum(s[4] for s in sel); ni = sum(s[5] for s in sel)
    print(f"  Conjunto delas no BTC teste: {100*kb/nb:.2f}% ({nb}) | no IDX: {100*ki/ni:.2f}% ({ni})")
# controle: o melhor do treino geral, o que o acaso entregaria
import random
random.seed(0)
print("\nControle: quanto de 'melhor acerto' o ACASO daria com esse número de regras (rótulos embaralhados, treino)?")
best_rand = []
allc = [(tt[tt < SPLIT], cc[tt < SPLIT]) for key, tt, cc in btc if len(tt[tt < SPLIT]) >= 1500]
for rep in range(5):
    b = 0
    for tt, cc in allc:
        sh = cc.copy(); np.random.default_rng(rep).shuffle(sh)
        g = int((sh == 1).sum()); r = int((sh == -1).sum()); h = max(g, r) / len(sh); b = max(b, h)
    best_rand.append(b)
print("  melhor acerto por acaso em 5 embaralhamentos: " + ", ".join(f"{100*x:.2f}%" for x in best_rand))
