// Registro somente leitura das velas de 5 segundos (S5) do IDX e do MEMX. A corretora só guarda ~1 hora de S5,
// então este módulo vai acumulando a cada 15 min para podermos testar, no futuro, regras que usam o estado da vela
// poucos segundos antes de fechar (o que é o que dá para operar de verdade).
import fs from 'fs';
const MIN = 60_000, SYMS = ['IDXUSDT', 'MEMXUSDT'];
export function startSeg(live) {
  const file = s => `dados/seg5_${s}.jsonl`, last = {};
  for (const s of SYMS) { try { const l = fs.readFileSync(file(s), 'utf8').trimEnd().split('\n').pop(); last[s] = l ? JSON.parse(l).t : 0; } catch { last[s] = 0; } }
  async function run() {
    if (!live.running) return;
    for (const s of SYMS) {
      try {
        const to = Date.now(), from = Math.max(to - 50 * MIN, last[s] + 1);
        const j = await live.rest(`https://api.ebinex.com/dataProvider/aggregatedTrades?symbol=${s}&candleTimeFrame=S5&from=${from}&to=${to}&limit=1500`);
        if (!Array.isArray(j) || !j.length) continue;
        const novas = j.filter(x => x.t > last[s]).sort((a, b) => a.t - b.t); if (!novas.length) continue;
        fs.appendFileSync(file(s), novas.map(x => JSON.stringify({ t: x.t, o: x.o, h: x.h, l: x.l, c: x.c, v: x.v })).join('\n') + '\n');
        last[s] = novas.at(-1).t;
      } catch (e) { console.error('seg5:', e.message); }
      await new Promise(r => setTimeout(r, 1500));
    }
  }
  setInterval(run, 15 * MIN); setTimeout(run, 20_000);
  console.log('Registro de velas S5 (IDX, MEMX): ligado');
}
