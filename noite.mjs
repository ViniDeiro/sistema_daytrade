// Modo madrugada: libera sinais/alertas fora do horário normal (08h–22h) em janelas fixas (dados/noite.json, campo "janelas" em minutos do dia,
// ex.: [[0, 240]] = 00:00–04:00 todo dia) ou até um instante ("ate", ms). As entradas da madrugada ficam marcadas noite:true e fora da contagem oficial.
import fs from 'node:fs';
export function noiteAtiva(ms = Date.now()) {
  let c; try { c = JSON.parse(fs.readFileSync('dados/noite.json', 'utf8')); } catch { return false; }
  if (ms < (c.ate || 0)) return true;
  const d = new Date(ms), m = d.getHours() * 60 + d.getMinutes();
  return (c.janelas || []).some(([a, b]) => m >= a && m < b);
}
