// Sinais do MEMX/USDT (M1) em papel + Telegram: mesma regra do IDX (4+ velas iguais, só sinais FORTES: força >= 4,9 ATR14).
// Lê candles por REST 1x por minuto (poucos segundos antes do fechamento da vela); não envia ordens. Config em dados/memx.json; registro em dados/forward_memx.json.
import fs from 'node:fs';
import { noiteAtiva } from './noite.mjs';
const MIN = 60_000, LOG = 'dados/forward_memx.json', LOGC = 'dados/forward_memx_comum.json', CFG = 'dados/memx.json';
export function startMemx(live, send, fmtSinal, fmtAtencao) {
  const cfg = () => { const base = { symbol: 'MEMXUSDT', nome: 'MEMX/USDT', stake: 20, horas: [[480, 1321]], payout: 0.96, leadSec: 15, forcaMin: 4.9, atencaoMin: 4.0, desde: 0 };
    try { return { ...base, ...JSON.parse(fs.readFileSync(CFG, 'utf8')) }; } catch { return base; } };
  let trades = []; try { trades = JSON.parse(fs.readFileSync(LOG, 'utf8')).trades ?? []; } catch {}
  const save = () => fs.writeFileSync(LOG, JSON.stringify({ trades }, null, 1));
  let comuns = []; try { comuns = JSON.parse(fs.readFileSync(LOGC, 'utf8')).trades ?? []; } catch {}
  const saveC = () => fs.writeFileSync(LOGC, JSON.stringify({ trades: comuns }, null, 1));
  const done = new Set(trades.map(t => t.sigT)), doneC = new Set(comuns.map(t => t.sigT)), alertado = new Set(); let checked = 0, info = null, velasVivas = null, pollAt = 0;
  const url = (sym, a, b) => `https://api.ebinex.com/dataProvider/aggregatedTrades?symbol=${sym}&candleTimeFrame=M1&from=${a}&to=${b}&limit=40`;
  const dentro0 = (ms, hs) => { const d = new Date(ms), m = d.getHours() * 60 + d.getMinutes(); return hs.some(([a, b]) => m >= a && m < b); };
  const dentro = (ms, hs) => dentro0(ms, hs) || noiteAtiva(ms);
  const cor = x => x.c > x.o ? 1 : x.c < x.o ? -1 : 0;
  async function check(B) {                                   // B = fim da vela atual (= abertura da vela de entrada)
    const c = cfg(); const j = await live.rest(url(c.symbol, B - 20 * MIN, B + MIN)); if (!Array.isArray(j)) { info = { erro: 'sem resposta', em: Date.now() }; return; }
    const by = new Map(j.map(x => [x.t, x])), cur = by.get(B - MIN); if (!cur) { info = { erro: 'sem a vela atual', em: Date.now() }; return; }
    const X = cor(cur); info = { B, cor: X, em: Date.now() }; if (X === 0 || !dentro(B, c.horas)) return;
    let r = 0; while (by.has(B - (2 + r) * MIN) && cor(by.get(B - (2 + r) * MIN)) === X) r++;            // velas fechadas iguais antes da atual
    const run = r + 1; if (run < 4 && r < 2) return;
    let soma = 0; for (let k = 0; k < 14; k++) { const x = by.get(B - (1 + k) * MIN); if (!x) return; soma += x.h - x.l; }
    const atr = soma / 14, st = by.get(B - (1 + r) * MIN); if (!(atr > 0) || !st) return;
    const forca = +(Math.abs(cur.c - st.o) / atr).toFixed(2); info = { ...info, run, forca };
    if (run >= 4 && forca >= c.forcaMin && !done.has(B - MIN)) {
      done.add(B - MIN); const key0 = (X > 0 ? 'G' : 'R') + (B - run * MIN), semAviso = !alertado.has(key0); alertado.add(key0); const dir = X > 0 ? 'G' : 'R';
      trades.push({ id: B - MIN, sigT: B - MIN, entryT: B, sigAt: Date.now(), dir, run, forca, stake: c.stake, status: 'aberto', ...(dentro0(B, c.horas) ? {} : { noite: true }) }); save();
      send('signal', fmtSinal({ dir, run, entryT: B, stake: c.stake, forca, forte: true, ativo: c.nome, soros: trades.some(t => t.entryT === B - MIN), semAviso, noite: !dentro0(B, c.horas) })).catch(() => {}); return;
    }
    if (run >= 4 && forca < c.forcaMin && !doneC.has(B - MIN)) {   // sinal COMUM (4+ velas, força < 4,9): SEM Telegram, só registro separado (não entra na banca dos fortes)
      doneC.add(B - MIN); const dir = X > 0 ? 'G' : 'R';
      comuns.push({ id: B - MIN, sigT: B - MIN, entryT: B, sigAt: Date.now(), dir, run, forca, stake: c.stake, status: 'aberto' }); saveC();
      return;                                                    // só registra (sem Telegram)
    }
    if (run >= 3 && forca >= c.atencaoMin && forca < c.forcaMin) {   // atenção: a sequência já está forte; a próxima vela pode virar sinal forte
      const key = (X > 0 ? 'G' : 'R') + (B - run * MIN); if (alertado.has(key)) return; alertado.add(key); if (alertado.size > 300) alertado.clear();
      send('pre', fmtAtencao({ X: X > 0 ? 'G' : 'R', r: run, closeAt: B + MIN, leadMs: c.leadSec * 1000, forca, ativo: c.nome })).catch(() => {});
    }
  }
  async function settle(list = trades, sv = save) {
    const c = cfg(), now = Date.now();
    for (const tr of list) if (tr.status === 'aberto' && now > tr.entryT + MIN + 6_000) {
      const j = await live.rest(url(c.symbol, tr.entryT - MIN, tr.entryT + 2 * MIN)); const x = Array.isArray(j) && j.find(y => y.t === tr.entryT);
      if (!x) { if (now > tr.entryT + 5 * MIN) { tr.status = 'sem-dado'; sv(); } continue; }
      tr.entryPrice = x.o; tr.exitPrice = x.c; tr.empate = x.c === x.o; tr.win = tr.dir === 'G' ? x.c > x.o : x.c < x.o;
      tr.pnl = tr.empate ? 0 : tr.win ? +(tr.stake * c.payout).toFixed(2) : -tr.stake; tr.status = 'fechado'; tr.closedAt = now; sv();
    }
  }
  async function poll() {                                      // atualiza as velas do painel (a cada ~10 s, só no horário de operação)
    const c = cfg(), now = Date.now(); const d = new Date(now), mm = d.getHours() * 60 + d.getMinutes(); if (((mm < 470 || mm > 1330) && !noiteAtiva(now + 60_000)) || now - pollAt < 4_000) return; pollAt = now;
    const j = await live.rest(url(c.symbol, (Math.floor(now / MIN) - 16) * MIN, (Math.floor(now / MIN) + 1) * MIN)); if (!Array.isArray(j) || !j.length) return;
    const v = j.sort((a, b) => a.t - b.t).slice(-14), cur = v[v.length - 1]; if (cur.t !== Math.floor(now / MIN) * MIN) { velasVivas = { ...(velasVivas || {}), em: now }; return; }
    const X = cor(cur); let r = 0; while (X !== 0 && v[v.length - 2 - r] && cor(v[v.length - 2 - r]) === X) r++;
    let soma = 0, ok = v.length >= 14; for (const x of v) soma += x.h - x.l; const atr = soma / v.length, st = v[v.length - 1 - r];
    velasVivas = { em: now, velas: v.map(x => ({ t: x.t, k: cor(x) > 0 ? 'G' : cor(x) < 0 ? 'R' : 'D' })), cur: { t: cur.t, o: cur.o, c: cur.c }, run: X === 0 ? 0 : r + 1, forca: X !== 0 && atr > 0 && st ? +(Math.abs(cur.c - st.o) / atr).toFixed(2) : null };
  }
  setInterval(async () => {
    try {
      if (!live.running) return; await poll(); const c = cfg(), now = Date.now(), B = Math.ceil((now + 1) / MIN) * MIN;
      if (now >= B - c.leadSec * 1000 && checked !== B) { checked = B; await check(B); }
      await settle(); await settle(comuns, saveC);
    } catch (e) { console.error('memx:', e.message); }
  }, 1000);
  console.log('Sinais do MEMX/USDT: ligados (Telegram: só fortes; comuns só registrados)');
  return {
    trades: () => trades,
    state() {
      const c = cfg(), P = c.payout, ts = trades.filter(t => t.status === 'fechado'); const d0 = new Date(); d0.setHours(0, 0, 0, 0); const hoje = d0.getTime();
      const mk = soros => { let nivel = 0, prev = null, pw = false; const o = { n: 0, w: 0, pnl: 0, hoje: { n: 0, w: 0, pnl: 0 }, dias: new Map(), linhas: [] };
        for (const t of [...ts].sort((a, b) => a.entryT - b.entryT)) {
          if (!(prev !== null && t.entryT - prev === MIN && pw)) nivel = 0; const stk = soros && nivel === 1 ? t.stake * (1 + P) : t.stake;
          const pnl = t.empate ? 0 : t.win ? stk * P : -stk, k = new Date(t.entryT).toLocaleDateString('sv-SE'), d = o.dias.get(k) ?? { dia: k, n: 0, w: 0, pnl: 0 };
          if (!t.empate) { d.n++; d.w += t.win ? 1 : 0; o.n++; o.w += t.win ? 1 : 0; } d.pnl += pnl; o.dias.set(k, d); o.pnl += pnl;
          if (t.entryT >= hoje) { o.hoje.pnl += pnl; if (!t.empate) { o.hoje.n++; o.hoje.w += t.win ? 1 : 0; } }
          o.linhas.push({ t: t.entryT, dir: t.dir, run: t.run, forca: t.forca, stake: +stk.toFixed(2), res: t.empate ? 'E' : t.win ? 'W' : 'L', pnl: +pnl.toFixed(2) });
          nivel = soros && nivel === 0 && t.win ? 1 : 0; prev = t.entryT; pw = !!t.win && !t.empate; }
        o.pnl = +o.pnl.toFixed(2); o.hoje.pnl = +o.hoje.pnl.toFixed(2); o.dias = [...o.dias.values()].map(d => ({ ...d, pnl: +d.pnl.toFixed(2) })).sort((a, b) => b.dia.localeCompare(a.dia)).slice(0, 15); o.linhas = o.linhas.slice(-30).reverse(); return o; };
      return { cfg: c, info, vivo: velasVivas, abertas: trades.filter(t => t.status === 'aberto').length, entrada: trades.filter(t => t.status === 'aberto').at(-1) ?? null, fixo: mk(false), soros: mk(true) };
    } };
}
