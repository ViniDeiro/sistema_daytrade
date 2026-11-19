// Gera dados/historico.json para a página /historico: Regra 1 (4+ velas da mesma cor → entra a favor na seguinte),
// refeita pelas velas fechadas, agregada por dia e hora. Uso: node gera_historico.mjs   (pode rodar com o servidor ligado)
// Por (ativo, dia, hora): [todosW, todosL, todosE, fortesW, fortesL, fortesE]. Forte = força ≥ 4,9 ATR14 (mesma conta do ao vivo).
import fs from 'fs';
const MIN = 60_000, col = c => c.c > c.o ? 1 : c.c < c.o ? -1 : 0;
const ATIVOS = { IDX: ['dados/candles_IDX_2anos_2026-10-09.json', 'dados/IDXUSDT_candles.json'], MEMX: ['dados/MEMXUSDT_candles.json'] };
const out = { geradoEm: Date.now(), ativos: {} };
for (const [nome, arqs] of Object.entries(ATIVOS)) {
  const by = new Map(); for (const f of arqs) if (fs.existsSync(f)) for (const c of JSON.parse(fs.readFileSync(f))) by.set(c.t, c);
  const ts = [...by.keys()].sort((a, b) => a - b), dias = {}, velas = {}, seq = { todos: [], fortes: [] };
  const cel = (d, h) => ((dias[d] ??= {})[h] ??= Array(14).fill(0));
  for (const B of ts) {
    const dt = new Date(B), d = dt.toLocaleDateString('sv-SE'), h = dt.getHours(); velas[d] = (velas[d] ?? 0) + 1;
    const s = by.get(B - MIN); if (!s) continue; const X = col(s); if (!X) continue;
    let r = 1; while (r < 400 && by.get(B - (r + 1) * MIN) && col(by.get(B - (r + 1) * MIN)) === X) r++;
    if (r < 4) continue;
    const nd = col(by.get(B)), k = nd === 0 ? 2 : nd === X ? 0 : 1, c = cel(d, h); c[k]++;
    let soma = 0, ok = true; for (let i = 1; i <= 14; i++) { const x = by.get(B - i * MIN); if (!x) { ok = false; break; } soma += x.h - x.l; }
    const st = by.get(B - r * MIN);
    const forte = ok && st && soma > 0 && Math.abs(s.c - st.o) / (soma / 14) >= 4.9; if (forte) c[3 + k]++;
    seq.todos.push({ B, k, d, h }); if (forte) seq.fortes.push({ B, k, d, h });
  }
  // Soros nível 1 (igual ao painel): se a entrada anterior foi no minuto anterior e ganhou, esta vale stake×(1+payout); depois volta ao normal.
  // Guarda quantas vitórias/derrotas caíram no nível 1, em dois modos: "segue" (sequência vem da hora anterior) e "zera" (a hora começa do zero,
  // usado quando a hora anterior está fora do filtro). Posições 6..13 da célula: todos[segueW1,segueL1,zeraW1,zeraL1], fortes[idem].
  for (const [ti, tipo] of [[0, 'todos'], [1, 'fortes']]) for (const [mi, zera] of [[0, false], [1, true]]) {
    let nivel = 0, prev = null;
    for (const t of seq[tipo]) {
      if (!(prev && t.B - prev.B === MIN && prev.k === 0 && !(zera && prev.h !== t.h))) nivel = 0;
      else nivel = prev.nivel === 0 ? 1 : 0;
      if (nivel === 1 && t.k < 2) cel(t.d, t.h)[6 + ti * 4 + mi * 2 + t.k]++;
      t.nivel = nivel; prev = t;
    }
  }
  out.ativos[nome] = { de: ts[0], ate: ts.at(-1), dias, velas };
  console.log(nome, new Date(ts[0]).toLocaleDateString('pt-BR'), '→', new Date(ts.at(-1)).toLocaleString('pt-BR'), Object.keys(dias).length, 'dias');
}
fs.writeFileSync('dados/historico.json', JSON.stringify(out));
console.log('dados/historico.json', (fs.statSync('dados/historico.json').size / 1024).toFixed(0), 'KB');
