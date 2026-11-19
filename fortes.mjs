// Aba principal: SINAIS FORTES (IDX + MEMX), gestão Soros nível 1 (base $20) e a versão fixa (secundária). Tudo em papel, derivado dos registros.
import fs from 'node:fs';
const MIN = 60_000;
export function calcFortes(idxTrades, memxTrades, { payout = 0.96, ativoPayout = {} } = {}) {
  let cfg = { desde: 0, bank0: 253.61, stake: 20 }; try { cfg = { ...cfg, ...JSON.parse(fs.readFileSync('dados/forte.json', 'utf8')) }; } catch {}
  const hojeKey = new Date().toLocaleDateString('sv-SE');
  const fonte = [['IDX', idxTrades.filter(t => t.status === 'fechado' && t.forte === true)], ['MEMX', memxTrades.filter(t => t.status === 'fechado')]];
  const mk = (soros, inv = false) => {
    const o = { n: 0, w: 0, pnl: 0, hoje: { n: 0, w: 0, pnl: 0 }, dias: new Map(), linhas: [], ativos: { IDX: { n: 0, w: 0, pnl: 0 }, MEMX: { n: 0, w: 0, pnl: 0 } } };
    for (const [nome, L] of fonte) {
      let nivel = 0, prev = null, pw = false;
      for (const t0 of [...L].sort((a, b) => a.entryT - b.entryT)) {
        const t = inv ? { ...t0, win: t0.empate ? t0.win : !t0.win, dir: t0.dir === 'G' ? 'R' : 'G' } : t0;   // aba "inverso": opera o contrário do sinal (papel)
        if (!(prev !== null && t.entryT - prev === MIN && pw)) nivel = 0;
        const manual = soros ? cfg.stakeReal?.[t.entryT] : undefined, stk = manual ?? (soros && nivel === 1 ? cfg.stake * (1 + payout) : cfg.stake), pnl = t.empate ? 0 : t.win ? stk * payout : -stk;
        const k = new Date(t.entryT).toLocaleDateString('sv-SE');
        if (t.entryT >= cfg.desde) {
          o.pnl += pnl; if (!t.empate) { o.n++; o.w += t.win ? 1 : 0; o.ativos[nome].n++; o.ativos[nome].w += t.win ? 1 : 0; } o.ativos[nome].pnl += pnl;
          const d = o.dias.get(k) ?? { dia: k, n: 0, w: 0, pnl: 0 }; if (!t.empate) { d.n++; d.w += t.win ? 1 : 0; } d.pnl += pnl; o.dias.set(k, d);
          if (k === hojeKey) { o.hoje.pnl += pnl; if (!t.empate) { o.hoje.n++; o.hoje.w += t.win ? 1 : 0; } }
          o.linhas.push({ t: t.entryT, ativo: nome, dir: t.dir, run: t.run, forca: t.forca ?? null, stake: +stk.toFixed(2), manual: manual !== undefined, rec: !!t.recuperada, res: t.empate ? 'E' : t.win ? 'W' : 'L', pnl: +pnl.toFixed(2) });
        }
        nivel = soros && nivel === 0 && t.win ? 1 : 0; prev = t.entryT; pw = !!t.win && !t.empate;
      }
    }
    o.pnl = +o.pnl.toFixed(2); o.hoje.pnl = +o.hoje.pnl.toFixed(2); o.banca = +(cfg.bank0 + o.pnl).toFixed(2);
    for (const a of Object.values(o.ativos)) a.pnl = +a.pnl.toFixed(2);
    o.dias = [...o.dias.values()].map(d => ({ ...d, pnl: +d.pnl.toFixed(2) })).sort((a, b) => b.dia.localeCompare(a.dia)).slice(0, 15);
    o.linhas = o.linhas.sort((a, b) => b.t - a.t).slice(0, 30); return o;
  };
  return { cfg, soros: mk(true), fixo: mk(false), inverso: mk(false, true) };
}
