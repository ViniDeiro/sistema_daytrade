// Coleta somente leitura de velas M1 do Crypto IDX da Binomo (endpoint público do gráfico, sem login).
// Uso: node coleta_binomo.mjs <dias>   → grava dados/BINOMO_CRYIDX_candles.json  (t = abertura da vela, em ms)
import fs from 'fs';
const DAYS = +(process.argv[2] || 730), OUT = 'dados/BINOMO_CRYIDX_candles.json', RIC = 'Z-CRY%2FIDX';
const all = new Map(); if (fs.existsSync(OUT)) for (const c of JSON.parse(fs.readFileSync(OUT))) all.set(c.t, c);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const save = () => fs.writeFileSync(OUT, JSON.stringify([...all.values()].sort((a, b) => a.t - b.t)));
const hoje = new Date(); hoje.setUTCHours(0, 0, 0, 0);
let falhas = 0;
for (let d = DAYS; d >= 0; d--) {
  const dia = new Date(hoje.getTime() - d * 86400_000), iso = dia.toISOString().slice(0, 19);
  const temDia = [...Array(24)].every((_, h) => all.has(dia.getTime() + h * 3600_000)) && d > 1;
  if (temDia) continue;
  let ok = false;
  for (let tent = 0; tent < 3 && !ok; tent++) {
    try {
      const r = await fetch(`https://api.binomo.com/candles/v1/${RIC}/${iso}/60?locale=br`, { headers: { 'User-Agent': 'Mozilla/5.0' } });
      if (r.ok) { const j = await r.json(); for (const c of j.data || []) { const t = Date.parse(c.created_at) - 60_000; all.set(t, { t, o: c.open, h: c.high, l: c.low, c: c.close }); } ok = true; }
      else await sleep(5000);
    } catch { await sleep(5000); }
  }
  if (!ok) falhas++;
  if (d % 30 === 0) { save(); console.log(iso.slice(0, 10), 'velas:', all.size); }
  await sleep(1000);
}
save();
const c = [...all.values()].sort((a, b) => a.t - b.t);
console.log({ velas: c.length, falhas, de: new Date(c[0].t).toLocaleString('pt-BR'), ate: new Date(c.at(-1).t).toLocaleString('pt-BR') });
