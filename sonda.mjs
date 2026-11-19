// Sonda: 2 requisições para descobrir o limite por pedido e a profundidade do histórico.
import { chromium } from 'playwright';
const MIN = 60_000, profile = process.argv[2];
const ctx = await chromium.launchPersistentContext(profile, { headless: true });
const page = ctx.pages()[0] ?? await ctx.newPage();
let hdrs = null;
page.on('request', r => { if (!hdrs && r.url().includes('/dataProvider/aggregatedTrades')) hdrs = r.headers(); });
await page.goto('https://app.ebinex.com', { waitUntil: 'domcontentloaded' });
for (let i = 0; i < 60 && !hdrs; i++) await page.waitForTimeout(500);
if (!hdrs) { console.log('SEM SESSÃO: o app não pediu o histórico (login expirado?)'); await ctx.close(); process.exit(1); }
const now = Date.now();
for (const days of [180, 270, 365, 400]) {
  const a = now - days * 86400_000;
  const r = await ctx.request.get(`https://api.ebinex.com/dataProvider/aggregatedTrades?symbol=IDXUSDT&candleTimeFrame=M1&from=${a}&to=${a + 1500 * MIN}&limit=1500`, { headers: hdrs });
  const body = r.ok() ? await r.json() : null;
  console.log(days + ' dias atrás -> HTTP', r.status(), body ? `velas=${body.length}${body.length ? ' de ' + new Date(body[0].t).toLocaleString('pt-BR') : ''}` : '');
  await page.waitForTimeout(2000);
}
await ctx.close();
