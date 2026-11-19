// Forward test AO VIVO (somente leitura): lê as velas M1 do IDX/USDT pelo feed do gráfico, aplica a regra
// "N velas iguais -> a próxima repete" a LEAD segundos antes do fim da vela e registra operações de PAPEL
// (banca virtual). Não envia ordens. Cada operação fica em dados/forward_log.json.
import { chromium } from 'playwright';
import fs from 'fs';
import { noiteAtiva } from './noite.mjs';

const MIN = 60_000, LOG = 'dados/forward_log.json', FORCA_MIN = 4.9, ATENCAO_MIN = 4.0;
const colorOf = c => (c.c > c.o ? 'G' : c.c < c.o ? 'R' : 'D');


// 4 bancas de papel calculadas em cima do registro de operações (nenhuma envia ordens): fixo, Soros, Soros + stop win e fixo + stop win.
const BANCAS = [{ id: 'fixo', nome: 'Fixo $40', soros: false, stopWin: null }, { id: 'soros', nome: 'Soros 40/78,40', soros: true, stopWin: null },
  { id: 'soros500', nome: 'Soros + stop win $500', soros: true, stopWin: 500 },
  { id: 'soros500l400', nome: 'Soros + stop win $500 + stop loss $400', soros: true, stopWin: 500, stopLoss: 400 }, { id: 'fixo500', nome: 'Fixo + stop win $500', soros: false, stopWin: 500 },
  { id: 'forte', nome: 'Fixo $40, só sinais fortes (≥4,9 ATR)', soros: false, stopWin: null, soForte: true },
  { id: 'forteSoros', nome: 'Soros, só sinais fortes (≥4,9 ATR)', soros: true, stopWin: null, soForte: true },
  { id: 'janela', nome: 'Fixo, só 10h–15h e 18h–22h', soros: false, stopWin: null, horas: [[600, 900], [1080, 1320]] }];
function calcBancas(done, { stake, payout, desde, bank0 }) {
  const ts = [...done].sort((a, b) => a.entryT - b.entryT), hojeKey = new Date().toLocaleDateString('sv-SE');
  return BANCAS.map(v => {
    let dia = null, dayPnl = 0, parado = false, nivel = 0, prevT = null, prevWin = false;
    const r = { id: v.id, nome: v.nome, stopWin: v.stopWin, stopLoss: v.stopLoss ?? null, motivoHoje: null, hoje: 0, hojeN: 0, hojeIgn: 0, paradoHoje: false, desde: 0, desdeN: 0, total: 0, piorDia: 0, diasParados: 0 };
    const dias = new Map();
    for (const t of ts) {
      const k = new Date(t.entryT).toLocaleDateString('sv-SE');
      if (k !== dia) { dia = k; dayPnl = 0; parado = false; nivel = 0; prevT = null; prevWin = false; }
      if (v.soForte && t.forte !== true) continue;
      if (v.horas) { const dt = new Date(t.entryT), m = dt.getHours() * 60 + dt.getMinutes(); if (!v.horas.some(([a, b]) => m >= a && m < b)) continue; }
      if (parado) { if (k === hojeKey) r.hojeIgn++; continue; }
      if (!(prevT !== null && t.entryT - prevT === MIN && prevWin)) nivel = 0;
      const stk = v.soros && nivel === 1 ? stake * (1 + payout) : stake;
      const pnl = t.empate ? 0 : t.win ? stk * payout : -stk;
      dayPnl += pnl; dias.set(k, dayPnl); r.total += pnl;
      if (t.entryT >= desde) { r.desde += pnl; r.desdeN++; }
      if (k === hojeKey) { r.hoje += pnl; r.hojeN++; }
      nivel = v.soros && nivel === 0 && t.win ? 1 : 0; prevT = t.entryT; prevWin = !!t.win && !t.empate;
      if ((v.stopWin && dayPnl >= v.stopWin) || (v.stopLoss && dayPnl <= -v.stopLoss)) { parado = true; r.diasParados++; if (k === hojeKey) { r.paradoHoje = true; r.motivoHoje = dayPnl > 0 ? 'win' : 'loss'; } }
    }
    r.piorDia = dias.size ? Math.min(...dias.values()) : 0;
    for (const x of ['hoje', 'desde', 'total', 'piorDia']) r[x] = +r[x].toFixed(2);
    r.banca = +(bank0 + r.desde).toFixed(2);
    return r;
  });
}

// Aba "Contra": só a 1ª entrada de cada sequência (depois de 4 velas iguais), apostando na cor OPOSTA, valor fixo e sem gale.
function calcContra(done, { desde, bank0, stake, payout }) {
  const ts = [...done].sort((a, b) => a.entryT - b.entryT), hojeKey = new Date().toLocaleDateString('sv-SE');
  const mk = gale => {
    let nivel = 0, prevT = null, prevLoss = false;
    const o = { n: 0, w: 0, e: 0, pnl: 0, iniN: 0, iniW: 0, galeN: 0, galeW: 0, hoje: { n: 0, w: 0, pnl: 0 }, total: { n: 0, w: 0, pnl: 0 }, dias: new Map(), linhas: [] };
    for (const t of ts) {
      if (!(prevT !== null && t.entryT - prevT === MIN && prevLoss)) nivel = 0;
      const emGale = gale && nivel === 1, stk = emGale ? stake * 2 : stake;
      if (t.run !== 4 && !emGale) { nivel = 0; prevT = null; prevLoss = false; continue; }      // só a 1ª entrada (depois de 4 velas); a 5ª só entra como gale
      const venceu = !t.empate && !t.win, pnl = t.empate ? 0 : venceu ? stk * payout : -stk, k = new Date(t.entryT).toLocaleDateString('sv-SE');
      const d = o.dias.get(k) ?? { dia: k, n: 0, w: 0, pnl: 0 }; if (!t.empate) { d.n++; d.w += venceu ? 1 : 0; } d.pnl += pnl; o.dias.set(k, d);
      o.total.pnl += pnl; if (!t.empate) { o.total.n++; o.total.w += venceu ? 1 : 0; }
      if (t.entryT >= desde) {
        o.pnl += pnl; if (t.empate) o.e++; else { o.n++; o.w += venceu ? 1 : 0; if (emGale) { o.galeN++; o.galeW += venceu ? 1 : 0; } else { o.iniN++; o.iniW += venceu ? 1 : 0; } }
        if (k === hojeKey) { o.hoje.pnl += pnl; if (!t.empate) { o.hoje.n++; o.hoje.w += venceu ? 1 : 0; } }
      }
      o.linhas.push({ t: t.entryT, dir: t.dir === 'G' ? 'R' : 'G', run: t.run, gale: emGale, stake: stk, res: t.empate ? 'E' : venceu ? 'W' : 'L', pnl: +pnl.toFixed(2) });
      nivel = gale && nivel === 0 && !t.empate && !venceu ? 1 : 0; prevT = t.entryT; prevLoss = !t.empate && !venceu;
    }
    for (const x of ['pnl']) o[x] = +o[x].toFixed(2); o.hoje.pnl = +o.hoje.pnl.toFixed(2); o.total.pnl = +o.total.pnl.toFixed(2);
    o.banca = +(bank0 + o.pnl).toFixed(2); o.dias = [...o.dias.values()].map(d => ({ ...d, pnl: +d.pnl.toFixed(2) })).sort((a, b) => b.dia.localeCompare(a.dia)).slice(0, 15);
    o.linhas = o.linhas.filter(l => l.t >= desde).slice(-30).reverse(); return o;
  };
  return { desde, bank0, stake, semGale: mk(false) };
}

// Aba "Janela": entradas normais (mesmos sinais da estratégia atual), valor fixo, só dentro das janelas de horário.
function calcJanela(done, { desde, bank0, stake, horas, payout }) {
  const ts = [...done].filter(t => { const d = new Date(t.entryT), m = d.getHours() * 60 + d.getMinutes(); return horas.some(([a, b]) => m >= a && m < b); }).sort((a, b) => a.entryT - b.entryT);
  const hojeKey = new Date().toLocaleDateString('sv-SE'), o = { n: 0, w: 0, e: 0, pnl: 0, hoje: { n: 0, w: 0, pnl: 0 }, total: { n: 0, w: 0, pnl: 0 }, dias: new Map(), linhas: [] };
  for (const t of ts) {
    const pnl = t.empate ? 0 : t.win ? stake * payout : -stake, k = new Date(t.entryT).toLocaleDateString('sv-SE');
    const d = o.dias.get(k) ?? { dia: k, n: 0, w: 0, pnl: 0 }; if (!t.empate) { d.n++; d.w += t.win ? 1 : 0; } d.pnl += pnl; o.dias.set(k, d);
    o.total.pnl += pnl; if (!t.empate) { o.total.n++; o.total.w += t.win ? 1 : 0; }
    if (t.entryT >= desde) {
      o.pnl += pnl; if (t.empate) o.e++; else { o.n++; o.w += t.win ? 1 : 0; }
      if (k === hojeKey) { o.hoje.pnl += pnl; if (!t.empate) { o.hoje.n++; o.hoje.w += t.win ? 1 : 0; } }
      o.linhas.push({ t: t.entryT, dir: t.dir, run: t.run, res: t.empate ? 'E' : t.win ? 'W' : 'L', pnl: +pnl.toFixed(2) });
    }
  }
  o.pnl = +o.pnl.toFixed(2); o.hoje.pnl = +o.hoje.pnl.toFixed(2); o.total.pnl = +o.total.pnl.toFixed(2); o.banca = +(bank0 + o.pnl).toFixed(2);
  o.dias = [...o.dias.values()].map(d => ({ ...d, pnl: +d.pnl.toFixed(2) })).sort((a, b) => b.dia.localeCompare(a.dia)).slice(0, 15); o.linhas = o.linhas.slice(-30).reverse();
  return { desde, bank0, stake, horas, ...o };
}

export function createLive({ profile = './profile', stake = 20, bank0 = 2000, hours = [8, 22], minRun = 3, payout = 0.96, leadMs = 7000, preAlert = true, notify = async () => {} } = {}) {
  let ctx = null, page = null, headers = null, timer = null, watchdog = null, preTimer = null;
  const S = { on: false, starting: false, connected: false, warn: null, lastFrame: null, cur: null, offset: 0, signal: null, trades: [] };
  const closed = new Map();                       // t -> vela fechada {t,o,h,l,c}
  const evaluated = new Set();
  const offs = [];
  try { S.trades = JSON.parse(fs.readFileSync(LOG, 'utf8')).trades ?? []; } catch {}
  const save = () => fs.writeFileSync(LOG, JSON.stringify({ stake, bank0, trades: S.trades }, null, 1));
  let baseT = 0; try { baseT = JSON.parse(fs.readFileSync('dados/baseline.json', 'utf8')).t || 0; } catch {}   // início da contagem das "entradas novas"
  const nowSrv = () => Date.now() + S.offset;      // relógio alinhado ao do servidor da Ebinex

  function onCandle(p, srvTs) {
    S.lastFrame = Date.now(); S.connected = true; S.warn = null;
    if (srvTs) { offs.push(srvTs - Date.now()); if (offs.length > 30) offs.shift(); S.offset = Math.max(...offs); }
    if (!S.cur || p.t === S.cur.t) { S.cur = S.cur ? { ...p, o: S.cur.o } : p; return; }
    if (p.t < S.cur.t) return;
    const fin = { ...S.cur, c: p.o };              // a abertura da vela nova == fechamento da anterior (verificado nos dados)
    if (p.t - S.cur.t === MIN) closed.set(fin.t, fin);
    else if (p.t - S.cur.t > MIN) fillGap(S.cur.t, p.t);                    // o feed pulou minuto(s): busca as velas que faltam no histórico
    S.cur = p;
    try { preFor(S.cur.t); } catch {}
    for (const tr of S.trades) if (tr.status === 'aberto' && tr.entryT === p.t) tr.entryPrice = p.o;
    settle(fin);
  }

  const hhmmss = ms => new Date(ms).toLocaleTimeString('pt-BR');
  const preSent = new Set();
  const streakSent = new Set();
  function preFor(startT) {                        // aviso "fique atento": só quando a sequência JÁ fechada tem >= minRun velas e força >= ATENCAO_MIN (pode virar sinal forte na vela que acabou de abrir)
    if (!S.on || !preAlert || preSent.has(startT)) return;
    const eh = new Date(startT).getHours(); if ((eh < hours[0] || eh >= hours[1]) && !noiteAtiva(startT + MIN)) return;
    const prevT = startT - MIN, prev = closed.get(prevT) ?? (S.cur && S.cur.t === prevT ? S.cur : null);   // se o feed ainda não trouxe a vela nova, usa o último preço da anterior
    if (!prev) return;
    const X = colorOf(prev); if (X === 'D') return;
    let r = 1, t = prevT - MIN;
    while (closed.has(t) && colorOf(closed.get(t)) === X) { r++; t -= MIN; }
    if (r < minRun) return;
    const first = closed.get(prevT - (r - 1) * MIN) ?? (r === 1 ? prev : null); if (!first) return;
    let soma = 0; for (let k = 0; k < 14; k++) { const c = k === 0 ? prev : closed.get(prevT - k * MIN); if (!c || c.h === undefined) return; soma += c.h - c.l; }
    const atr = soma / 14; if (!(atr > 0)) return;
    const forca = +(Math.abs(prev.c - first.o) / atr).toFixed(1); if (forca < ATENCAO_MIN) return;
    const key = X + (prevT - (r - 1) * MIN); if (streakSent.has(key)) return;           // um aviso por sequência
    streakSent.add(key); if (streakSent.size > 300) streakSent.clear();
    preSent.add(startT); if (preSent.size > 300) preSent.clear();
    notify('pre', { X, r, closeAt: startT + MIN, leadMs, forca }).catch(() => {});
  }

  let lastGapAt = 0;
  async function fillGap(fromT, toT) {            // completa velas que o feed não enviou (rápido, 1 requisição por buraco)
    if (!ctx || !headers || Date.now() - lastGapAt < 15_000) return; lastGapAt = Date.now();
    try {
      const r = await ctx.request.get(`https://api.ebinex.com/dataProvider/aggregatedTrades?symbol=IDXUSDT&candleTimeFrame=M1&from=${fromT}&to=${toT}&limit=60`, { headers });
      if (!r.ok()) return;
      for (const c of await r.json()) if (c.t >= fromT && c.t < toT) { const cd = { t: c.t, o: c.o, h: c.h, l: c.l, c: c.c }; closed.set(c.t, cd); settle(cd); }
      S.gapsFilled = (S.gapsFilled || 0) + 1;
    } catch {}
  }

  function settle(fin) {
    let changed = false;
    for (const tr of S.trades) {
      if (tr.status !== 'aberto' || tr.entryT !== fin.t) continue;
      const k = colorOf(fin); tr.exitPrice = fin.c; tr.entryPrice ??= fin.o;
      tr.empate = k === 'D';                       // doji: a Ebinex devolve a entrada (empate)
      tr.win = tr.empate ? null : k === tr.dir;
      tr.pnl = tr.empate ? 0 : +(tr.win ? tr.stake * payout : -tr.stake).toFixed(2);
      const sig = closed.get(tr.sigT);             // a vela do sinal fechou na cor esperada?
      tr.sinalConfirmado = sig ? colorOf(sig) === tr.dir : null;
      tr.status = 'fechado'; tr.closedAt = Date.now(); changed = true;
      if (S.signal && S.signal.entryT === tr.entryT) S.signal = null;
    }
    if (changed) save();
  }

  let catchFor = 0;
  async function catchUp(m) {                      // o feed não mandou nenhum quadro do minuto atual (m): busca por REST para não perder o sinal
    if (!ctx || !headers || catchFor === m) return; catchFor = m;
    try {
      const r = await ctx.request.get(`https://api.ebinex.com/dataProvider/aggregatedTrades?symbol=IDXUSDT&candleTimeFrame=M1&from=${S.cur.t}&to=${m + MIN}&limit=60`, { headers });
      if (!r.ok()) return;
      for (const c of (await r.json()).sort((a, b) => a.t - b.t)) {
        const cd = { t: c.t, o: c.o, h: c.h, l: c.l, c: c.c };
        if (c.t < m) { closed.set(c.t, cd); settle(cd); } else if (c.t === m && S.cur && S.cur.t < m) S.cur = cd;
      }
      S.gapsFilled = (S.gapsFilled || 0) + 1;
    } catch {}
  }

  function evaluate() {
    if (!S.on || !S.cur) return;
    const n = nowSrv(), el = n - S.cur.t;
    { const m = Math.floor(n / MIN) * MIN; if (S.cur.t < m && n - m >= 45_000) catchUp(m); }
    S.elapsed = el;
    for (const tr of S.trades)                     // operação sem fechamento por falta de dados
      if (tr.status === 'aberto' && n > tr.entryT + 2 * MIN) { tr.status = 'sem-dado'; save(); if (S.signal?.entryT === tr.entryT) S.signal = null; }
    if (S.signal && n >= S.signal.entryT) S.signal = { ...S.signal, entrou: true };
    if (el < MIN - leadMs || el >= MIN || evaluated.has(S.cur.t)) return;
    evaluated.add(S.cur.t); if (evaluated.size > 500) evaluated.clear();
    const eh = new Date(S.cur.t + MIN), mins = eh.getHours() * 60 + eh.getMinutes();      // minuto do dia da vela de ENTRADA
    const foraBase = mins < hours[0] * 60 || mins > hours[1] * 60; if (foraBase && !noiteAtiva(S.cur.t + MIN)) { S.lastEval = { t: S.cur.t, motivo: 'fora do horário' }; return; }   // aceita entradas de 08:00 até 22:00 (inclusive)
    let t = S.cur.t - MIN, X = null, r = 0;        // sequência de velas FECHADAS iguais antes da atual
    while (closed.has(t)) { const k = colorOf(closed.get(t)); if (k === 'D') break; if (X === null) X = k; if (k !== X) break; r++; t -= MIN; }
    if (r < minRun) { S.lastEval = { t: S.cur.t, motivo: `sequência ${r} (< ${minRun})` }; return; }
    if (colorOf(S.cur) !== X) { S.lastEval = { t: S.cur.t, motivo: `a vela atual não está na cor da sequência (${r} iguais antes)` }; return; }
    let forca = null;                              // força da sequência: movimento da sequência em múltiplos do ATR14 (>= FORCA_MIN = sinal "forte")
    { const cs = [S.cur]; let ok = S.cur.h !== undefined && S.cur.l !== undefined; for (let k = 1; ok && k < 14; k++) { const c = closed.get(S.cur.t - k * MIN); if (!c || c.h === undefined) ok = false; else cs.push(c); }
      const st = closed.get(S.cur.t - r * MIN); if (ok && st) { const atr = cs.reduce((a, c) => a + (c.h - c.l), 0) / 14; if (atr > 0) forca = +(Math.abs(S.cur.c - st.o) / atr).toFixed(2); } }
    const kAv = X + (S.cur.t - r * MIN), semAviso = !streakSent.has(kAv); streakSent.add(kAv);
    const tr = { id: S.cur.t, sigT: S.cur.t, entryT: S.cur.t + MIN, sigAt: Date.now(), dir: X, run: r + 1, stake, status: 'aberto', forca, forte: forca !== null ? forca >= FORCA_MIN : null, ...(foraBase ? { noite: true } : {}) };
    S.trades.push(tr); S.signal = { dir: X, entryT: tr.entryT, run: r + 1, at: Date.now(), forte: tr.forte, forca }; S.lastEval = { t: S.cur.t, motivo: 'SINAL' }; save();
    notify('signal', { dir: X, run: r + 1, entryT: tr.entryT, stake, forca, forte: tr.forte, semAviso, noite: !!tr.noite }).catch(() => {});
  }

  function handle(payload) {
    if (typeof payload !== 'string' || !payload.startsWith('a[')) return;
    let arr; try { arr = JSON.parse(payload.slice(1)); } catch { return; }
    for (const m of arr) {
      if (typeof m !== 'string' || !m.startsWith('MESSAGE')) continue;
      const i = m.indexOf('\n\n'); if (i < 0) continue;
      const head = m.slice(0, i), body = m.slice(i + 2).replace(/\0$/, '');
      if (!/graph\\cIDXUSDT\\cM1/.test(head)) continue;
      try {
        const j = JSON.parse(body);
        if (j.data?.event === 'trade' && j.data.payload?.t) onCandle(j.data.payload, +(/timestamp:(\d+)/.exec(head)?.[1] ?? 0));
      } catch {}
    }
  }

  async function seed() {                          // 1 requisição: últimas ~6h, para já ter a sequência e as grades
    const to = Date.now(), from = to - 6 * 3600_000;
    const r = await ctx.request.get(`https://api.ebinex.com/dataProvider/aggregatedTrades?symbol=IDXUSDT&candleTimeFrame=M1&from=${from}&to=${to}&limit=1500`, { headers });
    if (!r.ok()) throw new Error('histórico HTTP ' + r.status());
    for (const c of await r.json()) if (c.t + MIN <= to - 5000) closed.set(c.t, { t: c.t, o: c.o, h: c.h, l: c.l, c: c.c });
  }

  return {
    get running() { return S.on; },
    setBaseline(ts = Date.now()) { baseT = ts; fs.writeFileSync('dados/baseline.json', JSON.stringify({ t: baseT })); },
    candles: () => [...closed.values()].sort((a, b) => a.t - b.t),
    allTrades: () => S.trades,
    async rest(url) { if (!ctx || !headers) return null; try { const r = await ctx.request.get(url, { headers }); return r.ok() ? await r.json() : null; } catch { return null; } },   // GET autenticado (usado pelo módulo de cripto M15)
    async start() {
      if (S.on || S.starting) return; S.starting = true; S.warn = 'Conectando…';
      try {
        ctx = await chromium.launchPersistentContext(profile, { headless: process.env.HEADLESS !== '0', viewport: { width: 1280, height: 800 } });
        page = ctx.pages()[0] ?? await ctx.newPage();
        page.on('request', r => { if (!headers && r.url().includes('/dataProvider/aggregatedTrades')) headers = r.headers(); });
        page.on('websocket', ws => ws.on('framereceived', f => handle(f.payload)));
        await page.goto('https://app.ebinex.com', { waitUntil: 'domcontentloaded' });
        for (let i = 0; i < 80 && !headers; i++) await page.waitForTimeout(500);
        if (!headers) throw new Error('sessão não carregou — faça login (node login.mjs)');
        await seed();
        for (const tr of S.trades) if ((tr.status === 'aberto' || tr.status === 'sem-dado') && closed.has(tr.entryT)) { tr.status = 'aberto'; settle(closed.get(tr.entryT)); }
        S.on = true; S.startedAt = Date.now();
        timer = setInterval(evaluate, 500);
        preTimer = setInterval(() => { const n = nowSrv(), st = n - (n % MIN); if (n - st >= 1500) { try { preFor(st); } catch {} } }, 500);   // aviso pelo relógio, 1,5s depois da virada do minuto
        watchdog = setInterval(() => { if (S.on && (!S.lastFrame || Date.now() - S.lastFrame > 45_000)) { S.connected = false; S.warn = 'Sem dados do IDX/USDT M1 há 45s — deixe o gráfico IDX/USDT em M1 aberto na janela.'; } }, 5000);
        S.warn = null;
      } catch (e) { S.warn = e.message; await this.stop(); }
      S.starting = false;
    },
    async stop() {
      clearInterval(timer); clearInterval(watchdog); clearInterval(preTimer); S.on = false; S.connected = false; S.signal = null;
      try { await ctx?.close(); } catch {}
      ctx = page = null; headers = null; S.cur = null;
    },
    summary(fromMs = Date.now() - 3600_000, toMs = Date.now()) {   // dados para o relatório do Telegram
      const d0 = new Date(); d0.setHours(0, 0, 0, 0);
      const fechadas = S.trades.filter(t => t.status === 'fechado').sort((a, b) => a.entryT - b.entryT);
      const stat = list => { const dec = list.filter(t => !t.empate); return { n: dec.length, w: dec.filter(t => t.win).length, e: list.length - dec.length, pnl: +list.reduce((a, t) => a + (t.pnl || 0), 0).toFixed(2) }; };
      const hoje = fechadas.filter(t => t.entryT >= d0.getTime());
      let eq = 0, pico = 0, fundo = 0, cur = 0, mx = 0;
      for (const t of hoje) { eq += t.pnl || 0; pico = Math.max(pico, eq); fundo = Math.min(fundo, eq); if (!t.empate) { cur = t.win ? 0 : cur + 1; mx = Math.max(mx, cur); } }
      const dec = hoje.filter(t => !t.empate); let seq = 0, tipo = null;
      for (let i = dec.length - 1; i >= 0; i--) { const k = !!dec[i].win; if (tipo === null) tipo = k; if (k !== tipo) break; seq++; }
      const total = stat(fechadas);
      return { hoje: { ...stat(hoje), pico: +pico.toFixed(2), fundo: +fundo.toFixed(2), maxSeqLoss: mx, seqAtual: seq, seqTipo: tipo },
        janela: stat(fechadas.filter(t => t.entryT >= fromMs && t.entryT < toMs)), total,
        novas: { desde: baseT, ...stat(fechadas.filter(t => t.entryT >= baseT)) },
        bank: +(bank0 + total.pnl).toFixed(2), bank0, stake, dias: new Set(fechadas.filter(t => !t.empate).map(t => new Date(t.entryT).toDateString())).size, hours };
    },
    state() {
      const done = S.trades.filter(t => t.status === 'fechado'), dec = done.filter(t => !t.empate);
      const pnl = done.reduce((a, t) => a + t.pnl, 0);
      const d0 = new Date(); d0.setHours(0, 0, 0, 0);
      const today = dec.filter(t => t.closedAt >= d0.getTime());
      const lastClosed = [...closed.values()].sort((a, b) => a.t - b.t).slice(-12).map(c => ({ t: c.t, k: colorOf(c) }));
      let run = 0, X = null; { let t = S.cur ? S.cur.t - MIN : null; while (t && closed.has(t)) { const k = colorOf(closed.get(t)); if (k === 'D' || (X && k !== X)) break; X = k; run++; t -= MIN; } }
      let vivo = null;                                  // sequência incluindo a vela atual + força em tempo real (mesma conta do sinal)
      if (S.cur && S.cur.h !== undefined) { const kc = colorOf(S.cur); if (kc !== 'D') { let rr = 0, tt = S.cur.t - MIN; while (closed.has(tt) && colorOf(closed.get(tt)) === kc) { rr++; tt -= MIN; }
        const st = closed.get(S.cur.t - rr * MIN) ?? (rr === 0 ? S.cur : null); let soma = S.cur.h - S.cur.l, ok = !!st;
        for (let k = 1; ok && k < 14; k++) { const c = closed.get(S.cur.t - k * MIN); if (!c || c.h === undefined) ok = false; else soma += c.h - c.l; }
        vivo = { run: rr + 1, cor: kc, forca: ok && soma > 0 ? +(Math.abs(S.cur.c - st.o) / (soma / 14)).toFixed(2) : null }; } }
      return {
        vivo, gapsFilled: S.gapsFilled || 0, on: S.on, starting: S.starting, connected: S.connected, warn: S.warn, serverNow: nowSrv(),
        cur: S.cur && { t: S.cur.t, o: S.cur.o, c: S.cur.c, k: colorOf(S.cur) }, elapsed: S.elapsed ?? null, lastClosed, run, runColor: X,
        signal: S.signal, lastEval: S.lastEval ?? null,
        cfg: { stake, bank0, hours, minRun, payout, leadMs },
        bank: +(bank0 + pnl).toFixed(2), pnl: +pnl.toFixed(2),
        novas: (() => { const nv = done.filter(t => t.entryT >= baseT), nd = nv.filter(t => !t.empate); return { desde: baseT, n: nd.length, wins: nd.filter(t => t.win).length, empates: nv.length - nd.length, pnl: +nv.reduce((a, t) => a + (t.pnl || 0), 0).toFixed(2) }; })(),
        diasComDados: new Set(dec.map(t => new Date(t.entryT).toDateString())).size,
        total: { n: dec.length, empates: done.length - dec.length, wins: dec.filter(t => t.win).length, confirmados: done.filter(t => t.sinalConfirmado === true).length },
        today: { n: today.length, wins: today.filter(t => t.win).length, pnl: +done.filter(t => t.closedAt >= d0.getTime()).reduce((a, t) => a + t.pnl, 0).toFixed(2) },
        bancas: (() => { let cfg = { desde: 0, bank0: 1649.61 }; try { cfg = JSON.parse(fs.readFileSync('dados/bancas.json', 'utf8')); } catch {} return { desde: cfg.desde, bank0: cfg.bank0, lista: calcBancas(done, { stake, payout, desde: cfg.desde, bank0: cfg.bank0 }) }; })(),
        contra: (() => { let cfg = { desde: 0, bank0: 624.01, stake: 20 }; try { cfg = JSON.parse(fs.readFileSync('dados/contra.json', 'utf8')); } catch {} return calcContra(done, { ...cfg, payout }); })(),
        janela: (() => { let cfg = { desde: 0, bank0: 545.61, stake: 20, horas: [[600, 900], [1080, 1320]] }; try { cfg = JSON.parse(fs.readFileSync('dados/janela.json', 'utf8')); } catch {} return calcJanela(done, { ...cfg, payout }); })(),
        porDia: (() => { const m = new Map(); for (const t of dec) { const k = new Date(t.entryT).toLocaleDateString('sv-SE'); const o = m.get(k) ?? { dia: k, n: 0, wins: 0, pnl: 0 }; o.n++; o.wins += t.win ? 1 : 0; o.pnl += t.pnl; m.set(k, o); } return [...m.values()].map(o => ({ ...o, pnl: +o.pnl.toFixed(2) })).sort((a, b) => b.dia.localeCompare(a.dia)); })(),
        trades: S.trades.slice(-60).reverse(),
      };
    },
  };
}
