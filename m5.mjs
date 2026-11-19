// IDX/USDT M5 · "extremo" (PAPEL). Regra achada no histórico (24 meses de IDX): vela de 5 min com força >= 4,9 x ATR14(M5) e preço
// fechando na máxima (verde) ou na mínima (vermelha) -> a PRÓXIMA vela de 5 min continua na mesma cor (62,6% no histórico, estado 1 min antes de fechar).
// Somente leitura: registra operações de papel e avisa no Telegram marcado como PAPEL. Nunca opera.
import fs from 'fs';
const MIN = 60_000, M5 = 5 * MIN, LOG = 'dados/forward_m5.json', SYM = 'IDXUSDT', FORCA = 4.9, CHECK_MS = 240_000, P = 0.96;
export function startM5(live, send) {
  let trades = []; try { trades = JSON.parse(fs.readFileSync(LOG, 'utf8')).trades ?? []; } catch {}
  const save = () => fs.writeFileSync(LOG, JSON.stringify({ trades }, null, 1));
  const done = new Set(trades.map(t => t.sigT)); let info = null;
  const url = (a, b) => `https://api.ebinex.com/dataProvider/aggregatedTrades?symbol=${SYM}&candleTimeFrame=M5&from=${a}&to=${b}&limit=40`;
  const cor = x => x.c > x.o ? 1 : x.c < x.o ? -1 : 0;
  const hm = ms => new Date(ms).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  async function check(S) {                       // S = início da vela M5 atual; roda ~1 min antes de ela fechar
    const j = await live.rest(url(S - 20 * M5, S + M5)); if (!Array.isArray(j)) { info = { erro: 'sem resposta', em: Date.now() }; return; }
    const by = new Map(j.map(x => [x.t, x])), cur = by.get(S); if (!cur) { info = { erro: 'sem a vela atual', em: Date.now() }; return; }
    const X = cor(cur); info = { S, em: Date.now(), cor: X }; if (X === 0 || !(cur.h > cur.l)) return;
    let r = 0; while (by.has(S - (1 + r) * M5) && cor(by.get(S - (1 + r) * M5)) === X) r++;
    const run = r + 1; let soma = 0; for (let k = 1; k <= 14; k++) { const x = by.get(S - k * M5); if (!x) return; soma += x.h - x.l; }
    const atr = soma / 14, st = by.get(S - r * M5) ?? cur; if (!(atr > 0)) return;
    const forca = +(Math.abs(cur.c - (r ? st.o : cur.o)) / atr).toFixed(2), ext = X > 0 ? cur.c === cur.h : cur.c === cur.l;
    info = { ...info, run, forca, ext };
    if (forca >= FORCA && ext && !done.has(S)) {
      done.add(S); const dir = X > 0 ? 'G' : 'R', entryT = S + M5;
      trades.push({ id: S, sigT: S, entryT, sigAt: Date.now(), dir, run, forca, stake: 20, status: 'aberto' }); save();
      const h = new Date(entryT).getHours(); if (h >= 8 && h < 22)
        send('signal', `🧪 <b>PAPEL · IDX/USDT · M5</b>\n<b>${dir === 'G' ? '▲ COMPRA' : '▼ VENDA'}</b> na vela de 5 min das <b>${hm(entryT)}</b>\n${run}ª vela ${dir === 'G' ? 'verde' : 'vermelha'} · força ${forca} · preço no ${dir === 'G' ? 'topo' : 'fundo'} da vela\n<i>Estratégia em teste (papel). Não operar com dinheiro real.</i>`).catch(() => {});
    }
  }
  async function settle() {
    const ab = trades.filter(t => t.status === 'aberto' && Date.now() > t.entryT + M5 + 6000); if (!ab.length) return;
    const j = await live.rest(url(ab[0].entryT - M5, Date.now() + M5)); if (!Array.isArray(j)) return; const by = new Map(j.map(x => [x.t, x]));
    for (const t of ab) { const c = by.get(t.entryT); if (!c) { if (Date.now() > t.entryT + 3 * M5) { t.status = 'sem-dado'; save(); } continue; }
      t.entryPrice = c.o; t.exitPrice = c.c; t.empate = c.c === c.o; t.win = !t.empate && (t.dir === 'G' ? c.c > c.o : c.c < c.o); t.pnl = t.empate ? 0 : t.win ? t.stake * P : -t.stake; t.status = 'fechado'; t.closedAt = Date.now(); save(); }
  }
  let checked = 0;
  setInterval(async () => { try {
    if (!live.running) return; const now = Date.now(), S = Math.floor(now / M5) * M5;
    if (now - S >= CHECK_MS && now - S < CHECK_MS + 40_000 && checked !== S) { checked = S; await check(S); }
    await settle();
  } catch (e) { console.error('m5:', e.message); } }, 1000);
  console.log('IDX M5 extremo (papel): ligado');
  return { trades: () => trades, state() {
    const ts = trades.filter(t => t.status === 'fechado'), w = ts.filter(t => !t.empate), o = { n: w.length, w: w.filter(t => t.win).length, pnl: +ts.reduce((a, t) => a + (t.pnl || 0), 0).toFixed(2) };
    return { ...o, abertas: trades.filter(t => t.status === 'aberto').length, info, linhas: [...trades].reverse().slice(0, 30) }; } };
}
