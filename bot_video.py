import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

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

# Dummy: Simulasi user count untuk masing-masing bot
# Nanti ini bisa diganti dengan data nyata, misal dari database atau cache
user_counts = {
    "@NakalAccess_Bot": 6325,
    "@GacorAccess_Bot": 4780,
    "@Koloni4DNakal_Bot": 3870,
    "@SingaNakal_Bot": 2560,
}

# Fungsi untuk update nama bot via API Telegram (setMyName)
async def update_bot_name(token, display_name):
    url = f"https://api.telegram.org/bot{token}/setMyName"
    data = {"name": display_name}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            res_json = await resp.json()
            if not res_json.get("ok"):
                print(f"❌ Gagal update nama bot: {res_json}")
            else:
                print(f"✅ Nama bot berhasil diupdate ke:\n{display_name}")

# === CEK MEMBER DAN LANJUT ===
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
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Lanjut ➡️", url=next_url)]
            ])
        )
    except Exception:
        # Belum join semua
        buttons = [[InlineKeyboardButton("📥 Join Grup", url=f"https://t.me/{config['group'][1:]}")]]
        for ch in config["channels"]:
            buttons.append([InlineKeyboardButton("📥 Join Channel", url=f"https://t.me/{ch[1:]}")])
        buttons.append([InlineKeyboardButton("🔁 Coba Lagi", callback_data=f"check_again_{video_id}")])

        await context.bot.send_message(
            chat_id=user_id,
            text="❗ Kamu harus join semua grup dan channel ini dulu:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, config):
    video_id = context.args[0] if context.args else ""
    await check_membership_and_reply(update, context, config, video_id)

# === Callback tombol ulang ===
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, config):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("check_again_"):
        video_id = query.data.replace("check_again_", "")
        await check_membership_and_reply(update, context, config, video_id, is_callback=True)

# Background task yang berjalan terus untuk update nama bot setiap 10 menit
async def background_update_bot_name(app, config):
    token = config["token"]
    bot_name = config["name"]
    bot_username = config["name"]  # Misal pakai ini sebagai key untuk user_counts

    while True:
        # Dapatkan jumlah user untuk bot ini (dummy)
        count = user_counts.get(bot_username, 0)
        # Format nama bot dengan dua baris
        display_name = f"{bot_name}\n{count} pengguna"

        # Panggil API update nama bot
        await update_bot_name(token, display_name)

        # Tunggu 10 menit sebelum update lagi
        await asyncio.sleep(600)  # 600 detik = 10 menit

# === Build & Jalankan Bot ===
async def run_bot(config):
    app = ApplicationBuilder().token(config["token"]).build()
    app.add_handler(CommandHandler("start", lambda u, c: start(u, c, config)))
    app.add_handler(CallbackQueryHandler(lambda u, c: callback_handler(u, c, config), pattern="^check_again_"))
    print(f"✅ {config['name']} aktif.")
    await app.initialize()
    await app.start()

    # Start background task untuk update nama bot
    app.job = asyncio.create_task(background_update_bot_name(app, config))

    return app

# === Main Async Loop untuk Semua Bot ===
async def main():
    apps = await asyncio.gather(*(run_bot(cfg) for cfg in BOTS_CONFIG))
    print("Semua bot aktif. Menunggu polling...")

    # Mulai polling semua bot
    await asyncio.gather(*(app.updater.start_polling() for app in apps))
    await asyncio.Event().wait()  # Biar tetap jalan di Railway

if __name__ == "__main__":
    asyncio.run(main())
