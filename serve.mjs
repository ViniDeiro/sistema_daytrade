// Servidor local do painel: http://localhost:3000  (acompanhamento ao vivo; somente leitura)
import http from 'http';
import fs from 'fs';
import { createLive } from './live.mjs';
import { startRompimento } from './rompimento.mjs';
import { startCripto } from './cripto.mjs';
import { startMemx } from './memx.mjs';
import { startSeg } from './seg.mjs';
import { startM5 } from './m5.mjs';
import { calcFortes } from './fortes.mjs';
import { createNotifier } from './notify.mjs';
import * as M from './mensagens.mjs';
import { noiteAtiva } from './noite.mjs';

const notifier = createNotifier();
const send = (kind, text, opts = {}) => notifier.send(kind, text, { html: true, ...opts });
const live = createLive({ stake: 40, bank0: 3752.01, leadMs: (() => { try { return JSON.parse(fs.readFileSync('dados/alertas.json', 'utf8')).leadSec * 1000; } catch { return notifier.cfg.leadSec * 1000; } })(), preAlert: notifier.cfg.pre,
  notify: (kind, p) => {
    if (kind === 'signal' && p.forte !== true) { console.log(`[sinal comum não enviado] ${p.run}ª vela, força ${p.forca ?? 'n/d'}`); return Promise.resolve(); }   // Telegram: só sinais FORTES (força >= 4,9 ATR); o painel registra todos
    if (kind === 'signal' || kind === 'pre') {                                   // horário dos avisos do IDX (dados/janela.json, campo alertHoras); o painel registra todos
      let hs = [[480, 1321]]; try { hs = JSON.parse(fs.readFileSync('dados/janela.json', 'utf8')).alertHoras ?? hs; } catch {}
      const d = new Date(kind === 'signal' ? p.entryT : p.closeAt), m = d.getHours() * 60 + d.getMinutes();
      const noite = noiteAtiva(d.getTime());
      if (!hs.some(([a, b]) => m >= a && m < b) && !noite) return Promise.resolve();
    }
    if (kind === 'signal') p = { ...p, stake: 20, ativo: 'IDX/USDT', soros: p.forte === true && live.allTrades().some(t => t.entryT === p.entryT - 60_000 && t.forte === true) };
    return send(kind, M[kind](p));                    // o aviso 'atenção' também vibra (antes saía em modo silencioso)
  } });
console.log(notifier.ready ? 'Notificações: Telegram ATIVO' : 'Notificações: desligadas (sem .env com TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID)');

// ---- relatório toda hora cheia (09h às 22h)
let lastReportKey = '';
startRompimento(live);
const memx = startMemx(live, (k, t) => send(k, t), M.signal, M.pre);
startSeg(live);
const m5 = startM5(live, (k, t) => send(k, t));
const cripto = startCripto(live, (t) => send('signal', t), M.criptoSinal);
const reportNow = (h, final) => { const d = new Date(), to = d.getTime(), from = new Date(d); from.setMinutes(0, 0, 0); from.setHours(h - 1); return send('report', M.reportForte(calcFortes(live.allTrades().filter(t => !t.noite), memx.trades().filter(t => !t.noite), { payout: 0.96 }), h, final)); };
setInterval(() => {
  const d = new Date(), h = d.getHours();
  if (!live.running || d.getMinutes() !== 0 || h < 9 || h > 22) return;
  const key = d.toDateString() + '-' + h; if (key === lastReportKey) return; lastReportKey = key;
  reportNow(h, h === 22);
}, 15_000);

// ---- marcos de 100/200/300/500/1000 entradas novas (cada um é enviado uma vez por ponto de partida)
const PONTOS = [100, 200, 300, 500, 1000, 2000, 3000, 4000, 5000];
setInterval(() => {
  if (!live.running) return;
  const S = live.summary(); let mk; try { mk = JSON.parse(fs.readFileSync('dados/marcos.json', 'utf8')); } catch { mk = { desde: 0, enviados: [] }; }
  if (mk.desde !== S.novas.desde) mk = { desde: S.novas.desde, enviados: [] };
  const alvo = [...PONTOS].reverse().find(p => S.novas.n >= p);
  if (alvo && !mk.enviados.includes(alvo)) {
    mk.enviados = PONTOS.filter(p => p <= alvo); fs.writeFileSync('dados/marcos.json', JSON.stringify(mk));
    send('marco', M.marco(S, alvo));
  } else fs.writeFileSync('dados/marcos.json', JSON.stringify(mk));
}, 20_000);

// ---- veredito final da validação: 30/11/2026 às 22h, uma vez só (mesmos limites: >=53% validada · 51–53% fraca · <51% reprovada)
setInterval(() => {
  if (!live.running || new Date() < new Date(2026, 10, 30, 22, 0)) return;
  let f = {}; try { f = JSON.parse(fs.readFileSync('dados/veredito.json', 'utf8')); } catch {}
  if (f.enviado) return; fs.writeFileSync('dados/veredito.json', JSON.stringify({ enviado: true, em: Date.now() }));
  send('marco', M.veredito(live.summary()));
}, 60_000);

// ---- aviso de conexão perdida (só dentro do horário de operação)
let avisadoEm = 0;
setInterval(() => {
  const h = new Date().getHours(); if (!live.running || h < 8 || h >= 22) return;
  const st = live.state();
  if (st.warn && Date.now() - avisadoEm > 30 * 60_000) { avisadoEm = Date.now(); send('aviso', M.aviso({ titulo: 'Sem dados do gráfico', texto: st.warn })); }
  else if (!st.warn && avisadoEm) { avisadoEm = 0; send('aviso', M.restabelecido()); }
}, 30_000);

// ---- gatilhos de banca (plano combinado em dados/CRITERIOS.md): cada um avisa uma única vez
const GATILHOS = [
  { nivel: 1800, titulo: 'Gatilho de banca: abaixo de $1.800', texto: 'Pelo plano combinado: reduzir a entrada para $30.' },
  { nivel: 1200, titulo: 'Gatilho de banca: abaixo de $1.200', texto: 'Pelo plano combinado: reduzir a entrada para $20 (ou parar).' },
  { nivel: 600, titulo: 'Gatilho de banca: abaixo de $600', texto: 'Pelo plano combinado: PARAR e só voltar depois da validação (veredito final em 30/11/2026, com acerto de 53% ou mais).' }];
setInterval(() => {
  const bank = live.state().bank; let g; try { g = JSON.parse(fs.readFileSync('dados/gatilhos.json', 'utf8')); } catch { g = { enviados: [] }; }
  for (const x of GATILHOS) if (bank < x.nivel && !g.enviados.includes(x.nivel)) { g.enviados.push(x.nivel); fs.writeFileSync('dados/gatilhos.json', JSON.stringify(g)); send('aviso', M.aviso({ titulo: x.titulo, texto: `${x.texto} (banca do painel agora: $${Math.round(bank).toLocaleString('pt-BR')})` })); break; }
}, 20_000);

http.createServer(async (req, res) => {
  const json = o => { res.writeHead(200, { 'content-type': 'application/json' }); res.end(JSON.stringify(o)); };
  if (req.url.startsWith('/api/live')) {
    if (req.method === 'POST') {
      const on = new URL(req.url, 'http://x').searchParams.get('on') === '1';
      if (on) { live.start(); console.log('Acompanhamento ao vivo: LIGANDO'); }
      else { await live.stop(); console.log('Acompanhamento ao vivo: DESLIGADO'); }
    }
    return json(live.state());
  }
  if (req.url.startsWith('/api/fortes')) return json({ ...calcFortes(live.allTrades().filter(t => !t.noite), memx.trades().filter(t => !t.noite), { payout: 0.96 }), memx: memx.state().vivo && { ...memx.state().vivo, entrada: memx.state().entrada } });
  if (req.url.startsWith('/api/m5')) return json(m5.state());
  if (req.url.startsWith('/api/memx')) return json(memx.state());
  if (req.url.startsWith('/api/cripto')) return json(cripto.state());
  if (req.url.startsWith('/api/velas')) { const ds = +(new URL(req.url, 'http://x').searchParams.get('desde') || 0); return json(live.candles().filter(c => c.t >= ds)); }
  if (req.method === 'POST' && req.url.startsWith('/api/baseline')) { live.setBaseline(); return json(live.state().novas); }
  if (req.method === 'POST' && req.url.startsWith('/api/report')) { const e = await reportNow(new Date().getHours(), false); return json({ enviado: e.sent, erro: e.erro ?? null }); }
  if (req.method === 'POST' && req.url.startsWith('/api/exemplos')) {          // manda uma amostra de cada tipo de mensagem, marcada como exemplo
    const S = live.summary(), now = Date.now(), tag = '🧪 <i>exemplo de formatação</i>\n';
    const out = [];
    for (const [k, txt] of [['signal', M.signal({ dir: 'G', run: 5, entryT: now + 60_000, stake: 40 })], ['signal', M.signal({ dir: 'R', run: 4, entryT: now + 60_000, stake: 40 })],
      ['pre', M.pre({ X: 'G', r: 3, closeAt: now + 60_000, leadMs: 7000 })], ['marco', M.marco(S, 300)], ['aviso', M.aviso({ titulo: 'Sem dados do gráfico', texto: 'Deixe o gráfico IDX/USDT em M1 aberto na janela.' })]])
      out.push((await send('exemplo', tag + txt)).sent);
    out.push((await send('exemplo', tag + M.report(S, new Date().getHours(), false))).sent);
    return json({ enviados: out });
  }
  if (req.url.startsWith('/dados/historico.json')) { res.writeHead(200, { 'content-type': 'application/json' }); return res.end(fs.existsSync('dados/historico.json') ? fs.readFileSync('dados/historico.json') : '{}'); }
  res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
  res.end(fs.readFileSync(req.url.startsWith('/historico') ? 'historico.html' : 'index.html'));
}).listen(3000, () => console.log('Painel: http://localhost:3000'));
