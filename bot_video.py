import os
import json
import asyncio
import logging
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

import pytz
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ====== KONFIGURASI BOT BERJENJANG (BOT 1-4) ======
BOTS_CONFIG = [
    {
        "token": os.getenv("BOT1_TOKEN"),
        "name": "@NakalAccess_Bot",
        "next_bot": "@GacorAccess_Bot",
        "group": "@InfoFreebet4D",
        "channels": ["@bola_pelangi", "@studionakal18"]
    },
    {
        "token": os.getenv("BOT2_TOKEN"),
        "name": "@GacorAccess_Bot",
        "next_bot": "@KoloniNakal_Bot",
        "group": "@SITUSLINKGACOR4D",
        "channels": ["@bolapelangi2ofc", "@studionakal18"]
    },
    {
        "token": os.getenv("BOT3_TOKEN"),
        "name": "@KoloniNakal_Bot",
        "next_bot": "@SingaNakal_Bot",
        "group": "@GrupStudioNakal18",
        "channels": ["@koloni4d_official1", "@studionakal18"]
    },
    {
        "token": os.getenv("BOT4_TOKEN"),
        "name": "@SingaNakal_Bot",
        "next_bot": "@VidioLast_Bot",
        "group": "@GrupStudioNakal18",
        "channels": ["@koloni4d_official1", "@studionakal18"]
    }
]

# ====== KONFIGURASI BOT TERAKHIR (BOT 5) ======
TOKEN_LAST_BOT = os.getenv("LAST_BOT_TOKEN")
VIDEOS_JSON_PATH = "videos.json"  # Pastikan file ada

def load_videos():
    with open("video.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"📦 [DEBUG] Loaded video IDs: {list(data.keys())}")
    return data

# ====== Bot 1-4: cek membership dan tombol lanjut ======
async def check_membership_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, config, video_id="", is_callback=False):
    user = update.effective_user
    user_id = user.id
    try:
        group_member = await context.bot.get_chat_member(config["group"], user_id)
        if group_member.status not in ("member", "administrator", "creator"):
            raise Exception("Belum join grup")
        for ch in config["channels"]:
            ch_member = await context.bot.get_chat_member(ch, user_id)
            if ch_member.status not in ("member", "administrator", "creator"):
                raise Exception("Belum join channel")

        next_url = f"https://t.me/{config['next_bot'][1:]}?start={video_id}"
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Kamu sudah join semua. Klik tombol di bawah untuk lanjut.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Lanjut ➡️", url=next_url)]])
        )
    except Exception:
        buttons = [[InlineKeyboardButton("📥 Join Grup", url=f"https://t.me/{config['group'][1:]}")]]
        for ch in config["channels"]:
            buttons.append([InlineKeyboardButton("📥 Join Channel", url=f"https://t.me/{ch[1:]}")])
        buttons.append([InlineKeyboardButton("🔁 Coba Lagi", callback_data=f"check_again_{video_id}")])

        await context.bot.send_message(
            chat_id=user_id,
            text="❗ Kamu harus join semua grup dan channel ini dulu:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE, config):
    video_id = context.args[0] if context.args else ""
    await check_membership_and_reply(update, context, config, video_id)

async def callback_handler_bot(update: Update, context: ContextTypes.DEFAULT_TYPE, config):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("check_again_"):
        video_id = query.data.replace("check_again_", "")
        await check_membership_and_reply(update, context, config, video_id, is_callback=True)

# ====== Bot terakhir: kirim foto + link video ======
async def start_last_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    video_id = context.args[0] if context.args else ""

    print(f"✅ [DEBUG] Diterima video ID: {video_id}")

    videos = load_videos()

    # Cek apakah ID valid
    if video_id in videos:
        video = videos[video_id]

        # Cek field penting
        thumbnail = video.get("thumbnail")
        title = video.get("title", "Tanpa Judul")
        url = video.get("url")

        if not (thumbnail and url):
            await context.bot.send_message(
                chat_id=user.id,
                text="⚠️ Data video tidak lengkap. Thumbnail atau URL kosong."
            )
            return

        # Kirim konten ke user
        await context.bot.send_photo(
            chat_id=user.id,
            photo=thumbnail,
            caption=f"🎬 <b>{title}</b>\n\n🔞 Klik tombol di bawah untuk menonton:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🔗 Tonton Sekarang", url=f"https://t.me/NakalAccess_Bot?start={video_id}")]]
            )
        )
    else:
        await context.bot.send_message(
            chat_id=user.id,
            text=f"❌ Video tidak ditemukan atau ID tidak valid.\n(ID: <code>{video_id}</code>)",
            parse_mode="HTML"
        )


# ====== Fungsi tambahan /list ======
async def list_all_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    videos = load_videos()

    if not videos:
        await context.bot.send_message(
            chat_id=user_id,
            text="⚠️ Tidak ada video tersedia saat ini."
        )
        return

    text = "<b>📋 Daftar Video Tersedia:</b>\n\n"
    for vid_id, vid in videos.items():
        title = vid.get("title", "Tanpa Judul")
        text += f"🎬 <b>{title}</b>\n➡️ /start {vid_id}\n\n"

    await context.bot.send_message(
        chat_id=user_id,
        text=text,
        parse_mode="HTML"
    )

# ====== Fungsi logging user ke file ======
def log_activity(user_id, username, action):
    try:
        with open("userlist.txt", "a", encoding="utf-8") as f:
            f.write(f"{datetime.now()} | {user_id} | {username} | {action}\n")
    except Exception as e:
        logging.error(f"Failed to write log: {e}")

# ====== HTTP healthcheck server ======
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is alive!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def start_ping_server():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# Mulai thread healthcheck
threading.Thread(target=start_ping_server, daemon=True).start()

# ====== Fungsi jalankan bot ======
async def run_bot(config):
    app = ApplicationBuilder().token(config["token"]).build()
    app.add_handler(CommandHandler("start", lambda u, c: start_bot(u, c, config)))
    app.add_handler(CallbackQueryHandler(lambda u, c: callback_handler_bot(u, c, config), pattern="^check_again_"))
    print(f"✅ {config['name']} aktif.")
    return app

async def run_last_bot():
    app = ApplicationBuilder().token(TOKEN_LAST_BOT).build()
    app.add_handler(CommandHandler("start", start_last_bot))
    app.add_handler(CommandHandler("list", list_all_videos))  # Tambahkan fitur /list
    print("✅ Bot terakhir aktif.")
    return app

# ====== Main runner ======
async def main():
    all_apps = []
    for config in BOTS_CONFIG:
        app = await run_bot(config)
        all_apps.append(app)

    last_app = await run_last_bot()
    all_apps.append(last_app)

    async def start_polling(app):
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        print("📡 Polling berjalan:", app.bot.username)

    await asyncio.gather(*(start_polling(app) for app in all_apps))
    await asyncio.Event().wait()

# Start semua bot
if __name__ == "__main__":
    asyncio.run(main())
