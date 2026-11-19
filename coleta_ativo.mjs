// Coleta somente leitura de velas M1 de um ativo da Ebinex, com sessão copiada. Uso: node coleta_ativo.mjs <perfil_copiado> <SIMBOLO> <dias> [--probe]
import { chromium } from 'playwright';
import fs from 'fs';
const [profile, SYMBOL, DAYS] = [process.argv[2], process.argv[3], +process.argv[4]], PROBE = process.argv.includes('--probe'), MIN = 60_000;
const OUT = `dados/${SYMBOL}_candles.json`;
const ctx = await chromium.launchPersistentContext(profile, { headless: true, viewport: { width: 1400, height: 900 } });
const page = ctx.pages()[0] ?? await ctx.newPage();
let hdrs = null;
page.on('request', r => { if (!hdrs && r.url().includes('/dataProvider/aggregatedTrades')) hdrs = r.headers(); });
await page.goto('https://app.ebinex.com', { waitUntil: 'domcontentloaded' });
for (let i = 0; i < 60 && !hdrs; i++) await page.waitForTimeout(500);
if (!hdrs) { await ctx.close(); throw new Error('sessão não carregou'); }
const get = async (a, b) => { const r = await ctx.request.get(`https://api.ebinex.com/dataProvider/aggregatedTrades?symbol=${SYMBOL}&candleTimeFrame=M1&from=${a}&to=${b}&limit=1500`, { headers: hdrs }); return [r.status(), r.ok() ? await r.json() : null]; };
const now = Date.now();
if (PROBE) {
  for (const d of (process.env.PROBE_DAYS || '0.1,30,90,180,365').split(',').map(Number)) { const a = now - d * 86400_000; const [s, j] = await get(a, a + 1500 * MIN); console.log(`${d} dias atrás: HTTP ${s}, velas=${j?.length ?? '-'}${j?.length ? ' de ' + new Date(j[0].t).toLocaleString('pt-BR') : ''}`); await page.waitForTimeout(1500); }
  await ctx.close(); process.exit(0);
}
const all = new Map(); if (fs.existsSync(OUT)) for (const c of JSON.parse(fs.readFileSync(OUT))) all.set(c.t, c);
let from = now - DAYS * 86400_000, reqs = 0;
for (const k of all.keys()) if (k > from) from = Math.max(from, k + MIN);   // retoma de onde parou
for (let a = from; a < now; a += 1500 * MIN) {
  const [s, j] = await get(a, Math.min(a + 1500 * MIN, now)); reqs++;
  if (!j) { fs.writeFileSync(OUT, JSON.stringify([...all.values()].sort((x, y) => x.t - y.t))); await ctx.close(); throw new Error('HTTP ' + s); }
  for (const c of j) all.set(c.t, { t: c.t, o: c.o, h: c.h, l: c.l, c: c.c });
  if (reqs % 20 === 0) { fs.writeFileSync(OUT, JSON.stringify([...all.values()].sort((x, y) => x.t - y.t))); console.log(reqs, 'requisições, velas:', all.size); }
  await page.waitForTimeout(2000);
}
await ctx.close();
const c = [...all.values()].sort((x, y) => x.t - y.t); fs.writeFileSync(OUT, JSON.stringify(c));
console.log({ ativo: SYMBOL, requisicoes: reqs, velas: c.length, falhas: c.slice(1).filter((x, i) => x.t - c[i].t !== MIN).length, de: new Date(c[0].t).toLocaleString('pt-BR'), ate: new Date(c.at(-1).t).toLocaleString('pt-BR') });
