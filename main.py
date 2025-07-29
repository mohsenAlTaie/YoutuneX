import shutil
import os
import logging
import yt_dlp
import json
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
)

# تحقق من ffmpeg
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

FAV_FILE = "favorites.json"
if not os.path.exists(FAV_FILE):
    with open(FAV_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

if not os.path.exists("downloads"):
    os.makedirs("downloads", exist_ok=True)

NIGHT_MESSAGE = """
🎧🌑 مرحباً بك في عالم الموسيقى الليلي! 🌑🎧

هنا تحت ضوء القمر، تتحول الروابط إلى أنغامٍ سرية، ويندمج صوتك مع ظلال الليل.
أرسل رابط يوتيوب... واجعل الليل يغني لك 🎶🌙

🌌 اختر مغامرتك الليلة من الأزرار أدناه!
"""

DAY_MESSAGE = """
🎧🌞 صباح الإبداع في عالم الموسيقى! 🌞🎧

هنا، تحت أشعة الشمس الذهبية، تتحول الروابط إلى أنغام تبعث الأمل والحياة.
كل ما عليك فعله: أرسل رابط يوتيوب ودع البوت يملأ يومك بأجمل الألحان! 🎵✨

🚀 استمتع بتجربة موسيقية نهارية لا مثيل لها عبر الأزرار بالأسفل!
"""

def get_greeting_message():
    # توقيت بغداد UTC+3
    now = datetime.utcnow() + timedelta(hours=3)
    hour = now.hour
    if 7 <= hour < 19:
        return DAY_MESSAGE
    else:
        return NIGHT_MESSAGE

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        get_greeting_message(),
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
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
        user_id = str(update.effective_user.id)
        with open(FAV_FILE, "r", encoding="utf-8") as f:
            favs = json.load(f)
        user_favs = favs.get(user_id, [])
        if user_favs:
            msg = "⭐ قائمة أغانيك المفضلة:\n\n"
            for idx, fav in enumerate(user_favs, 1):
                msg += f"{idx}. [{fav['title']}]({fav['url']})\n"
            msg += "\n⬅️ [العودة إلى القائمة الرئيسية](#)"
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ العودة إلى القائمة الرئيسية", callback_data="back_to_main")]
            ])
            await query.edit_message_text(msg, reply_markup=reply_markup, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            msg = "⭐ قائمة أغانيك المفضلة فارغة حالياً.\n\nكل ما عليك: بعد تحميل أي أغنية اضغط زر ⭐ حتى تضيفها هنا."
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("⬅️ العودة إلى القائمة الرئيسية", callback_data="back_to_main")]
            ])
            await query.edit_message_text(msg, reply_markup=reply_markup)

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

async def add_favorite_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    url = context.user_data.get("last_url")
    title = context.user_data.get("last_title")
    if not url or not title:
        await query.answer("لا توجد أغنية أخيرة لإضافتها.")
        return

    with open(FAV_FILE, "r", encoding="utf-8") as f:
        favs = json.load(f)

    user_favs = favs.get(user_id, [])
    # تحقق إذا الأغنية موجودة مسبقاً
    if any(fav['url'] == url for fav in user_favs):
        await query.answer("الأغنية موجودة مسبقاً في المفضلة ⭐", show_alert=True)
    else:
        user_favs.append({'url': url, 'title': title})
        favs[user_id] = user_favs
        with open(FAV_FILE, "w", encoding="utf-8") as f:
            json.dump(favs, f, ensure_ascii=False, indent=2)
        await query.answer("تمت الإضافة إلى المفضلة ⭐", show_alert=True)

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

    msg = await update.message.reply_text("🚀 *جاري فتح البوابة الصوتية وتحويل الموسيقى... انتظر!*", parse_mode="Markdown")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'المؤدي غير معروف')
        if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
            await update.message.reply_audio(
                audio=open(file_name, "rb"),
                title=title
            )
            # زر الإضافة للمفضلة بعد التحميل
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ أضف إلى المفضلة", callback_data="add_favorite")],
                [InlineKeyboardButton("⬅️ العودة إلى القائمة الرئيسية", callback_data="back_to_main")]
            ])
            await update.message.reply_text(
                "🎶 هل أعجبتك هذه الموسيقى؟ اضغط ⭐ لإضافتها إلى المفضلة!",
                reply_markup=keyboard
            )
            # حفظ بيانات آخر أغنية في user_data
            context.user_data["last_url"] = url
            context.user_data["last_title"] = title
            await msg.delete()
            os.remove(file_name)
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
    app.add_handler(CallbackQueryHandler(button_handler, pattern="^(download_youtube|back_to_main|show_favorites)$"))
    app.add_handler(CallbackQueryHandler(add_favorite_callback, pattern="^add_favorite$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()