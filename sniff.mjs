// Reconhecimento: abre a Ebinex com perfil persistente e grava o tráfego (WS + XHR) em sniff.log
import { chromium } from 'playwright';
import fs from 'fs';

const ctx = await chromium.launchPersistentContext('./profile', { headless: false, viewport: { width: 1400, height: 900 } });
const page = ctx.pages()[0] ?? await ctx.newPage();
const out = fs.createWriteStream('sniff.log');
const log = (...a) => out.write(a.join(' ') + '\n');

page.on('websocket', ws => {
  log('WS OPEN', ws.url());
  ws.on('framereceived', f => log('WS <-', ws.url().slice(0, 60), String(f.payload).slice(0, 600)));
  ws.on('framesent', f => log('WS ->', ws.url().slice(0, 60), String(f.payload).slice(0, 300)));
});
page.on('response', async r => {
  const u = r.url();
  if (/candle|kline|chart|history|ohlc|bars/i.test(u)) {
    let body = ''; try { body = (await r.text()).slice(0, 600); } catch {}
    log('HTTP', r.status(), u, body);
  }
});

await page.goto('https://app.ebinex.com');
console.log('Navegador aberto. Faça login (conta Demo), abra IDX/USDT em M1 e deixe o gráfico carregar. Gravando em sniff.log por 4 minutos...');
await page.waitForTimeout(240000);
await ctx.close();
