import requests
import json
import time
import random

# التوكن الخاص بالبوت
TOKEN = "8650482506:AAFswJ6DEtb1O_x5sUcUZNlqu5HbeQgQ2bI"
URL = f"https://api.telegram.org/bot{TOKEN}/"

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
def edit_message(chat_id, message_id, text, reply_markup):
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(reply_markup)
    }
    try:
        requests.post(URL + "editMessageText", json=data, timeout=10)
    except Exception as e:
        print(f"خطأ في تعديل الرسالة: {e}")

# معالجة التحديثات الواردة
def handle_updates(updates):
    for update in updates.get("result", []):
        # معالجة أمر /start
        if "message" in update and "text" in update["message"] and update["message"]["text"] == "/start":
            chat_id = update["message"]["chat"]["id"]
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🎲 رمي النرد", "callback_data": "roll"}]
                ]
            }
            send_message(chat_id, "🎲 *مرحباً بك في لعبة النرد!*\nاضغط الزر أدناه لرمي النرد.", reply_markup=keyboard)
        
        # معالجة الضغط على الزر
        elif "callback_query" in update:
            query = update["callback_query"]
            chat_id = query["message"]["chat"]["id"]
            message_id = query["message"]["message_id"]
            callback_id = query["id"]
            
            # رمي النرد
            dice = random.randint(1, 6)
            
            # رسائل حسب الرقم
            if dice == 1:
                msg = "😭 *يا خسارة!* طلعلك **1** ... جرب حظك مرة ثانية"
            elif dice == 6:
                msg = "🎉🎊 *مبروك!* طلعلك **6** ... أنت محظوظ اليوم!"
            else:
                msg = f"🎲 رميت النرد... النتيجة: **{dice}**\n\nاضغط الزر لتجربة حظك مجدداً."
            
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🎲 رمي مجدداً", "callback_data": "roll"}]
                ]
            }
            
            # الإجابة على الاستدعاء (لإزالة حالة "التحميل" على الزر)
            answer_callback(callback_id)
            # تعديل الرسالة بالنتيجة
            edit_message(chat_id, message_id, msg, keyboard)

# التشغيل الرئيسي
print("✅ بوت النرد يعمل الآن...")
print(f"البوت: https://t.me/... (استخدم /start للبدء)")

last_update_id = 0
while True:
    try:
        # جلب التحديثات الجديدة
        response = requests.get(URL + "getUpdates", params={"offset": last_update_id + 1, "timeout": 30}, timeout=35)
        updates = response.json()
        
        if updates.get("ok") and updates.get("result"):
            handle_updates(updates)
            # تحديث آخر ID تم معالجته
            last_update_id = updates["result"][-1]["update_id"]
            
    except requests.exceptions.Timeout:
        # الوقت الطويل متوقع، نكمل
        continue
    except Exception as e:
        print(f"خطأ عام: {e}")
        time.sleep(5)
    
    time.sleep(1)