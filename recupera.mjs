// Recupera sinais FORTES que o ao vivo perdeu (PC dormindo/desligado), refazendo pelas velas já coletadas.
// Uso (com o servidor PARADO): node recupera.mjs "2026-11-14T08:00" "2026-11-14T12:26" [--aplicar]
// Sem --aplicar só mostra. Entradas gravadas com recuperada:true (o painel marca com ↺). Não mexe no que o ao vivo já registrou.
import fs from 'fs';
const [ini, fim] = process.argv.slice(2, 4).map(s => new Date(s + ':00-03:00').getTime()), APLICAR = process.argv.includes('--aplicar');
const MIN = 60_000, FORCA = 4.9, P = 0.96, col = c => c.c > c.o ? 1 : c.c < c.o ? -1 : 0;
const ativos = [
  { nome: 'IDX', velas: 'dados/IDXUSDT_candles.json', log: 'dados/forward_log.json', forte: true },
  { nome: 'MEMX', velas: 'dados/MEMXUSDT_candles.json', log: 'dados/forward_memx.json', forte: false },
];
let tot = { n: 0, w: 0, e: 0, pnl: 0 };
for (const a of ativos) {
  const C = JSON.parse(fs.readFileSync(a.velas)), by = new Map(C.map(c => [c.t, c]));
  const J = JSON.parse(fs.readFileSync(a.log)), trades = J.trades, ja = new Set(trades.map(t => t.entryT));
  const stake = a.nome === 'IDX' ? (J.stake ?? 20) : 20, novos = [];
  for (let B = Math.ceil(ini / MIN) * MIN; B <= fim; B += MIN) {
    const h = new Date(B).getHours(); if (h < 8 || h >= 22) continue;               // só horário oficial (madrugada fica de fora)
    const s = by.get(B - MIN), e = by.get(B); if (!s || !e) continue;
    const X = col(s); if (!X) continue;
    let r = 1; while (by.get(B - (r + 1) * MIN) && col(by.get(B - (r + 1) * MIN)) === X) r++;
    if (r < 4) continue;
    let soma = 0, ok = true; for (let k = 1; k <= 14; k++) { const x = by.get(B - k * MIN); if (!x) { ok = false; break; } soma += x.h - x.l; }
    const st = by.get(B - r * MIN); if (!ok || !st || !(soma > 0)) continue;
    const forca = +(Math.abs(s.c - st.o) / (soma / 14)).toFixed(2); if (forca < FORCA) continue;
    const dir = X > 0 ? 'G' : 'R', nd = col(e), empate = nd === 0, win = !empate && nd === X;
    const pnl = empate ? 0 : win ? +(stake * P).toFixed(2) : -stake;
    const ao_vivo = ja.has(B);
    if (!ao_vivo) novos.push({ id: B - MIN, sigT: B - MIN, entryT: B, dir, run: r, forca, ...(a.forte ? { forte: true } : {}), stake, status: 'fechado', entryPrice: e.o, exitPrice: e.c, empate, win, pnl, recuperada: true });
    console.log(new Date(B).toTimeString().slice(0, 5), a.nome.padEnd(4), dir === 'G' ? 'COMPRA' : 'VENDA ', `${r}ª`, 'força', forca, empate ? '➖ empate' : win ? '✅' : '❌', ao_vivo ? '(já registrada ao vivo)' : '→ recuperada');
  }
  for (const t of novos) { tot.n += t.empate ? 0 : 1; tot.w += t.win ? 1 : 0; tot.e += t.empate ? 1 : 0; }
  if (APLICAR && novos.length) { J.trades = [...trades, ...novos].sort((x, y) => x.entryT - y.entryT); fs.writeFileSync(a.log, JSON.stringify(J, null, 1)); }
  console.log(`${a.nome}: ${novos.length} recuperada(s)${APLICAR ? ' GRAVADAS' : ' (só simulação)'}\n`);
}
console.log('recuperadas no total:', tot);
