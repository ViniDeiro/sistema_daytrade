// Forward test (paper) da variante "rompimento de resistência após 4+ toques". Só registra; sem Telegram, sem ordens.
// Regra (a mesma do backtest com ATR causal): resistência = máxima das 120 velas anteriores; toques = velas da janela com máxima >= R - 0,3*ATR14 (menos a própria máxima);
// sinal quando a vela FECHA acima de R com >= 4 toques; entrada = abertura da vela seguinte, compra; vence se a vela seguinte fechar verde.
import fs from 'node:fs';
const MIN = 60_000, W = 120, LOG = 'dados/forward_rompimento.json';
export function startRompimento(live, { stake = 30, payout = 0.96 } = {}) {
  let trades = []; try { trades = JSON.parse(fs.readFileSync(LOG, 'utf8')).trades ?? []; } catch {}
  const save = () => fs.writeFileSync(LOG, JSON.stringify({ stake, regra: 'rompe resistência (120 velas) após 4+ toques, compra, ATR causal', trades }, null, 1));
  const seen = new Set(trades.map(t => t.sigT));
  function tick() {
    const cs = live.candles().filter(c => c.c !== undefined), by = new Map(cs.map(c => [c.t, c]));
    for (const tr of trades) if (tr.status === 'aberto') {                       // fecha a operação quando a vela de entrada fechar
      const e = by.get(tr.entryT); if (!e) continue;
      const win = e.c > e.o, emp = e.c === e.o; tr.status = 'fechado'; tr.win = win; tr.empate = emp; tr.pnl = emp ? 0 : win ? +(stake * payout).toFixed(2) : -stake; save();
    }
    for (const c of cs.slice(-8)) {
      if (seen.has(c.t)) continue;
      const win = []; for (let k = 1; k <= W; k++) { const x = by.get(c.t - k * MIN); if (!x || x.h === undefined) { win.length = 0; break; } win.push(x); }
      if (win.length !== W) continue;
      const trs = []; for (let k = 0; k < 14; k++) { const x = by.get(c.t - (k + 1) * MIN), p = by.get(c.t - (k + 2) * MIN); if (!x || !p) { trs.length = 0; break; } trs.push(Math.max(x.h - x.l, Math.abs(x.h - p.c))); }
      if (trs.length !== 14) continue;
      seen.add(c.t);
      const atr = trs.reduce((a, b) => a + b, 0) / 14, R = Math.max(...win.map(x => x.h)), tol = 0.3 * atr;
      const toques = win.filter(x => x.h >= R - tol).length - 1;
      if (c.c > R && toques >= 4) { trades.push({ id: c.t, sigT: c.t, entryT: c.t + MIN, R, toques, dir: 'G', stake, status: 'aberto' }); save(); }
    }
  }
  setInterval(() => { try { tick(); } catch (e) { console.error('rompimento:', e.message); } }, 2000);
  console.log('Forward test do rompimento: ligado (sem alertas)');
}
