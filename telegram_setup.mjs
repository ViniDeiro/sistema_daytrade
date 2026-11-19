// Descobre o seu CHAT_ID: 1) crie o bot no @BotFather e ponha o token em .env  2) mande qualquer mensagem ao seu bot  3) rode este script.
import { loadEnv } from './notify.mjs';
const token = loadEnv().TELEGRAM_BOT_TOKEN;
if (!token) { console.log('Coloque TELEGRAM_BOT_TOKEN=... no arquivo .env primeiro.'); process.exit(1); }
const r = await (await fetch(`https://api.telegram.org/bot${token}/getUpdates`)).json();
if (!r.ok) { console.log('Token inválido:', r.description); process.exit(1); }
const chats = new Map(); for (const u of r.result) { const c = u.message?.chat; if (c) chats.set(c.id, c.first_name || c.title || ''); }
if (!chats.size) console.log('Nenhuma mensagem recebida ainda: abra o seu bot no Telegram, toque em Iniciar e mande "oi"; depois rode de novo.');
for (const [id, nome] of chats) console.log(`CHAT_ID = ${id}   (${nome})  -> coloque em .env como TELEGRAM_CHAT_ID=${id}`);
