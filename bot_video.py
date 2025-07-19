import os
import json
import asyncio
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# === KONFIGURASI BOT BERJENJANG ===
BOTS_CONFIG = [
    {
        "BOT1_TOKEN": "7502172892:AAGxZr5cR3unmV92HYu5FXMvuXVFx_xSlBI",
        "name": "@NakalAccessBot",
        "next_bot": "@GacorAccessBot",
        "group": "@InfoFreebet4D",
        "channels": ["@bola_pelangi", "@studionakal18"]
    },
    {
        "BOT2_TOKEN": "7867189011:AAFo0MoSs_YIcteplSP13Nw1dM_Fb04WZTU",
        "name": "@GacorAccessBot",
        "next_bot": "@Koloni4DNakalBot",
        "group": "@SITUSLINKGACOR4D",
        "channels": ["@bolapelangi2ofc", "@studionakal18"]
    },
    {
        "BOT3_TOKEN": "8104298639:AAGv8wMQmPwIEQAnC5h09BSUJyCjl14bg3Q",
        "name": "@Koloni4DNakalBot",
        "next_bot": "@SingaNakalBot",
        "group": "@GrupStudioNakal",
        "channels": ["@koloni4d_official1", "@studionakal18"]
    },
    {
        "BOT4_TOKEN": "7681213875:AAHfdNdjljBinIGNO2WUC2lfSifNJQJAH5A",
        "name": "@SingaNakalBot",
        "next_bot": "@FinalNakalBot",
        "group": "@GrupStudioNakal",
        "channels": ["@Infosingaslot", "@studionakal18"]
    }
]

# === CEK MEMBER DAN KIRIM TOMBOL LANJUT ===
async def check_membership_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, config, video_id="", is_callback=False):
    user = update.effective_user
    user_id = user.id

    try:
        # Cek grup
        member_group = await context.bot.get_chat_member(config["group"], user_id)
        if member_group.status not in ("member", "administrator", "creator"):
            raise Exception("Belum join grup")

        # Cek semua channel
        for ch in config["channels"]:
            member_channel = await context.bot.get_chat_member(ch, user_id)
            if member_channel.status not in ("member", "administrator", "creator"):
                raise Exception("Belum join channel")

        # Sudah join semua → lanjut ke bot berikutnya
        next_url = f"https://t.me/{config['next_bot'][1:]}?start={video_id}"
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Kamu sudah join semua. Klik tombol di bawah untuk lanjut.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Lanjut ➡️", url=next_url)]
            ])
        )
    except Exception:
        # Belum join → kirim ulang tombol join
        join_buttons = [[InlineKeyboardButton("📥 Join Grup", url=f"https://t.me/{config['group'][1:]}")]]
        for ch in config["channels"]:
            join_buttons.append([InlineKeyboardButton("📥 Join Channel", url=f"https://t.me/{ch[1:]}")])
        join_buttons.append([InlineKeyboardButton("🔁 Coba Lagi", callback_data=f"check_again_{video_id}")])

        await context.bot.send_message(
            chat_id=user_id,
            text="❗ Kamu harus join semua grup dan channel berikut sebelum lanjut:",
            reply_markup=InlineKeyboardMarkup(join_buttons)
        )

# === HANDLER /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, config):
    video_id = context.args[0] if context.args else ""
    await check_membership_and_reply(update, context, config, video_id)

# === HANDLER CALLBACK ===
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, config):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("check_again_"):
        video_id = query.data.replace("check_again_", "", 1)
        await check_membership_and_reply(update, context, config, video_id, is_callback=True)

# === JALANKAN SETIAP BOT DALAM THREAD ===
def run_bot(config):
    app = ApplicationBuilder().token(config["token"]).build()
    app.add_handler(CommandHandler("start", lambda u, c: start(u, c, config)))
    app.add_handler(CallbackQueryHandler(lambda u, c: callback_handler(u, c, config), pattern="^check_again_"))
    print(f"🚀 {config['name']} aktif...")
    app.run_polling()

# === MAIN STARTUP UNTUK SEMUA BOT ===
async def main():
    threads = []
    for config in BOTS_CONFIG:
        t = threading.Thread(target=run_bot, args=(config,), daemon=True)
        t.start()
        threads.append(t)

    while True:
        await asyncio.sleep(10)  # Jaga tetap hidup di Railway

if __name__ == "__main__":
    asyncio.run(main())
