import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

# ضع التوكن هنا مباشرة (للتجريب فقط)
TOKEN = "8650482506:AAFswJ6DEtb1O_x5sUcUZNlqu5HbeQgQ2bI"

# تفعيل التسجيل للأخطاء
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# أمر /start
def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton("🎲 رمي النرد", callback_data="roll")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('🎲 أهلاً بك في لعبة النرد!\nاضغط الزر أدناه لرمي النرد.',
                              reply_markup=reply_markup)

# استجابة زر النرد
def roll_dice(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    dice = random.randint(1, 6)
    
    # رسائل حسب الرقم
    if dice == 1:
        msg = "😭 يا خسارة! طلعلك **1** ... جرب حظك مرة ثانية"
    elif dice == 6:
        msg = "🎉🎊 مبروك! طلعلك **6** ... أنت محظوظ اليوم!"
    else:
        msg = f"🎲 رميت النرد... النتيجة: **{dice}**\n\nاضغط الزر لتجربة حظك مجدداً."
    
    keyboard = [[InlineKeyboardButton("🎲 رمي مجدداً", callback_data="roll")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text=msg, reply_markup=reply_markup, parse_mode='Markdown')

# تشغيل البوت
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(roll_dice, pattern='roll'))
    
    updater.start_polling()
    print("✅ البوت يعمل... اضغط Ctrl+C للإيقاف")
    updater.idle()

if __name__ == '__main__':
    main()