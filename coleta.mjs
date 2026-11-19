// Coleta ÚNICA de velas M1 (somente leitura) usando uma CÓPIA do perfil, sem mexer no servidor.
// Uso: node coleta.mjs <pasta-do-perfil-copiado> --hours 48
import { chromium } from 'playwright';
import fs from 'fs';
import { catalog, STRATEGIES } from './catalog.mjs';

const profile = process.argv[2], HOURS = +process.argv[process.argv.indexOf('--hours') + 1], MIN = 60_000;
const ctx = await chromium.launchPersistentContext(profile, { headless: true, viewport: { width: 1400, height: 900 } });
const page = ctx.pages()[0] ?? await ctx.newPage();
let hdrs = null;
page.on('request', r => { if (!hdrs && r.url().includes('/dataProvider/aggregatedTrades')) hdrs = r.headers(); });
await page.goto('https://app.ebinex.com', { waitUntil: 'domcontentloaded' });
for (let i = 0; i < 60 && !hdrs; i++) await page.waitForTimeout(500);
if (!hdrs) { await ctx.close(); throw new Error('sessão não carregou'); }

const now = Date.now(), hs = new Date(now); hs.setMinutes(0, 0, 0);
const from = hs.getTime() - HOURS * 3600_000 - 10 * MIN, all = new Map();
let reqs = 0;
// reaproveita o que já foi coletado e busca só o trecho que falta (antes e depois)
if (fs.existsSync('dados/candles.json')) for (const c of JSON.parse(fs.readFileSync('dados/candles.json'))) all.set(c.t, c);
let lo = null, hi = null;
for (const k of all.keys()) { if (lo === null || k < lo) lo = k; if (hi === null || k > hi) hi = k; }
const ranges = lo === null ? [[from, now]] : [[from, lo], [hi + MIN, now]].filter(([a, b]) => b - a > MIN);
for (const [ra, rb] of ranges) for (let a = ra; a < rb; a += 1500 * MIN) {
  const b = Math.min(a + 1500 * MIN, rb);
  const r = await ctx.request.get(`https://api.ebinex.com/dataProvider/aggregatedTrades?symbol=IDXUSDT&candleTimeFrame=M1&from=${a}&to=${b}&limit=1500`, { headers: hdrs });
  reqs++;
  if (!r.ok()) { await ctx.close(); throw new Error('HTTP ' + r.status()); }
  for (const c of await r.json()) all.set(c.t, { t: c.t, o: c.o, h: c.h, l: c.l, c: c.c });
  if (reqs % 40 === 0) { fs.writeFileSync('dados/candles.json', JSON.stringify([...all.values()].sort((x, y) => x.t - y.t))); console.log(reqs, 'requisições, velas:', all.size); }
  await page.waitForTimeout(2000);                       // espaça as requisições
}
await ctx.close();
const candles = [...all.values()].sort((x, y) => x.t - y.t);
fs.writeFileSync('dados/candles.json', JSON.stringify(candles));
const ciclos = Object.fromEntries(Object.entries(STRATEGIES).map(([id, st]) => [id, catalog(candles, now, st)]));
fs.writeFileSync('dados/ciclos.json', JSON.stringify(ciclos));
const gaps = candles.slice(1).filter((c, i) => c.t - candles[i].t !== MIN).length;
console.log({ requisicoes: reqs, velas: candles.length, falhasNaSequencia: gaps, de: new Date(candles[0].t).toLocaleString('pt-BR'), ate: new Date(candles.at(-1).t).toLocaleString('pt-BR'), ciclos4x2: ciclos['4x2'].length, ciclosP23: ciclos.p23.length });
