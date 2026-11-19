// Notificações no celular via Telegram (rodando LOCAL; só faz uma chamada HTTPS à API do Telegram por mensagem).
// Configuração em .env (arquivo local, fora do git):  TELEGRAM_BOT_TOKEN=...  TELEGRAM_CHAT_ID=...
import fs from 'fs';

export function loadEnv(file = '.env') {
  const env = {};
  try { for (const l of fs.readFileSync(file, 'utf8').split('\n')) { const m = /^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/.exec(l); if (m && !l.trim().startsWith('#')) env[m[1]] = m[2]; } } catch {}
  return { ...env, ...Object.fromEntries(Object.entries(process.env).filter(([k]) => k.startsWith('TELEGRAM_') || k.startsWith('ALERT_'))) };
}

export function createNotifier() {
  const cfg = loadEnv();
  const token = cfg.TELEGRAM_BOT_TOKEN, chat = cfg.TELEGRAM_CHAT_ID;
  const ready = !!(token && chat);
  const log = [];
  async function send(kind, text, opts = {}) {
    const entry = { at: Date.now(), kind, text, sent: false };
    const reg = (ok, erro) => { try { fs.appendFileSync('dados/notificacoes.log', `${new Date(entry.at).toISOString()} ${kind} ${ok ? 'enviado' : 'FALHOU ' + (erro ?? '')} | ${String(text).split('\n')[0].replace(/<[^>]+>/g, '')}\n`); } catch {} };
    log.push(entry); if (log.length > 50) log.shift();
    if (!ready) { console.log(`[aviso simulado — sem TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID] ${text}`); return entry; }
    for (let i = 0; i < 4; i++) {                      // tenta de novo se a rede falhar (o sinal vale por poucos segundos)
      try {
        const r = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, { method: 'POST', headers: { 'content-type': 'application/json' }, signal: AbortSignal.timeout(6000),
          body: JSON.stringify({ chat_id: chat, text, ...(opts.html ? { parse_mode: 'HTML' } : {}), disable_notification: !!opts.silent }) });
        entry.sent = r.ok; if (!r.ok) { entry.erro = r.status; console.error('Telegram HTTP', r.status); } else delete entry.erro;
        if (r.ok || r.status < 500 && r.status !== 429) break;
      } catch (e) { entry.erro = e.message; console.error('Telegram falhou:', e.message); }
      await new Promise(r => setTimeout(r, 700));
    }
    reg(entry.sent, entry.erro);
    return entry;
  }
  return { ready, send, log: () => log.slice().reverse(), cfg: { pre: cfg.ALERT_PRE !== '0', leadSec: +(cfg.ALERT_LEAD_SEC || 7) } };
}
