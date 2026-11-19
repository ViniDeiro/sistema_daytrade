// Coleta velas de 5 segundos do Crypto IDX da Binomo (endpoint público, sem login), para testar retração dentro da vela M1.
// Uso: node coleta_binomo5s.mjs <dias>   → dados/BINOMO_CRYIDX_5s.json  ([t, o, h, l, c], t = início da vela de 5s em ms)
// Retoma de onde parou; 1 pedido por segundo.
import fs from 'fs';
const DIAS = +(process.argv[2] || 60), OUT = 'dados/BINOMO_CRYIDX_5s.json', H = 3_600_000;
let V = []; try { V = JSON.parse(fs.readFileSync(OUT)); } catch {}
const tem = new Set(V.map(v => Math.floor(v[0] / H) * H));
const fim = Math.floor(Date.now() / H) * H - H, ini = fim - DIAS * 24 * H;
let n = 0, novos = 0;
for (let h = ini; h <= fim; h += H) {
  if (tem.has(h)) continue;
  const iso = new Date(h).toISOString().slice(0, 19);
  try {
    const r = await fetch(`https://api.binomo.com/candles/v1/Z-CRY%2FIDX/${iso}/5?locale=br`);
    if (r.ok) { const d = (await r.json()).data ?? []; for (const c of d) { V.push([Date.parse(c.created_at) - 5000, c.open, c.high, c.low, c.close]); novos++; } }
    else console.log(iso, 'HTTP', r.status);
  } catch (e) { console.log(iso, 'erro', e.message); }
  if (++n % 48 === 0) { fs.writeFileSync(OUT, JSON.stringify(V)); console.log(new Date(h).toLocaleString('pt-BR'), 'velas', V.length); }
  await new Promise(r => setTimeout(r, 1000));
}
V = [...new Map(V.map(v => [v[0], v])).values()].sort((a, b) => a[0] - b[0]);
fs.writeFileSync(OUT, JSON.stringify(V)); console.log('fim', V.length, 'velas de 5s, novas', novos);
