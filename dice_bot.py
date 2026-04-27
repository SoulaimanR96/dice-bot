import requests
import json
import time
import random

# التوكن الخاص بالبوت
TOKEN = "8650482506:AAFswJ6DEtb1O_x5sUcUZNlqu5HbeQgQ2bI"
URL = f"https://api.telegram.org/bot{TOKEN}/"

# قاموس لتخزين بيانات المستخدمين (محاولات، أرباح، رقم مطلوب)
# في تطبيق حقيقي، استخدم قاعدة بيانات. لكن للتجريب، هذا يكفي.
user_data = {}

# إرسال رسالة عادية
def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(URL + "sendMessage", json=data, timeout=10)
    except Exception as e:
        print(f"خطأ في إرسال الرسالة: {e}")

# الرد على استدعاء الزر
def answer_callback(callback_id):
    try:
        requests.post(URL + "answerCallbackQuery", json={"callback_query_id": callback_id}, timeout=10)
    except Exception as e:
        print(f"خطأ في الرد على الاستدعاء: {e}")

# تعديل رسالة موجودة
def edit_message(chat_id, message_id, text, reply_markup=None):
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(URL + "editMessageText", json=data, timeout=10)
    except Exception as e:
        print(f"خطأ في تعديل الرسالة: {e}")

# بدء لعبة جديدة للمستخدم
def start_game(chat_id):
    # الرقم المطلوب (1-6) عشوائي
    target_number = random.randint(1, 6)
    user_data[chat_id] = {
        "attempts_left": 5,      # المحاولات المتبقية
        "total_won": 0,          # إجمالي الأرباح بالـ USDT
        "target": target_number, # الرقم المطلوب للفوز
        "game_active": True
    }
    
    msg = f"🎲 *مرحباً بك في لعبة الحظ!*\n\n"
    msg += f"💰 قيمة اللفة الواحدة: *1 USDT*\n"
    msg += f"🎯 الهدف: احصل على الرقم *{target_number}*\n"
    msg += f"🏆 الجائزة: *10 USDT* إذا تطابق الرقم\n"
    msg += f"🔄 عدد المحاولات المجانية: *5*\n\n"
    msg += f"اضغط الزر أدناه للبدء..."
    
    keyboard = {
        "inline_keyboard": [
            [{"text": f"🎲 رمي النرد (1 USDT) - متبقي {5} محاولات", "callback_data": "roll"}]
        ]
    }
    send_message(chat_id, msg, reply_markup=keyboard)

# معالجة طلب رمي النرد
def roll_dice(chat_id, message_id, callback_id):
    # التحقق من وجود المستخدم في البيانات
    if chat_id not in user_data:
        answer_callback(callback_id)
        edit_message(chat_id, message_id, "⚠️ يبدو أن جلستك انتهت. أرسل /start للبدء من جديد.")
        return
    
    data = user_data[chat_id]
    
    # التحقق من أن اللعبة لا تزال نشطة
    if not data["game_active"]:
        answer_callback(callback_id)
        edit_message(chat_id, message_id, "📞 انتهت محاولاتك المجانية. تواصل مع الدعم: @SupportBot")
        return
    
    # التحقق من وجود محاولات متبقية
    if data["attempts_left"] <= 0:
        data["game_active"] = False
        answer_callback(callback_id)
        edit_message(chat_id, message_id, "📞 *انتهت محاولاتك المجانية*\n\nللحصول على محاولات إضافية، يرجى التواصل مع الدعم:\n@SupportBot")
        return
    
    # رمي النرد (رقم عشوائي 1-6)
    dice_result = random.randint(1, 6)
    data["attempts_left"] -= 1
    
    # التحقق من الفوز
    is_winner = (dice_result == data["target"])
    if is_winner:
        data["total_won"] += 10
        result_text = f"🎉 *فوز!* 🎉\nالرقم المطلوب: {data['target']}\nالرقم الذي حصلت عليه: {dice_result}\n💰 ربحت *10 USDT*!"
    else:
        result_text = f"😔 *للأسف* 😔\nالرقم المطلوب: {data['target']}\nالرقم الذي حصلت عليه: {dice_result}\n💔 لم تخسر شيئاً (المحاولة مجانية)."
    
    # بناء رسالة الحالة الجديدة
    status_msg = f"{result_text}\n\n"
    status_msg += f"📊 *حالتك الحالية:*\n"
    status_msg += f"🔄 المحاولات المتبقية: {data['attempts_left']} من 5\n"
    status_msg += f"💵 إجمالي الأرباح: *{data['total_won']} USDT*\n"
    
    # إذا انتهت المحاولات، ننهي اللعبة
    if data["attempts_left"] <= 0:
        data["game_active"] = False
        status_msg += f"\n📞 *انتهت محاولاتك المجانية* - تواصل مع الدعم للمزيد: @SupportBot"
        keyboard = None
    else:
        # زر للمحاولة التالية
        keyboard = {
            "inline_keyboard": [
                [{"text": f"🎲 رمي النرد (1 USDT) - متبقي {data['attempts_left']}", "callback_data": "roll"}]
            ]
        }
    
    # إرسال النتيجة
    answer_callback(callback_id)
    edit_message(chat_id, message_id, status_msg, reply_markup=keyboard)

# معالجة التحديثات الواردة من Telegram
def handle_updates(updates):
    for update in updates.get("result", []):
        # أمر /start
        if "message" in update and "text" in update["message"]:
            if update["message"]["text"] == "/start":
                chat_id = update["message"]["chat"]["id"]
                start_game(chat_id)
        
        # الضغط على زر
        elif "callback_query" in update:
            query = update["callback_query"]
            chat_id = query["message"]["chat"]["id"]
            message_id = query["message"]["message_id"]
            callback_id = query["id"]
            roll_dice(chat_id, message_id, callback_id)

# التشغيل الرئيسي
print("✅ بوت النرد (نظام 5 محاولات) يعمل الآن...")
print("البوت جاهز للاستخدام - أرسل /start للبدء")

last_update_id = 0
while True:
    try:
        response = requests.get(URL + "getUpdates", params={"offset": last_update_id + 1, "timeout": 30}, timeout=35)
        updates = response.json()
        
        if updates.get("ok") and updates.get("result"):
            handle_updates(updates)
            last_update_id = updates["result"][-1]["update_id"]
            
    except requests.exceptions.Timeout:
        continue
    except Exception as e:
        print(f"خطأ: {e}")
        time.sleep(5)
    
    time.sleep(1)