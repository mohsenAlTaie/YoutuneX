import shutil
import os
import logging
import yt_dlp

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
)

# فحص ffmpeg أول مرة
print("FFmpeg first check:", shutil.which("ffmpeg"))

# تحديد موقع ffmpeg
ffmpeg_location = shutil.which("ffmpeg")
print(f"FFmpeg location: {ffmpeg_location}")

# إصدار yt-dlp
print("yt-dlp version:", yt_dlp.version.__version__)

# فحص مجلد التحميلات
print("هل مجلد downloads موجود؟", os.path.exists("downloads"))
print("هل يمكن الكتابة؟", os.access("downloads", os.W_OK))

# إعداد اللوجات
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = "8377439618:AAFOg73PrKhO2I-1SIwt8pxWocV5s1I-l9U"
BOT_USERNAME = "YoutuneX_bot"
SOCIAL_BOT_USERNAME = "@Dr7a_bot"
DEVELOPER_USERNAME = "@K0_MG"
COOKIES_FILE = "cookies_youtube.txt"

# تأكد من وجود مجلد downloads
if not os.path.exists("downloads"):
    os.makedirs("downloads", exist_ok=True)

# رسالة ترحيب
WELCOME_MESSAGE = """
🎧✨ أهلاً بك في عالم الموسيقى السرّي ✨🎧

هنا حيث تتحول الروابط إلى أنغام، والصمت إلى إبداع.
🔮 كل ما عليك فعله: أرسل رابط يوتيوب لأغنيتك المفضلة، والبوت سيحوّلها إلى MP3 بجودة عالية خلال لحظات.

أطلق العنان لذوقك الموسيقي، وجرّب أسرع بوت موسيقى في التيليغرام 🚀
"""

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 تحميل من يوتيوب", callback_data="download_youtube")],
        [InlineKeyboardButton("🌍 تحميل من جميع المواقع", url=f"https://t.me/{SOCIAL_BOT_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton("🤖 تواصل مع المطور", url="https://t.me/K0_MG")],
        [InlineKeyboardButton("🚀 شارك البوت مع أصدقائك", switch_inline_query="جرب أقوى بوت موسيقى! @YoutuneX_bot")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME_MESSAGE,
        reply_markup=get_main_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "download_youtube":
        await query.edit_message_text(
            "🎵 أرسل الآن رابط فيديو يوتيوب الذي تريد تحميله كملف MP3 (موسيقى فقط).\n\nمثال: https://www.youtube.com/watch?v=xxxxxxx",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ العودة", callback_data="back_to_main")]
            ])
        )
    elif query.data == "back_to_main":
        await query.edit_message_text(
            WELCOME_MESSAGE,
            reply_markup=get_main_keyboard()
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "youtube.com/" in text or "youtu.be/" in text:
        await download_youtube_mp3(update, context, text)
    else:
        await update.message.reply_text(
            "❌ أرسل رابط فيديو يوتيوب صحيح فقط!"
        )

async def download_youtube_mp3(update: Update, context: ContextTypes.DEFAULT_TYPE, url=None):
    url = url or update.message.text
    user_id = update.effective_user.id
    file_name = f"downloads/{user_id}_music.mp3"

    # طباعة كل المتغيرات المهمة كل مرة
    ffmpeg_location = shutil.which("ffmpeg")
    print(f"🔥 FFmpeg location: {ffmpeg_location}")
    print("yt-dlp version:", yt_dlp.version.__version__)
    print("هل مجلد downloads موجود؟", os.path.exists("downloads"))
    print("هل يمكن الكتابة؟", os.access("downloads", os.W_OK))
    print("الرابط الذي أرسله المستخدم:", url)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": file_name,
        "noplaylist": True,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "quiet": False,
        "ffmpeg_location": ffmpeg_location,
        "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None
    }

    msg = await update.message.reply_text("⏳ جاري تحميل الموسيقى... انتظر لحظات.")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        # طباعة حجم الملف بعد التحميل
        if os.path.exists(file_name):
            print("حجم الملف:", os.path.getsize(file_name))
        else:
            print("ملف غير موجود بعد التحميل")

        if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
            await update.message.reply_audio(
                audio=open(file_name, "rb"),
                title="موسيقاك جاهزة 🎶"
            )
            await msg.delete()
            os.remove(file_name)
        else:
            await msg.edit_text(f"❌ فشل التحويل! الملف لم يُنتج. تحقق من ffmpeg ومن الرابط.")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        await msg.edit_text(f"❌ حدث خطأ أثناء التحميل:\n{str(e)}\n\nتفاصيل:\n{tb}")

def main():
    print("🔥🔥 MAIN.PY STARTED 🔥🔥")  # تأكيد بدء البوت باللوج
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()