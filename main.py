import os
import shutil
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
)
import yt_dlp

ffmpeg_location = shutil.which("ffmpeg")
print(f"FFmpeg location: {ffmpeg_location}")


logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = "8377439618:AAFOg73PrKhO2I-1SIwt8pxWocV5s1I-l9U"
BOT_USERNAME = "YoutuneX_bot"
SOCIAL_BOT_USERNAME = "@Dr7a_bot"
DEVELOPER_USERNAME = "@K0_MG"
COOKIES_FILE = "cookies_youtube.txt"
DEVELOPER_ID = 7249021797  # غيرها لمعرفك اذا تحتاج

if not os.path.exists("downloads"):
    os.makedirs("downloads", exist_ok=True)

WELCOME_MESSAGE = """
🎧✨ أهلاً بك في عالم الموسيقى السرّي ✨🎧

هنا حيث تتحول الروابط إلى أنغام، والصمت إلى إبداع.
🔮 أرسل رابط يوتيوب لأغنيتك المفضلة وسيحوّلها البوت إلى MP3 بجودة عالية خلال لحظات.

🚀 جرب أسرع بوت موسيقى في التيليغرام!
"""

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 تحميل من يوتيوب", callback_data="download_youtube")],
        [InlineKeyboardButton("🌍 تحميل من جميع المواقع", url=f"https://t.me/{SOCIAL_BOT_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton("🤖 تواصل مع المطور", url="https://t.me/K0_MG")],
        [InlineKeyboardButton("🚀 شارك البوت مع أصدقائك", switch_inline_query="جرب أقوى بوت موسيقى! @YoutuneX_bot")]
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ رجوع للقائمة الرئيسية", callback_data="back_to_main")]
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
            reply_markup=get_back_keyboard()
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
            "❌ أرسل رابط فيديو يوتيوب صحيح فقط!",
            reply_markup=get_main_keyboard()
        )

async def download_youtube_mp3(update: Update, context: ContextTypes.DEFAULT_TYPE, url=None):
    url = url or update.message.text
    user_id = update.effective_user.id

    if not ffmpeg_location:
        await update.message.reply_text("❌ ffmpeg غير مثبت على السيرفر! راسل المطور لحل المشكلة.")
        return

    # جلب عنوان الفيديو تلقائياً
    ydl_info_opts = {
        "quiet": True,
        "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_info_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "music")
    except Exception as e:
        await update.message.reply_text(
            f"❌ فشل جلب معلومات الفيديو: {e}",
            reply_markup=get_main_keyboard()
        )
        # إرسال الخطأ للمطور تلقائياً
        try:
            await context.bot.send_message(chat_id=DEVELOPER_ID, text=f"يوزر: {user_id}\nخطأ في جلب معلومات الفيديو:\n{e}")
        except: pass
        return

    file_name = f"downloads/{user_id}_{title[:30].replace(' ', '_').replace('/', '')}.mp3"
    msg = await update.message.reply_text("⏳ جاري تحميل الموسيقى... انتظر لحظات.")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": file_name,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192"
        }],
        "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
        "quiet": True,
        "ffmpeg_location": ffmpeg_location
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if os.path.exists(file_name):
            # فحص طول الملف الصوتي
            from mutagen.mp3 import MP3
            audio = MP3(file_name)
            duration = audio.info.length if audio.info else 0

            if duration < 5:
                await msg.edit_text("❌ الملف الصوتي أقل من 5 ثواني! غالباً الرابط غير صالح أو محدود. جرب فيديو آخر.", reply_markup=get_main_keyboard())
                os.remove(file_name)
                return

            await update.message.reply_audio(
                audio=open(file_name, "rb"),
                title=title
            )
            await msg.delete()
            os.remove(file_name)
        else:
            await msg.edit_text(f"❌ فشل التحويل! الملف لم يُنتج. تحقق من ffmpeg ومن الرابط.", reply_markup=get_main_keyboard())
    except Exception as e:
        await msg.edit_text(f"❌ حدث خطأ أثناء التحميل:\n{str(e)}", reply_markup=get_main_keyboard())
        try:
            await context.bot.send_message(chat_id=DEVELOPER_ID, text=f"يوزر: {user_id}\nخطأ تحميل:\n{e}")
        except: pass

def main():
    print("🔥🔥 MAIN.PY STARTED 🔥🔥")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
