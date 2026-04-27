import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ضع التوكن هنا مباشرة (للتجريب فقط)
TOKEN = "8650482506:AAFswJ6DEtb1O_x5sUcUZNlqu5HbeQgQ2bI"

# تفعيل التسجيل للأخطاء
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
    
    # رسالة مضحكة حسب الرقم
    if dice == 1:
        msg = "😭 يا خسارة! طلعلك **1** ... جرب حظك مرة ثانية"
    elif dice == 6:
        msg = "🎉🎊 مبروك! طلعلك **6** ... أنت محظوظ اليوم!"
    else:
        msg = f"🎲 رميت النرد... النتيجة: **{dice}**\n\nاضغط الزر لتجربة حظك مجدداً."
    
    keyboard = [[InlineKeyboardButton("🎲 رمي مجدداً", callback_data="roll")]]
    await query.edit_message_text(
        msg,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# تشغيل البوت
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(roll_dice, pattern="roll"))
    print("✅ البوت يعمل... اضغط Ctrl+C للإيقاف")
    app.run_polling()

if __name__ == "__main__":
    main()