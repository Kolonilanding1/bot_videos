import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7368142853:AAHNyDF5WMub4gH50v3uuwoGfi5q-3N1Wlo"

def load_videos():
    with open("videos.json", "r") as f:
        return json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔗 Tonton Sekarang", url=video["url"])
            ]])
        )
    else:
        await context.bot.send_message(
            chat_id=user.id,
            text="❌ Video tidak ditemukan atau ID tidak valid."
        )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("✅ Bot terakhir aktif...")
    app.run_polling()
