// Formatação das mensagens do Telegram (HTML). Todas as mensagens saem daqui, para manter o mesmo visual.
const P = 0.538, BE = 1 / 1.96;                                  // esperado pelo backtest e equilíbrio (payout 96%)
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const num = (n, d = 0) => Number(n).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
export const money = n => `${n < 0 ? '−' : '+'}$${num(Math.abs(n), 2)}`;
const usd = n => `$${num(n, 2)}`;
const pct = (x, d = 1) => `${num(100 * x, d)}%`;
const bar = (x, len = 10, lo = 0.40, hi = 0.65) => { const k = Math.round(Math.max(0, Math.min(1, (x - lo) / (hi - lo))) * len); return '▰'.repeat(k) + '▱'.repeat(len - k); };
const hms = ms => new Date(ms).toLocaleTimeString('pt-BR');
const dm = ms => new Date(ms).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
const hm = ms => new Date(ms).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
const hh = h => String(((h % 24) + 24) % 24).padStart(2, '0') + ':00';
const LINE = '━━━━━━━━━━━━━━━━━━';
const alarm = n => P - 2 * Math.sqrt(P * (1 - P) / n);
const clear = n => BE + 2 * Math.sqrt(BE * (1 - BE) / n);
const wilson = (k, n) => { if (!n) return [0, 0]; const z = 1.96, p = k / n, d = 1 + z * z / n, c = (p + z * z / (2 * n)) / d, h = z * Math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return [c - h, c + h]; };
const row = (k, v) => ` ${k.padEnd(11)}${v}`;
const mono = rows => `<pre>${rows.map(esc).join('\n')}</pre>`;

function situacao(n, r, minN = 50) {
  if (n < minN) return { e: '⚪', t: 'Poucas entradas para avaliar' };
  if (r < alarm(n)) return { e: '🔴', t: 'Abaixo da faixa de alarme' };
  if (r > clear(n)) return { e: '🟢', t: 'Acima do equilíbrio, com folga' };
  return { e: '🟡', t: 'Dentro da faixa · inconclusivo' };
}

export const signal = ({ dir, run, entryT, stake, forca, forte, ativo = 'IDX/USDT', soros, semAviso, noite }) => {
  const buy = dir === 'G', acao = buy ? 'COMPRAR' : 'VENDER', tipo = (noite ? '🌙 MADRUGADA · ' : '') + (forte ? '💪 SINAL FORTE' : '⚪ SINAL COMUM');
  const valor = forte ? (soros ? `${usd(stake)} (Soros: ${usd(stake * 1.96)} se a entrada anterior ganhar)` : usd(stake)) : `${usd(stake)} fixo (sem Soros)`;
  return [`${tipo} · ${buy ? '🟢' : '🔴'} <b>${acao} AGORA · ${esc(ativo)}</b>`, LINE,
    `📍 <b>Abra o gráfico ${esc(ativo)}</b>`,
    `<b>${run}ª vela ${buy ? 'verde' : 'vermelha'}</b> seguida · ${esc(ativo)} M1`,
    mono([row('Tipo', forte ? 'FORTE (força 4,9+)' : 'COMUM (4+ velas)'), row('Direção', buy ? 'COMPRA  ▲' : 'VENDA   ▼'), row('Entrada', `abertura de ${hms(entryT)}`), row('Valor', valor)]),
    ...(forte && semAviso ? ['⚠️ <i>Sinal sem aviso de atenção antes: a força subiu de repente nesta vela.</i>'] : []),
    ...(forca != null ? [forte ? `💪 <b>SINAL FORTE</b> · força ${num(forca, 1)} ATR · entra no Soros` : `⚪ <b>SINAL COMUM</b> · força ${num(forca, 1)} ATR · valor fixo, não entra no Soros`] : [forte ? '💪 <b>SINAL FORTE</b>' : '⚪ <b>SINAL COMUM</b>'])].join('\n');
};

export const pre = ({ X, r, closeAt, leadMs, forca, ativo = 'IDX/USDT' }) => {
  const buy = X === 'G';
  return [`👀 <b>Atenção · ${esc(ativo)}</b> · ${r} velas <b>${buy ? 'verdes' : 'vermelhas'}</b> seguidas${forca != null ? ` · força ${num(forca, 1)} ATR` : ''}`,
    `<i>A ${r + 1}ª vela fecha às ${hms(closeAt)}. Pode sair um <b>💪 SINAL FORTE</b> de ${buy ? 'COMPRA' : 'VENDA'} ~${Math.round(leadMs / 1000)}s antes, se ela continuar ${buy ? 'verde' : 'vermelha'} e a força passar de 4,9. Vá para o gráfico <b>${esc(ativo)}</b>.</i>`].join('\n');
};

export function report(S, h, final) {
  const { hoje, janela, total, novas } = S, dia = hoje.n ? hoje.w / hoje.n : null;
  const rate = S.dias ? total.n / S.dias : 0, L = [];
  L.push(final ? `🏁 <b>FECHAMENTO DO DIA · ${hh(h)}</b>` : `📊 <b>RELATÓRIO DAS ${hh(h)}</b>`, `<i>IDX/USDT M1 · entrada de ${usd(S.stake)}</i>`, LINE, '');
  L.push('<b>HOJE</b>', mono([
    row('Entradas', `${hoje.n}  (${hoje.w}W · ${hoje.n - hoje.w}L${hoje.e ? ` · ${hoje.e}E` : ''})`),
    row('Acerto', dia === null ? '–' : `${pct(dia)}  ${bar(dia)}`),
    row('Resultado', money(hoje.pnl)),
    row('Pico/Fundo', `${money(hoje.pico)} / ${money(hoje.fundo)}`),
    row('Sequência', hoje.seqTipo === null ? '–' : `${hoje.seqAtual} ${hoje.seqTipo ? 'win(s)' : 'loss(es)'} seguidos`),
    row('Máx. losses', String(hoje.maxSeqLoss))]));
  L.push(`<b>ÚLTIMA HORA</b> <i>(${hh(h - 1)}–${hh(h)})</i>`, mono(janela.n
    ? [row('Entradas', `${janela.n}  (${janela.w}W · ${janela.n - janela.w}L)`), row('Acerto', pct(janela.w / janela.n)), row('Resultado', money(janela.pnl))]
    : [' nenhuma entrada fechada']));
  const nn = novas.n, r = nn ? novas.w / nn : 0, sit = situacao(nn, r);
  const pontos = [100, 200, 300, 500, 1000, 2000, 3000, 4000, 5000], prox = pontos.find(p => p > nn);
  L.push(`<b>ENTRADAS NOVAS</b> <i>desde ${dm(novas.desde)} ${hm(novas.desde)}</i>`, mono([
    row('Entradas', `${nn}  (${novas.w}W · ${nn - novas.w}L)`),
    row('Acerto', nn ? `${pct(r)}  ${bar(r)}` : '–'),
    row('Resultado', money(novas.pnl)),
    row('Alarme', nn >= 30 ? `abaixo de ${pct(alarm(nn))}` : '–'),
    row('Esperado', `${pct(P)}  · equil. ${pct(BE)}`)]),
    `${sit.e} <b>${sit.t}</b>`,
    prox ? `<i>Próximo marco: ${prox} entradas — faltam ${prox - nn}${rate ? ` (~${Math.ceil((prox - nn) / rate)} dia(s))` : ''}</i>` : '<i>Todos os marcos atingidos</i>', '');
  const ar = total.n ? total.w / total.n : 0;
  L.push(`<b>ACUMULADO</b> <i>desde 09/10 · referência</i>`, mono([
    row('Entradas', `${total.n}  (${total.w}W · ${total.n - total.w}L)`), row('Acerto', total.n ? pct(ar) : '–'),
    row('Resultado', money(total.pnl)), row('Banca painel', usd(S.bank))]), '');
  L.push(final ? '😴 <i>Até amanhã às 08h.</i>' : '<i>Próximo relatório na próxima hora cheia.</i>');
  return L.join('\n');
}

export function reportForte(F, h, final) {
  const { soros: S, fixo: X, cfg } = F, now = Date.now(), de = new Date(now); de.setMinutes(0, 0, 0); const ini = de.getTime() - (final ? 0 : 3_600_000), fim = ini + 3_600_000;
  const hr = S.linhas.filter(l => l.t >= ini && l.t < fim), hw = hr.filter(l => l.res === 'W').length, hn = hr.filter(l => l.res !== 'E').length, hp = hr.reduce((a, l) => a + l.pnl, 0);
  const acc = (o) => o.n ? `${pct(o.w / o.n)}  ${bar(o.w / o.n)}` : '–', L = [];
  L.push(final ? `🏁 <b>FECHAMENTO DO DIA · ${hh(h)}</b>` : `📊 <b>RELATÓRIO DAS ${hh(h)}</b>`, `<i>💪 Sinais fortes · IDX + MEMX · Soros nível 1 (base ${usd(cfg.stake)})</i>`, LINE, '');
  L.push('<b>HOJE</b>', mono([
    row('Entradas', `${S.hoje.n}  (${S.hoje.w}W · ${S.hoje.n - S.hoje.w}L)`), row('Acerto', acc(S.hoje)),
    row('Soros', money(S.hoje.pnl)), row('Fixa', money(X.hoje.pnl)),
    row('IDX', `${S.ativos.IDX.n} entr. · ${S.ativos.IDX.n ? pct(S.ativos.IDX.w / S.ativos.IDX.n) : '–'}`), row('MEMX', `${S.ativos.MEMX.n} entr. · ${S.ativos.MEMX.n ? pct(S.ativos.MEMX.w / S.ativos.MEMX.n) : '–'}`)]));
  L.push(`<b>ÚLTIMA HORA</b> <i>(${hh(new Date(ini).getHours())}–${hh(new Date(fim).getHours())})</i>`, mono(hn
    ? [row('Entradas', `${hn}  (${hw}W · ${hn - hw}L)`), row('Resultado', money(hp))] : [' nenhuma entrada forte']));
  const r = S.n ? S.w / S.n : 0;
  L.push(`<b>ACUMULADO</b> <i>desde ${dm(cfg.desde)} ${hm(cfg.desde)}</i>`, mono([
    row('Entradas', `${S.n}  (${S.w}W · ${S.n - S.w}L)`), row('Acerto', acc(S)), row('Soros', money(S.pnl)), row('Fixa', money(X.pnl)),
    row('Banca', usd(S.banca)), row('Esperado', `${pct(P)}  · equil. ${pct(BE)}`)]),
    S.n >= 30 ? (r >= 0.53 ? '🟢 <b>Acima de 53% (meta)</b>' : r >= 0.51 ? '🟡 <b>Entre 51% e 53%</b>' : '🔴 <b>Abaixo de 51%</b>') : '⚪ <i>Poucas entradas para avaliar (meta: ~500 até 30/11)</i>', '');
  L.push(final ? '😴 <i>Até amanhã às 08h.</i>' : '<i>Próximo relatório na próxima hora cheia.</i>');
  return L.join('\n');
}

export function marco(S, p) {
  const nv = S.novas, n = nv.n, w = nv.w, r = n ? w / n : 0, [lo, hi] = wilson(w, n), sit = situacao(n, r, 1);
  let nota;
  if (r < alarm(n)) nota = 'Neste ponto os dados contradizem o backtest. Vale reavaliar a estratégia antes de operar com dinheiro.';
  else if (r > clear(n)) nota = 'Sinal forte de que a vantagem existe. Dá para planejar a volta, aos poucos.';
  else if (r >= 0.52) nota = 'Caminho bom: acerto de 52% ou mais, mas ainda estatisticamente inconclusivo.';
  else nota = 'Inconclusivo: continue acompanhando antes de decidir.';
  let sit2 = sit;
  if (p >= 2000) {                                                  // checkpoint: a decisão final é no fim de novembro (30/11/2026), com os mesmos limites (>=53% validada · 51–53% fraca · <51% reprovada)
    if (r >= 0.53) { sit2 = { e: '🟢', t: 'Acima de 53% · no caminho de validar' }; nota = 'Acerto de 53% ou mais neste ponto. O veredito final fica para 30/11, com mais entradas.'; }
    else if (r >= 0.51) { sit2 = { e: '🟡', t: 'Entre 51% e 53% · vantagem fraca até aqui' }; nota = 'Acima do equilíbrio, mas abaixo da meta de 53%. Seguir acompanhando até 30/11, sem aumentar a entrada.'; }
    else { sit2 = { e: '🔴', t: 'Abaixo de 51% · sem vantagem até aqui' }; nota = 'Abaixo do equilíbrio neste ponto. A decisão final é em 30/11, mas é um sinal de alerta.'; }
  }
  const extra = p >= 2000 ? 'Checkpoint: o veredito final é dado no fim de novembro (30/11/2026).' : p >= 1000 ? 'Com 1.000 entradas a leitura já é bem mais firme.' : p >= 500 ? 'Cuidado: com 500 entradas, se a estratégia só empatasse (51%), ainda haveria ~34% de chance de ver 52% ou mais por sorte.' : null;
  const rate = S.dias ? S.total.n / S.dias : 0, prox = [100, 200, 300, 500, 1000, 2000, 3000, 4000, 5000].find(q => q > p);
  return [`🏁 <b>MARCO · ${num(p)} ENTRADAS NOVAS</b>`, `<i>desde ${dm(nv.desde)} ${hm(nv.desde)}</i>`, LINE,
    mono([row('Entradas', `${n}  (${w}W · ${n - w}L)`), row('Acerto', `${pct(r)}  ${bar(r)}`), row('IC 95%', `${pct(lo)} – ${pct(hi)}`),
      row('Resultado', money(nv.pnl)), row('Alarme', `abaixo de ${pct(alarm(n))}`), row('Esperado', pct(P)), row('Equilíbrio', pct(BE))]),
    `${sit2.e} <b>${sit2.t}</b>`, `<i>${nota}</i>`, ...(extra ? ['', `⚠️ <i>${extra}</i>`] : []),
    ...(prox ? ['', `<b>Próximo marco:</b> ${num(prox)} (faltam ${prox - n}${rate ? `, ~${Math.ceil((prox - n) / rate)} dia(s)` : ''})`] : [])].join('\n');
}

export const aviso = ({ titulo, texto }) => [`⚠️ <b>${esc(titulo)}</b>`, `<i>${esc(texto)}</i>`].join('\n');
export const restabelecido = () => '✅ <b>Conexão com o gráfico restabelecida</b>\n<i>Os sinais voltaram a ser avaliados.</i>';

export function veredito(S) {                                       // veredito final (30/11/2026): mesmos limites combinados, com todas as entradas novas até a data
  const nv = S.novas, n = nv.n, w = nv.w, r = n ? w / n : 0, [lo, hi] = wilson(w, n);
  const sit = r >= 0.53 ? { e: '✅', t: 'VALIDADA · a vantagem se confirma ao vivo' } : r >= 0.51 ? { e: '🟡', t: 'Vantagem fraca · inconclusiva' } : { e: '❌', t: 'REPROVADA · sem vantagem sobre o equilíbrio' };
  const nota = r >= 0.53 ? 'Acerto de 53% ou mais, como combinado. Dá para planejar a volta, com entrada pequena e gestão.' : r >= 0.51 ? 'Entre 51% e 53%: acima do equilíbrio, mas abaixo da meta. Manter entrada pequena e seguir acompanhando.' : 'Abaixo de 51%: os dados não sustentam a vantagem. Reavaliar a estratégia antes de operar com dinheiro.';
  return [`🏁 <b>VEREDITO FINAL · 30/11/2026</b>`, `<i>entradas novas desde ${dm(nv.desde)} ${hm(nv.desde)}</i>`, LINE,
    mono([row('Entradas', `${n}  (${w}W · ${n - w}L)`), row('Acerto', `${pct(r)}  ${bar(r)}`), row('IC 95%', `${pct(lo)} – ${pct(hi)}`), row('Resultado', money(nv.pnl)), row('Esperado', pct(P)), row('Equilíbrio', pct(BE))]),
    `${sit.e} <b>${sit.t}</b>`, `<i>${nota}</i>`].join('\n');
}

export const criptoSinal = ({ pair, entryT, stake, K, leadSec }) => [`🔴 <b>VENDER AGORA · ${esc(pair)}</b>`, LINE,
  `<b>${K} velas M15 verdes</b> seguidas · reversão esperada`,
  mono([row('Ativo', pair), row('Direção', 'VENDA   ▼'), row('Prazo', 'vela de 15 min (M15)'), row('Entrada', `abertura de ${hms(entryT)}`), row('Valor', soros ? `${usd(stake)} (Soros: ${usd(stake * 1.96)} se a entrada anterior ganhar)` : usd(stake))]),
  `<i>Sinal ~${leadSec}s antes do fim da 3ª vela. Payout de 90%: equilíbrio em 52,6% de acerto.</i>`].join('\n');
