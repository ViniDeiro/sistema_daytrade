// Verificação pontual: baixa as últimas ~6h de velas M1 reais do IDXUSDT (1 requisição) para comparar com o que o motor leu.
import { chromium } from 'playwright'; import fs from 'fs';
const profile = process.argv[2], MIN = 60_000;
const ctx = await chromium.launchPersistentContext(profile, { headless: true });
const page = ctx.pages()[0] ?? await ctx.newPage(); let hdrs = null;
page.on('request', r => { if (!hdrs && r.url().includes('/dataProvider/aggregatedTrades')) hdrs = r.headers(); });
await page.goto('https://app.ebinex.com', { waitUntil: 'domcontentloaded' });
for (let i = 0; i < 60 && !hdrs; i++) await page.waitForTimeout(500);
if (!hdrs) { console.log('sessão não carregou'); await ctx.close(); process.exit(1); }
const now = Date.now();
const r = await ctx.request.get(`https://api.ebinex.com/dataProvider/aggregatedTrades?symbol=IDXUSDT&candleTimeFrame=M1&from=${now - 6 * 3600_000}&to=${now}&limit=1500`, { headers: hdrs });
const j = await r.json(); fs.writeFileSync(process.argv[3], JSON.stringify(j)); console.log('velas baixadas:', j.length); await ctx.close();
