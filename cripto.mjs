// Sinais de CRIPTO M15 (papel + Telegram): depois de 3 velas M15 verdes seguidas, a próxima vela tende a ser vermelha -> VENDA.
// Só lê candles (REST) e registra; não envia ordens. Configuração em dados/cripto.json. Registro em dados/forward_cripto.json.
import fs from 'node:fs';
const MIN = 60_000, M15 = 15 * MIN, LOG = 'dados/forward_cripto.json', CFG = 'dados/cripto.json';
const NOME = { ETHUSDT: 'ETH/USDT', XRPUSDT: 'XRP/USDT', BTCUSDT: 'BTC/USDT', SOLUSDT: 'SOL/USDT', DOGEUSDT: 'DOGE/USDT', BNBUSDT: 'BNB/USDT' };
const hm = ms => new Date(ms).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
export function startCripto(live, send, fmtSinal) {
  const cfg = () => { try { return { assets: ['ETHUSDT', 'XRPUSDT'], stake: 20, horas: [[480, 1320]], K: 3, leadSec: 20, payout: 0.90, desde: 0, bank0: 0, ...JSON.parse(fs.readFileSync(CFG, 'utf8')) }; } catch { return { assets: [], stake: 20, horas: [[480, 1320]], K: 3, leadSec: 20, payout: 0.9, desde: 0, bank0: 0 }; } };
  let trades = []; try { trades = JSON.parse(fs.readFileSync(LOG, 'utf8')).trades ?? []; } catch {}
  const save = () => fs.writeFileSync(LOG, JSON.stringify({ trades }, null, 1));
  const done = new Set(trades.map(t => t.asset + t.sigT)); const info = {}; let checked = 0;
  const url = (sym, a, b) => `https://api.ebinex.com/dataProvider/aggregatedTrades?symbol=${sym}&candleTimeFrame=M15&from=${a}&to=${b}&limit=20`;
  const dentro = (ms, hs) => { const d = new Date(ms), m = d.getHours() * 60 + d.getMinutes(); return hs.some(([a, b]) => m >= a && m < b); };
  async function check(B) {                                  // B = fim da vela M15 atual (= abertura da próxima, a entrada)
    const c = cfg();
    for (const sym of c.assets) {
      const j = await live.rest(url(sym, B - (c.K + 1) * M15, B + MIN)); if (!Array.isArray(j)) { info[sym] = { erro: 'sem resposta', em: Date.now() }; continue; }
      const by = new Map(j.map(x => [x.t, x])), seq = []; for (let k = c.K; k >= 1; k--) { const x = by.get(B - k * M15); seq.push(x ? Math.sign(x.c - x.o) : null); }
      info[sym] = { B, seq, em: Date.now() };
      if (seq.every(v => v === 1) && !done.has(sym + B) && dentro(B, c.horas)) {
        done.add(sym + B); const tr = { id: sym + B, asset: sym, sigT: B, entryT: B, sigAt: Date.now(), dir: 'R', K: c.K, stake: c.stake, status: 'aberto' };
        trades.push(tr); save(); send('signal', fmtSinal({ pair: NOME[sym] || sym, entryT: B, stake: c.stake, K: c.K, leadSec: c.leadSec })).catch(() => {});
      }
    }
  }
  async function settle() {
    const c = cfg(), now = Date.now();
    for (const tr of trades) if (tr.status === 'aberto' && now > tr.entryT + M15 + 8_000) {
      const j = await live.rest(url(tr.asset, tr.entryT - MIN, tr.entryT + M15 + MIN)); const x = Array.isArray(j) && j.find(y => y.t === tr.entryT); if (!x) { if (now > tr.entryT + 3 * M15) { tr.status = 'sem-dado'; save(); } continue; }
      tr.entryPrice = x.o; tr.exitPrice = x.c; tr.empate = x.c === x.o; tr.win = x.c < x.o;               // venda ganha se a vela fechar vermelha
      tr.pnl = tr.empate ? 0 : tr.win ? +(tr.stake * c.payout).toFixed(2) : -tr.stake; tr.status = 'fechado'; tr.closedAt = now; save();
    }
  }
  setInterval(async () => {
    try {
      if (!live.running) return; const c = cfg(), now = Date.now(), B = Math.ceil((now + 1) / M15) * M15;
      if (now >= B - c.leadSec * 1000 && checked !== B) { checked = B; await check(B); }
      await settle();
    } catch (e) { console.error('cripto:', e.message); }
  }, 1000);
  console.log('Sinais de cripto M15: ligados (ETH e XRP por padrão)');
  return {
    state() {
      const c = cfg(), fechados = trades.filter(t => t.status === 'fechado'), dec = fechados.filter(t => !t.empate), d0 = new Date(); d0.setHours(0, 0, 0, 0);
      const pnl = fechados.filter(t => t.entryT >= c.desde).reduce((a, t) => a + t.pnl, 0), hoje = fechados.filter(t => t.entryT >= d0.getTime());
      const dias = new Map(); for (const t of fechados) { const k = new Date(t.entryT).toLocaleDateString('sv-SE'); const o = dias.get(k) ?? { dia: k, n: 0, w: 0, pnl: 0 }; if (!t.empate) { o.n++; o.w += t.win ? 1 : 0; } o.pnl += t.pnl; dias.set(k, o); }
      return { cfg: c, info, banca: +(c.bank0 + pnl).toFixed(2), pnl: +pnl.toFixed(2), n: dec.length, wins: dec.filter(t => t.win).length, abertas: trades.filter(t => t.status === 'aberto').length,
        hoje: { n: hoje.filter(t => !t.empate).length, wins: hoje.filter(t => t.win).length, pnl: +hoje.reduce((a, t) => a + t.pnl, 0).toFixed(2) },
        dias: [...dias.values()].map(o => ({ ...o, pnl: +o.pnl.toFixed(2) })).sort((a, b) => b.dia.localeCompare(a.dia)).slice(0, 15),
        linhas: trades.slice(-30).reverse().map(t => ({ t: t.entryT, asset: t.asset, status: t.status, win: t.win, empate: t.empate, pnl: t.pnl, stake: t.stake })) };
    } };
}
