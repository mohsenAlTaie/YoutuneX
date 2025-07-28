import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8377439618:AAFOg73PrKhO2I-1SIwt8pxWocV5s1I-l9U"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

DEV_MESSAGE = (
    "🎼🚧 *YoutuneX - بوت تحميل الموسيقى من يوتيوب* 🚧🎼\n\n"
    "حالياً البوت تحت التطوير السوبر… نضيف ميزات جديدة ونحسن الجودة لأجلكم!\n"
    "⏳ الرجاء الانتظار والعودة لاحقاً، قريبًا ترجع الأغاني تنزل بجودة وذوق الملوك 👑\n\n"
    "_شكرًا لصبرك ودعمك، إنت نغمة خاصة بهذا البوت! 🎶❤️_\n\n"
    "👨‍💻 المطور: [@K0_MG](https://t.me/K0_MG)"
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(DEV_MESSAGE, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(DEV_MESSAGE, parse_mode="Markdown")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.run_polling()

if __name__ == "__main__":
    main()
