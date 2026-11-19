// Catalogador 4x2 e Padrão 23 (somente leitura). Uso: node catalog.mjs [--hours 5] [--show]
// Regra por quadrante de 5 velas M1 (B = minuto múltiplo de 5):
//   vela1 descarta | vela2 = cor-alvo | vela4 = entrada | vela5 = Gale1 | vela6 (1ª do próximo quadrante) = Gale2
//   Padrão 23: vela1 = cor-alvo | vela2 = entrada | vela3 = Gale1 | vela4 = Gale2
//   doji (close == open) nunca bate a cor. Doji na vela2 => sem sinal.
import { chromium } from 'playwright';
import fs from 'fs';

const args = process.argv.slice(2);
const HOURS = +(args[args.indexOf('--hours') + 1] || 5);
const SYMBOL = 'IDXUSDT', MIN = 60_000;

const color = c => (c.c > c.o ? 'G' : c.c < c.o ? 'R' : 'D');
const hhmm = t => new Date(t).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

// ref = índice da vela que define a cor-alvo; entradas = índices [entrada, Gale1, Gale2] dentro do quadrante (5 = 1ª do próximo)
export const STRATEGIES = {
  '4x2': { nome: 'Estratégia 4x2', ref: 1, entradas: [3, 4, 5] },
  'p23': { nome: 'Padrão 23', ref: 0, entradas: [1, 2, 3] },
};

export function catalog(candles, now = Date.now(), strat = STRATEGIES['4x2']) {
  const by = new Map(candles.map(c => [c.t, c]));
  const closed = t => by.has(t) && t + MIN <= now;
  const hourStart = new Date(now); hourStart.setMinutes(0, 0, 0);
  const start = hourStart.getTime() - HOURS * 3600_000;
  const out = [];
  for (let B = start; B + MIN <= now; B += 5 * MIN) {
    if (!closed(B + strat.ref * MIN)) break;           // vela de referência ainda não fechou
    const target = color(by.get(B + strat.ref * MIN));
    const row = { bloco: hhmm(B), t: B, alvo: target, resultado: null };
    if (target === 'D') { row.resultado = 'sem-sinal'; out.push(row); continue; }
    row.resultado = 'loss';
    for (const [k, i] of strat.entradas.entries()) {
      if (!closed(B + i * MIN)) { row.resultado = 'pendente'; break; }
      if (color(by.get(B + i * MIN)) === target) { row.resultado = 'win' + k; break; }
    }
    out.push(row);
  }
  return out;
}

export function summarize(rows) {
  const done = rows.filter(r => /^(win|loss)/.test(r.resultado));
  const n = k => done.filter(r => r.resultado === k).length;
  const lastWin = [...done].reverse().find(r => r.resultado.startsWith('win'));
  let streak = 0; for (let i = done.length - 1; i >= 0 && done[i].resultado === 'loss'; i--) streak++;
  return { ciclos: done.length, win0: n('win0'), win1: n('win1'), win2: n('win2'), loss: n('loss'),
    assertividade: done.length ? +(100 * n('win0') / done.length).toFixed(1) : null,
    taxaWin: done.length ? +(100 * (done.length - n('loss')) / done.length).toFixed(1) : null,
    ultimoWin: lastWin ? `${lastWin.bloco} (${lastWin.resultado})` : null, lossesSeguidos: streak };
}

export async function fetchCandles() {
  const ctx = await chromium.launchPersistentContext('./profile', { headless: true, viewport: { width: 1400, height: 900 } });
  const page = ctx.pages()[0] ?? await ctx.newPage();
  let hdrs = null;
  page.on('request', r => { if (!hdrs && r.url().includes('/dataProvider/aggregatedTrades')) hdrs = r.headers(); });
  await page.goto('https://app.ebinex.com', { waitUntil: 'domcontentloaded' });
  for (let i = 0; i < 60 && !hdrs; i++) await page.waitForTimeout(500);
  if (!hdrs) { await ctx.close(); throw new Error('O app não pediu o histórico — sessão expirada? Rode "node sniff.mjs" e faça login de novo.'); }

  const now = Date.now(), hourStart = new Date(now); hourStart.setMinutes(0, 0, 0);
  const from = hourStart.getTime() - HOURS * 3600_000 - 10 * MIN, all = new Map();
  for (let a = from; a < now; a += 250 * MIN) {            // janelas de 250 velas (limite ~300)
    const b = Math.min(a + 250 * MIN, now);
    const url = `https://api.ebinex.com/dataProvider/aggregatedTrades?symbol=${SYMBOL}&candleTimeFrame=M1&from=${a}&to=${b}&limit=300`;
    const r = await ctx.request.get(url, { headers: hdrs });
    if (!r.ok()) { await ctx.close(); throw new Error(`HTTP ${r.status()} ao buscar velas`); }
    for (const c of await r.json()) all.set(c.t, { t: c.t, o: c.o, h: c.h, l: c.l, c: c.c });
  }
  await ctx.close();
  return [...all.values()].sort((x, y) => x.t - y.t);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const candles = await fetchCandles();
  const rows = catalog(candles), sum = summarize(rows);
  fs.writeFileSync('catalog.json', JSON.stringify({ geradoEm: new Date().toISOString(), ativo: SYMBOL, horas: HOURS, resumo: sum, blocos: rows }, null, 2));
  const tag = { win0: 'WIN', win1: 'GALE 1', win2: 'GALE 2', loss: 'LOSS', pendente: '…', 'sem-sinal': '—' };
  const first = candles[0] && hhmm(candles[0].t), last = candles.at(-1) && hhmm(candles.at(-1).t);
  console.log(`\n${SYMBOL} M1 — ${candles.length} velas (${first} → ${last}), janela ${HOURS}h\n`);
  console.log(rows.map(r => `${r.bloco}  alvo ${r.alvo}  ${tag[r.resultado]}`).join('\n'));
  console.log('\nResumo:', sum);
}
