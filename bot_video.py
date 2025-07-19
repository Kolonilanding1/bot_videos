import asyncio
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# === KONFIGURASI BOT BERJENJANG ===
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
        "next_bot": "@Koloni4DNakal_Bot",
        "group": "@SITUSLINKGACOR4D",
        "channels": ["@bolapelangi2ofc", "@studionakal18"]
    },
    {
        "token": "8104298639:AAGv8wMQmPwIEQAnC5h09BSUJyCjl14bg3Q",
        "name": "@Koloni4DNakal_Bot",
        "next_bot": "@SingaNakal_Bot",
        "group": "@GrupStudioNakal",
        "channels": ["@koloni4d_official1", "@studionakal18"]
    },
    {
        "token": "7681213875:AAHfdNdjljBinIGNO2WUC2lfSifNJQJAH5A",
        "name": "@SingaNakal_Bot",
        "next_bot": "@FinalNakal_Bot",
        "group": "@GrupStudioNakal",
        "channels": ["@Infosingaslot", "@studionakal18"]
    }
]

# === CEK MEMBER DAN LANJUT ===
async def check_membership_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, config, video_id="", is_callback=False):
    user = update.effective_user
    user_id = user.id

    try:
        # Cek grup
        group_member = await context.bot.get_chat_member(config["group"], user_id)
        if group_member.status not in ("member", "administrator", "creator"):
            raise Exception("Belum join grup")

        # Cek semua channel
        for ch in config["channels"]:
            ch_member = await context.bot.get_chat_member(ch, user_id)
            if ch_member.status not in ("member", "administrator", "creator"):
                raise Exception("Belum join channel")

        # Lanjut ke bot berikutnya
        next_url = f"https://t.me/{config['next_bot'][1:]}?start={video_id}"
        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Kamu sudah join semua. Klik tombol di bawah untuk lanjut.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Lanjut ➡️", url=next_url)]
            ])
        )
    except Exception:
        # Belum join → tampilkan ulang tombol join
        buttons = [[InlineKeyboardButton("📥 Join Grup", url=f"https://t.me/{config['group'][1:]}")]]
        for ch in config["channels"]:
            buttons.append([InlineKeyboardButton("📥 Join Channel", url=f"https://t.me/{ch[1:]}")])
        buttons.append([InlineKeyboardButton("🔁 Coba Lagi", callback_data=f"check_again_{video_id}")])

        await context.bot.send_message(
            chat_id=user_id,
            text="❗ Kamu harus join semua grup dan channel ini dulu:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# === /start handler ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, config):
    video_id = context.args[0] if context.args else ""
    await check_membership_and_reply(update, context, config, video_id)

# === callback query handler ===
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, config):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("check_again_"):
        video_id = query.data.replace("check_again_", "")
        await check_membership_and_reply(update, context, config, video_id, is_callback=True)

# === Jalankan bot tunggal ===
def run_bot(config):
    app = ApplicationBuilder().token(config["token"]).build()
    app.add_handler(CommandHandler("start", lambda u, c: start(u, c, config)))
    app.add_handler(CallbackQueryHandler(lambda u, c: callback_handler(u, c, config), pattern="^check_again_"))
    print(f"✅ {config['name']} aktif.")
    app.run_polling()

# === Main untuk semua bot ===
async def main():
    threads = []
    for config in BOTS_CONFIG:
        t = threading.Thread(target=run_bot, args=(config,), daemon=True)
        t.start()
        threads.append(t)

    while True:
        await asyncio.sleep(10)  # Keep alive on Railway

if __name__ == "__main__":
    asyncio.run(main())
