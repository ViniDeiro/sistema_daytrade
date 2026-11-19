// Abre a Ebinex com o perfil "profile" (a sessão que o servidor usa). Você faz o login na janela; não grava tráfego nem token.
// Feche a janela quando terminar o login.
import { chromium } from 'playwright';
const ctx = await chromium.launchPersistentContext('./profile', { headless: false, viewport: { width: 1400, height: 900 } });
const page = ctx.pages()[0] ?? await ctx.newPage();
await page.goto('https://app.ebinex.com');
console.log('Faça login na conta DEMO desejada e abra o IDX/USDT em M1. Depois feche a janela.');
await new Promise(res => ctx.on('close', res));
console.log('Sessão salva em ./profile');
