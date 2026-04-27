import requests
import json
import time
import random
import sqlite3
from database import *
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================== إعدادات البوت ==================
TOKEN = "8650482506:AAFswJ6DEtb1O_x5sUcUZNlqu5HbeQgQ2bI"
URL = f"https://api.telegram.org/bot{TOKEN}/"

# ================== معرف المشرف ==================
# ⚠️ ضع معرف تليغرام الخاص بك هنا (أرسل لـ @userinfobot لتعرف رقمك)
ADMIN_ID = 8317757440  # غير هذا الرقم إلى معرفك الحقيقي

def is_admin(user_id):
    return user_id == ADMIN_ID

# ================== دوال مساعدة ==================
def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(URL + "sendMessage", json=data, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}")

def edit_message(chat_id, message_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(URL + "editMessageText", json=data, timeout=10)
    except Exception as e:
        print(f"Error editing message: {e}")

def answer_callback(callback_id):
    try:
        requests.post(URL + "answerCallbackQuery", json={"callback_query_id": callback_id}, timeout=10)
    except Exception as e:
        print(f"Error answering callback: {e}")

# ================== لوحة الأزرار الرئيسية ==================
def get_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎲 ابدأ اللعب", "callback_data": "play"}],
            [{"text": "💰 رصيدي", "callback_data": "balance"}],
            [{"text": "📊 الترتيب", "callback_data": "leaderboard"}]
        ]
    }

# ================== دوال اللعبة ==================
def start_game(chat_id, user_id, username, first_name):
    create_user(user_id, username, first_name)
    msg = "🎲 *مرحباً في لعبة النرد!*\n\nاختر أحد الخيارات:"
    send_message(chat_id, msg, reply_markup=get_main_keyboard())

def show_balance(chat_id, message_id, user_id):
    user = get_user(user_id)
    if user:
        msg = f"💰 *رصيدك الحالي:* {user[3]} Coin\n"
        msg += f"🎲 *عدد اللفات:* {user[4]}\n"
        msg += f"🏆 *عدد مرات الفوز:* {user[5]}"
        edit_message(chat_id, message_id, msg, reply_markup=get_main_keyboard())
    else:
        edit_message(chat_id, message_id, "❌ حدث خطأ، حاول مرة أخرى", reply_markup=get_main_keyboard())

def show_leaderboard(chat_id, message_id):
    top_users = get_top_users(10)
    if top_users:
        msg = "🏆 *قائمة الأغنياء:*\n\n"
        for i, user in enumerate(top_users, 1):
            name = user[2] or user[1] or str(user[0])
            coins = user[3]
            msg += f"{i}. {name} — {coins} Coin\n"
        edit_message(chat_id, message_id, msg, reply_markup=get_main_keyboard())
    else:
        edit_message(chat_id, message_id, "لا يوجد مستخدمون بعد.", reply_markup=get_main_keyboard())

def perform_roll(chat_id, message_id, user_id):
    user = get_user(user_id)
    if not user:
        edit_message(chat_id, message_id, "❌ حدث خطأ، أعد إرسال /start", reply_markup=get_main_keyboard())
        return
    
    coins = user[3]
    cost = int(get_setting("cost_per_roll"))
    
    if coins < cost:
        msg = f"❌ رصيدك لا يكفي!\nتحتاج {cost} Coin للعب.\nرصيدك الحالي: {coins} Coin"
        edit_message(chat_id, message_id, msg, reply_markup=get_main_keyboard())
        return
    
    # خصم التكلفة
    new_coins = coins - cost
    
    # تحديد الفوز
    win_prob = float(get_setting("win_probability"))
    is_win = random.random() < win_prob
    
    # رمي النرد
    dice_result = random.randint(1, 6)
    
    if is_win:
        reward = int(get_setting("reward_coins"))
        new_coins += reward
        increment_wins_count(user_id)
        result_text = f"🎉 *فوز!* 🎉\n\nحصلت على: {dice_result}\nربحت {reward} Coin إضافية!"
    else:
        result_text = f"😔 *خسارة* 😔\n\nحصلت على: {dice_result}\nحظاً أوفر المرة القادمة."
    
    # تحديث البيانات
    update_user_coins(user_id, new_coins)
    increment_rolls_count(user_id)
    add_roll_log(user_id, user[4] + 1, dice_result, is_win, coins, new_coins)
    
    msg = f"{result_text}\n\n💰 رصيدك الآن: {new_coins} Coin\n💸 تكلفة اللفة: {cost} Coin"
    edit_message(chat_id, message_id, msg, reply_markup=get_main_keyboard())

# ================== أوامر المشرف السرية ==================
def handle_admin_commands(chat_id, text):
    # تغيير نسبة الفوز: /win 30
    if text.startswith("/win"):
        try:
            percent = float(text.split()[1])
            set_setting("win_probability", str(percent / 100))
            send_message(chat_id, f"✅ تم تغيير نسبة الفوز إلى {percent}%")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /win 30")
            return True
    
    # تغيير مكافأة الفوز: /reward 10
    elif text.startswith("/reward"):
        try:
            reward = int(text.split()[1])
            set_setting("reward_coins", str(reward))
            send_message(chat_id, f"✅ تم تغيير مكافأة الفوز إلى {reward} Coin")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /reward 10")
            return True
    
    # تغيير تكلفة اللفة: /cost 1
    elif text.startswith("/cost"):
        try:
            cost = int(text.split()[1])
            set_setting("cost_per_roll", str(cost))
            send_message(chat_id, f"✅ تم تغيير تكلفة اللفة إلى {cost} Coin")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /cost 1")
            return True
    
    # إضافة رصيد: /add 123456789 100
    elif text.startswith("/add"):
        try:
            parts = text.split()
            target_id = int(parts[1])
            amount = int(parts[2])
            user = get_user(target_id)
            if user:
                new_coins = user[3] + amount
                update_user_coins(target_id, new_coins)
                send_message(chat_id, f"✅ تم إضافة {amount} Coin للمستخدم {target_id}\n💰 رصيده الآن: {new_coins} Coin")
            else:
                send_message(chat_id, f"❌ المستخدم {target_id} غير موجود")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /add [معرف_المستخدم] [الكمية]")
            return True
    
    # تعيين رصيد: /set 123456789 500
    elif text.startswith("/set"):
        try:
            parts = text.split()
            target_id = int(parts[1])
            amount = int(parts[2])
            user = get_user(target_id)
            if user:
                update_user_coins(target_id, amount)
                send_message(chat_id, f"✅ تم تعيين رصيد المستخدم {target_id} إلى {amount} Coin")
            else:
                send_message(chat_id, f"❌ المستخدم {target_id} غير موجود")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /set [معرف_المستخدم] [الرصيد]")
            return True
    
    # عرض الإعدادات: /settings
    elif text == "/settings":
        win = float(get_setting("win_probability")) * 100
        reward = get_setting("reward_coins")
        cost = get_setting("cost_per_roll")
        msg = f"📊 *الإعدادات الحالية:*\n\n"
        msg += f"🎯 نسبة الفوز: {win}%\n"
        msg += f"💰 مكافأة الفوز: {reward} Coin\n"
        msg += f"💸 تكلفة اللفة: {cost} Coin"
        send_message(chat_id, msg)
        return True
    
    # عرض الإحصائيات: /stats
    elif text == "/stats":
        total_users = get_total_users()
        total_rolls = get_total_rolls()
        msg = f"📈 *إحصائيات البوت:*\n\n"
        msg += f"👥 عدد المستخدمين: {total_users}\n"
        msg += f"🎲 إجمالي اللفات: {total_rolls}"
        send_message(chat_id, msg)
        return True
    
    # عرض المستخدمين: /users
    elif text == "/users":
        users = get_all_users()
        if users:
            msg = "👥 *قائمة المستخدمين:*\n\n"
            for u in users:
                name = u[1] or u[2] or str(u[0])
                msg += f"🆔 `{u[0]}` | {name} | 💰 {u[3]} Coin\n"
            send_message(chat_id, msg)
        else:
            send_message(chat_id, "لا يوجد مستخدمون بعد")
        return True
    
    # مساعدة المشرف: /admin
    elif text == "/admin":
        msg = """
🔐 *أوامر المشرف السرية*

🎯 *التحكم في اللعبة:*
/win 30 - تغيير نسبة الفوز (30%)
/reward 10 - تغيير مكافأة الفوز
/cost 1 - تغيير تكلفة اللفة

💰 *التحكم في الأرصدة:*
/add 123456789 100 - إضافة رصيد
/set 123456789 500 - تعيين رصيد محدد

📊 *عرض المعلومات:*
/settings - عرض الإعدادات الحالية
/stats - عرض إحصائيات البوت
/users - عرض قائمة المستخدمين

📌 *للبحث عن معرف المستخدم:*
اطلب من المستخدم إرسال أي رسالة، ثم استخدم /users
"""
        send_message(chat_id, msg)
        return True
    
    return False

# ================== معالجة الأزرار ==================
def handle_callback(query):
    chat_id = query["message"]["chat"]["id"]
    message_id = query["message"]["message_id"]
    callback_id = query["id"]
    data = query["data"]
    user = query["from"]
    user_id = user["id"]
    
    answer_callback(callback_id)
    
    if data == "play":
        perform_roll(chat_id, message_id, user_id)
    elif data == "balance":
        show_balance(chat_id, message_id, user_id)
    elif data == "leaderboard":
        show_leaderboard(chat_id, message_id)

# ================== معالجة التحديثات ==================
def handle_updates(updates):
    for update in updates.get("result", []):
        # معالجة الرسائل النصية
        if "message" in update and "text" in update["message"]:
            text = update["message"]["text"]
            chat_id = update["message"]["chat"]["id"]
            user_id = update["message"]["from"]["id"]
            
            if text == "/start":
                user = update["message"]["from"]
                start_game(chat_id, user["id"], user.get("username", ""), user.get("first_name", ""))
            else:
                # أوامر المشرف (تعمل فقط إذا كان المرسل هو المشرف)
                if is_admin(user_id):
                    handle_admin_commands(chat_id, text)
        
        # معالجة الأزرار
        elif "callback_query" in update:
            handle_callback(update["callback_query"])

# ================== خادم ويب وهمي لإرضاء Render ==================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass  # تعطيل السجلات

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', 10000), DummyHandler)
    server.serve_forever()

Thread(target=run_dummy_server, daemon=True).start()

# ================== تشغيل البوت ==================
print("✅ بوت النرد يعمل...")
print("✅ الأوامر السرية للمشرف: /admin")
print("✅ انتظر المستخدمين...")

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
        print(f"Error: {e}")
        time.sleep(5)
    
    time.sleep(1)
