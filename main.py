import shutil
import os
import logging
import yt_dlp
from datetime import datetime, timedelta
from pytz import timezone

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

if not os.path.exists("downloads"):
    os.makedirs("downloads", exist_ok=True)
if not os.path.exists("favorites"):
    os.makedirs("favorites", exist_ok=True)

# رسائل ترحيب ليلية ونهارية
NIGHT_MESSAGE = """
🌑🎧 *مرحباً بك في عالم الموسيقى الليلي!* 🎧🌑

هنا تحت ضوء القمر، تتحول الروابط إلى أنغامٍ سرية، ويندمج صوتك مع ظلال الليل.
أرسل رابط يوتيوب... واجعل الليل يغني لك 🎶🌙

🌌 اختر مغامرتك الليلة من الأزرار أدناه!
"""

DAY_MESSAGE = """
🌞🎧 *صباح الإبداع في عالم الموسيقى!* 🎧🌞

هنا، تحت أشعة الشمس الذهبية، تتحول الروابط إلى أنغام تبعث الأمل والحياة.
كل ما عليك فعله: أرسل رابط يوتيوب ودع البوت يملأ يومك بأجمل الألحان! 🎵✨

🚀 استمتع بتجربة موسيقية نهارية لا مثيل لها عبر الأزرار بالأسفل!
"""

def get_main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌌 استكشف موسيقاك من يوتيوب", callback_data="download_youtube")],
        [InlineKeyboardButton("⭐ قائمة الأغاني المفضلة", callback_data="show_favorites")],
        [InlineKeyboardButton("🪐 استكشف بقية المجرات (كل المواقع)", url=f"https://t.me/{SOCIAL_BOT_USERNAME.lstrip('@')}")],
        [
            InlineKeyboardButton("💖 دعم المطور", url="https://t.me/K0_MG"),
            InlineKeyboardButton("🎁 شارك البوابة مع المغامرين", switch_inline_query="جرب أقوى بوت موسيقى! @YoutuneX_bot")
        ]
    ])

def get_greeting_message():
    baghdad = timezone('Asia/Baghdad')
    now = datetime.now(baghdad)
    hour = now.hour
    print("الوقت الفعلي في بغداد:", now)
    if 19 <= hour or hour < 7:
        return NIGHT_MESSAGE
    else:
        return DAY_MESSAGE

def favorites_file(user_id):
    return f"favorites/{user_id}.txt"

def add_to_favorites(user_id, title, url):
    file = favorites_file(user_id)
    with open(file, "a", encoding="utf-8") as f:
        f.write(f"{title}|{url}\n")

def list_favorites(user_id):
    file = favorites_file(user_id)
    if not os.path.exists(file):
        return []
    with open(file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        return [tuple(line.strip().split("|", 1)) for line in lines if "|" in line]

def clear_favorites(user_id):
    file = favorites_file(user_id)
    if os.path.exists(file):
        os.remove(file)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        get_greeting_message(),
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    if query.data == "download_youtube":
        await query.edit_message_text(
            "🎵 *أرسل الآن رابط فيديو يوتيوب لتحويله لموسيقى خيالية MP3!*\n\nمثال: https://www.youtube.com/watch?v=xxxxxxx",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ العودة إلى القائمة الرئيسية", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown"
        )
    elif query.data == "back_to_main":
        await query.edit_message_text(
            get_greeting_message(),
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    elif query.data == "show_favorites":
        favs = list_favorites(user_id)
        if not favs:
            txt = "⭐ قائمة أغانيك المفضلة فارغة حالياً.\nكل ما عليك: بعد تحميل أي أغنية اضغط زر ⭐ حتى تضيفها هنا."
        else:
            txt = "⭐ *قائمة أغانيك المفضلة:*\n\n"
            for i, (title, url) in enumerate(favs, 1):
                txt += f"{i}. [{title}]({url})\n"
            txt += "\n🗑️ لمسح القائمة بالكامل: أرسل /clear_favorites"
        await query.edit_message_text(
            txt,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ العودة إلى القائمة الرئيسية", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "youtube.com/" in text or "youtu.be/" in text:
        await download_youtube_mp3(update, context, text)
    else:
        await update.message.reply_text(
            "❌ *رجاءً أرسل رابط فيديو يوتيوب صالح فقط!*",
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )

async def download_youtube_mp3(update: Update, context: ContextTypes.DEFAULT_TYPE, url=None):
    url = url or update.message.text
    user_id = update.effective_user.id
    file_name = f"downloads/{user_id}_music.mp3"

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

    msg = await update.message.reply_text("🚀 *جاري تحويل الموسيقى... انتظر!*", parse_mode="Markdown")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "موسيقى غير معروفة")
        if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
            # زر اضافة للمفضلة
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ أضف إلى المفضلة", callback_data=f"add_fav|{title}|{url}")]
            ])
            await update.message.reply_audio(
                audio=open(file_name, "rb"),
                title=title,
                reply_markup=keyboard
            )
            await msg.delete()
            os.remove(file_name)
        else:
            await msg.edit_text(f"❌ فشل التحويل! الملف لم يُنتج. تحقق من ffmpeg ومن الرابط.", reply_markup=get_main_keyboard())
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        await msg.edit_text(f"❌ حدث خطأ أثناء التحويل:\n{str(e)}\n\nتفاصيل:\n{tb}", reply_markup=get_main_keyboard())

async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    if data.startswith("add_fav|"):
        _, title, url = data.split("|", 2)
        add_to_favorites(user_id, title, url)
        await query.answer("تمت إضافة الأغنية إلى قائمتك المفضلة! ⭐", show_alert=True)
        await query.edit_message_reply_markup(None)
    else:
        await button_handler(update, context)

async def clear_favorites_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    clear_favorites(user_id)
    await update.message.reply_text("🗑️ تم مسح قائمة الأغاني المفضلة الخاصة بك.", reply_markup=get_main_keyboard())

def main():
    print("🔥🔥 MAIN.PY STARTED 🔥🔥")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear_favorites", clear_favorites_command))
    app.add_handler(CallbackQueryHandler(callback_query_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()