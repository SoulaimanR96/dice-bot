import random
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# جلب التوكن من متغيرات البيئة (نضيفه لاحقاً في Render)
TOKEN = os.environ.get("8650482506:AAFswJ6DEtb1O_x5sUcUZNlqu5HbeQgQ2bI")

if not TOKEN:
    raise ValueError("❌ لم يتم العثور على التوكن! تأكد من إضافة BOT_TOKEN في إعدادات Render.")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# أمر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🎲 رمي النرد", callback_data="roll")]]
    await update.message.reply_text(
        "🎲 أهلاً بك في لعبة النرد!\nاضغط الزر أدناه لرمي النرد.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# استجابة زر النرد
async def roll_dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dice = random.randint(1, 6)
    text = f"🎲 رميت النرد... النتيجة: **{dice}**\n\nاضغط الزر لتجربة حظك مجدداً."
    keyboard = [[InlineKeyboardButton("🎲 رمي مجدداً", callback_data="roll")]]
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# تشغيل البوت
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(roll_dice, pattern="roll"))
    print("✅ البوت يعمل على Render...")
    app.run_polling()

if __name__ == "__main__":
    main()