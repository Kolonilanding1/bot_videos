import os
import json
import aiohttp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ====== KONFIGURASI BOT BERJENJANG (BOT 1-4) ======
BOTS_CONFIG = [
    {
        "token": "7502172892:AAGxZr5cR3unmV92HYu5FXMvuXVFx_xSlBI",
        "name": "@NakalAccess_Bot",
        "next_bot": "@GacorAccess_Bot",
        "group": "@InfoFreebet4D",
        "channels": ["@bola_pelangi", "@studionakal18"]
    },
    {
        "token": "7867189011:AAFo0MoSs_YIcteplSP13Nw1dM_Fb04WZTU",
        "name": "@GacorAccess_Bot",
        "next_bot": "@KoloniNakal_Bot",
        "group": "@SITUSLINKGACOR4D",
        "channels": ["@bolapelangi2ofc", "@studionakal18"]
    },
    {
        "token": "8104298639:AAGv8wMQmPwIEQAnC5h09BSUJyCjl14bg3Q",
        "name": "@KoloniNakal_Bot",
        "next_bot": "@SingaNakal_Bot",
        "group": "@GrupStudioNakal18",
        "channels": ["@koloni4d_official1", "@studionakal18"]
    },
    {
        "token": "7681213875:AAHfdNdjljBinIGNO2WUC2lfSifNJQJAH5A",
        "name": "@SingaNakal_Bot",
        "next_bot": "@VidioLast_Bot",
        "group": "@GrupStudioNakal18",
        "channels": ["@koloni4d_official1", "@studionakal18"]
    }
]

# ====== KONFIGURASI BOT TERAKHIR (BOT 5) ======
TOKEN_LAST_BOT = "7368142853:AAHNyDF5WMub4gH50v3uuwoGfi5q-3N1Wlo"
VIDEOS_JSON_PATH = "videos.json"

def load_videos():
    try:
        with open(VIDEOS_JSON_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# ====== Bot 1-4: cek membership dan tombol lanjut ======
async def check_membership_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, config, video_id="", is_callback=False):
    user = update.effective_user
    user_id = user.id
    try:
        # Cek grup
        group_member = await context.bot.get_chat_member(config["group"], user_id)
        if group_member.status not in ("member", "administrator", "creator"):
            raise Exception("Belum join grup")

        # Cek channel
        for ch in config["channels"]:
            ch_member = await context.bot.get_chat_member(ch, user_id)
            if ch_member.status not in ("member", "administrator", "creator"):
                raise Exception("Belum join channel")

        # Lanjut ke bot berikutnya
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

# ====== Bot terakhir: tampilkan video ======
async def start_last_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    video_id = context.args[0] if context.args else ""
    videos = load_videos()
    if video_id in videos:
        video = videos[video_id]
        await context.bot.send_photo(
            chat_id=user.id,
            photo=video["thumbnail"],
            caption=f"🎬 <b>{video['title']}</b>\n\n🔞 Klik tombol di bawah untuk menonton:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Tonton Sekarang", url=video["url"])]
            ])
        )
    else:
        await context.bot.send_message(
            chat_id=user.id,
            text="❌ Video tidak ditemukan atau ID tidak valid."
        )

# ====== Jalankan Bot 1–4 ======
async def run_bot(config):
    app = ApplicationBuilder().token(config["token"]).build()
    app.add_handler(CommandHandler("start", lambda u, c: start_bot(u, c, config)))
    app.add_handler(CallbackQueryHandler(lambda u, c: callback_handler_bot(u, c, config), pattern="^check_again_"))
    await app.initialize()
    await app.start()
    print(f"✅ Bot {config['name']} aktif.")
    return app

# ====== Jalankan Bot 5 ======
async def run_last_bot():
    app = ApplicationBuilder().token(TOKEN_LAST_BOT).build()
    app.add_handler(CommandHandler("start", start_last_bot))
    await app.initialize()
    await app.start()
    print("✅ Bot terakhir aktif.")
    return app

# ====== Main Async Runner ======
async def main():
    bots = await asyncio.gather(*(run_bot(cfg) for cfg in BOTS_CONFIG))
    last_bot = await run_last_bot()
    print("🚀 Semua bot sedang berjalan...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
