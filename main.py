import shutil
import os
import logging
import yt_dlp
import sqlite3
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
)

# فحص ffmpeg أول مرة
print("FFmpeg first check:", shutil.which("ffmpeg"))
ffmpeg_location = shutil.which("ffmpeg")
print(f"FFmpeg location: {ffmpeg_location}")
print("yt-dlp version:", yt_dlp.version.__version__)
print("هل مجلد downloads موجود؟", os.path.exists("downloads"))
print("هل يمكن الكتابة؟", os.access("downloads", os.W_OK))

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = "8377439618:AAFOg73PrKhO2I-1SIwt8pxWocV5s1I-l9U"
BOT_USERNAME = "YoutuneX_bot"
SOCIAL_BOT_USERNAME = "@Dr7a_bot"
DEVELOPER_USERNAME = "@K0_MG"
COOKIES_FILE = "cookies_youtube.txt"

if not os.path.exists("downloads"):
    os.makedirs("downloads", exist_ok=True)

# إعداد قاعدة بيانات للأغاني المفضلة
db = sqlite3.connect("favorites.db", check_same_thread=False)
cur = db.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS favorites (
    user_id INTEGER,
    url TEXT,
    title TEXT
)""")
db.commit()

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
        [InlineKeyboardButton("⭐ قائمة الأغاني المفضلة", callback_data="favorites")],
        [InlineKeyboardButton("🪐 استكشف بقية المجرات (كل المواقع)", url=f"https://t.me/{SOCIAL_BOT_USERNAME.lstrip('@')}")],
        [
            InlineKeyboardButton("💖 دعم المطور", url="https://t.me/K0_MG"),
            InlineKeyboardButton("🎁 شارك البوابة مع المغامرين", switch_inline_query="جرب أقوى بوت موسيقى! @YoutuneX_bot")
        ]
    ])

def get_greeting_message():
    now = datetime.utcnow() + timedelta(hours=3)
    hour = now.hour
    if 19 <= hour or hour < 7:
        return NIGHT_MESSAGE
    else:
        return DAY_MESSAGE

def get_favorites_keyboard(favorites):
    keyboard = []
    for idx, fav in enumerate(favorites, start=1):
        keyboard.append([
            InlineKeyboardButton(f"{idx}. {fav[2]}", url=fav[1]),
            InlineKeyboardButton("❌ حذف", callback_data=f"removefav_{fav[1]}")
        ])
    keyboard.append([InlineKeyboardButton("⬅️ العودة إلى القائمة الرئيسية", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

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
            "🎵 *أرسل الآن رابط فيديو يوتيوب لتحويله لموسيقى خيالية MP3!*\n\nمثال: https://www.youtube.com/watch?v=xxxxxxx\n\nإذا أعجبتك الأغنية، اضغط على زر ⭐ لإضافتها للمفضلة بعد التحميل.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ العودة إلى المدينة", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown"
        )
    elif query.data == "back_to_main":
        await query.edit_message_text(
            get_greeting_message(),
            reply_markup=get_main_keyboard(),
            parse_mode="Markdown"
        )
    elif query.data == "favorites":
        cur.execute("SELECT * FROM favorites WHERE user_id = ?", (user_id,))
        favorites = cur.fetchall()
        if not favorites:
            await query.edit_message_text(
                "⭐ *قائمة أغانيك المفضلة فارغة حالياً.*\n\nكل ما عليك: بعد تحميل أي أغنية اضغط زر ⭐ حتى تضيفها هنا.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ العودة إلى القائمة الرئيسية", callback_data="back_to_main")]
                ]),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "⭐ *قائمة الأغاني المفضلة لديك:*",
                reply_markup=get_favorites_keyboard(favorites),
                parse_mode="Markdown"
            )
    elif query.data.startswith("removefav_"):
        url = query.data.replace("removefav_", "")
        cur.execute("DELETE FROM favorites WHERE user_id=? AND url=?", (user_id, url))
        db.commit()
        # أرجع للقائمة بعد الحذف
        cur.execute("SELECT * FROM favorites WHERE user_id = ?", (user_id,))
        favorites = cur.fetchall()
        if not favorites:
            await query.edit_message_text(
                "⭐ *تم حذف الأغنية من المفضلة. قائمة أغانيك المفضلة فارغة حالياً.*",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("⬅️ العودة إلى القائمة الرئيسية", callback_data="back_to_main")]
                ]),
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                "⭐ *تم حذف الأغنية. قائمة الأغاني المفضلة لديك:*",
                reply_markup=get_favorites_keyboard(favorites),
                parse_mode="Markdown"
            )

# زر إضافة للأغاني المفضلة (يظهر بعد كل تحميل ناجح)
async def send_favorite_button(update, url, title):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ أضف هذه الأغنية إلى المفضلة", callback_data=f"addfav_{url}|{title}")],
        [InlineKeyboardButton("⬅️ العودة إلى القائمة الرئيسية", callback_data="back_to_main")]
    ])
    await update.message.reply_text(
        f"هل تريد إضافة '{title}' إلى قائمتك المفضلة؟",
        reply_markup=keyboard
    )

async def add_favorite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    try:
        data = query.data.replace("addfav_", "")
        url, title = data.split("|", 1)
        cur.execute("SELECT * FROM favorites WHERE user_id=? AND url=?", (user_id, url))
        if not cur.fetchone():
            cur.execute("INSERT INTO favorites (user_id, url, title) VALUES (?, ?, ?)", (user_id, url, title[:60]))
            db.commit()
        await query.edit_message_text(
            "✅ *تمت إضافة الأغنية لقائمة أغانيك المفضلة!*",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ عرض المفضلة", callback_data="favorites")],
                [InlineKeyboardButton("⬅️ العودة إلى القائمة الرئيسية", callback_data="back_to_main")]
            ]),
            parse_mode="Markdown"
        )
    except Exception as e:
        await query.edit_message_text(f"❌ حدث خطأ: {e}")

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

    # جلب عنوان الفيديو
    title = "موسيقى"
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "cookiefile": COOKIES_FILE if os.path.exists(COOKIES_FILE) else None}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "موسيقى")
    except Exception:
        pass

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

    msg = await update.message.reply_text("🚀 *جاري فتح البوابة الصوتية وتحويل الموسيقى... انتظر!*", parse_mode="Markdown")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
            await update.message.reply_audio(
                audio=open(file_name, "rb"),
                title=title
            )
            await msg.delete()
            os.remove(file_name)
            # زر الإضافة للمفضلة
            await send_favorite_button(update, url, title)
        else:
            await msg.edit_text(f"❌ فشل التحويل! الملف لم يُنتج. تحقق من ffmpeg ومن الرابط.", reply_markup=get_main_keyboard())
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        await msg.edit_text(f"❌ حدث خطأ أثناء التحويل:\n{str(e)}\n\nتفاصيل:\n{tb}", reply_markup=get_main_keyboard())

def main():
    print("🔥🔥 MAIN.PY STARTED 🔥🔥")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(add_favorite_callback, pattern="^addfav_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()