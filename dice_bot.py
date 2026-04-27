import requests
import json
import time
import random
from database import *
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

TOKEN = "8650482506:AAFswJ6DEtb1O_x5sUcUZNlqu5HbeQgQ2bI"
URL = f"https://api.telegram.org/bot{TOKEN}/"

# إعدادات من قاعدة البيانات
def get_win_probability():
    return float(get_setting("win_probability"))

def get_reward_coins():
    return int(get_setting("reward_coins"))

def get_cost_per_roll():
    return int(get_setting("cost_per_roll"))

# دوال مساعدة
def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(URL + "sendMessage", json=data, timeout=10)
    except Exception as e:
        print(f"Error: {e}")

def edit_message(chat_id, message_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(URL + "editMessageText", json=data, timeout=10)
    except Exception as e:
        print(f"Error: {e}")

def answer_callback(callback_id):
    try:
        requests.post(URL + "answerCallbackQuery", json={"callback_query_id": callback_id}, timeout=10)
    except Exception as e:
        print(f"Error: {e}")

# لوحة الأزرار الرئيسية
def get_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎲 ابدأ اللعب", "callback_data": "play"}],
            [{"text": "💰 رصيدي", "callback_data": "balance"}],
            [{"text": "📊 الترتيب", "callback_data": "leaderboard"}]
        ]
    }

# بدء اللعبة
def start_game(chat_id, user_id, username, first_name):
    create_user(user_id, username, first_name)
    msg = "🎲 *مرحباً في لعبة الأصدقاء!*\nاختر أحد الخيارات:"
    send_message(chat_id, msg, reply_markup=get_main_keyboard())

# عرض الرصيد
def show_balance(chat_id, message_id, user_id):
    user = get_user(user_id)
    if user:
        coins = user[3]
        rolls = user[4]
        wins = user[5]
        msg = f"💰 *رصيدك الحالي:* {coins} Coin\n"
        msg += f"🎲 *عدد اللفات:* {rolls}\n"
        msg += f"🏆 *عدد مرات الفوز:* {wins}"
        edit_message(chat_id, message_id, msg, reply_markup=get_main_keyboard())
    else:
        edit_message(chat_id, message_id, "❌ مستخدم غير موجود.", reply_markup=get_main_keyboard())

# عرض الترتيب
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

# تنفيذ الرمية
def perform_roll(chat_id, message_id, user_id):
    user = get_user(user_id)
    if not user:
        edit_message(chat_id, message_id, "❌ حدث خطأ. أعد إرسال /start", reply_markup=get_main_keyboard())
        return
    
    coins = user[3]
    cost = get_cost_per_roll()
    
    if coins < cost:
        msg = f"❌ رصيدك لا يكفي!\nتحتاج {cost} Coin للعب.\nرصيدك الحالي: {coins} Coin"
        edit_message(chat_id, message_id, msg, reply_markup=get_main_keyboard())
        return
    
    # خصم تكلفة اللعبة
    new_coins = coins - cost
    
    # تحديد الفوز بناءً على نسبة الربح
    win_prob = get_win_probability()
    is_win = random.random() < win_prob
    
    roll_result = random.randint(1, 6)
    
    if is_win:
        reward = get_reward_coins()
        new_coins += reward
        increment_wins_count(user_id)
        result_text = f"🎉 *فوز!* 🎉\nحصلت على: {roll_result}\nربحت {reward} Coin إضافية!"
    else:
        result_text = f"😔 *خسارة* 😔\nحصلت على: {roll_result}\nحظاً أوفر المرة القادمة."
    
    # تحديث الرصيد وتسجيل
    update_user_coins(user_id, new_coins)
    increment_rolls_count(user_id)
    add_roll_log(user_id, user[4] + 1, roll_result, is_win, coins, new_coins)
    
    msg = f"{result_text}\n\n💰 رصيدك الآن: {new_coins} Coin\n"
    msg += f"🎲 تكلفة اللفة: {cost} Coin"
    
    edit_message(chat_id, message_id, msg, reply_markup=get_main_keyboard())

# معالجة الأزرار
def handle_callback(query):
    chat_id = query["message"]["chat"]["id"]
    message_id = query["message"]["message_id"]
    callback_id = query["id"]
    data = query["data"]
    user = query["from"]
    user_id = user["id"]
    username = user.get("username", "")
    first_name = user.get("first_name", "")
    
    answer_callback(callback_id)
    
    if data == "play":
        perform_roll(chat_id, message_id, user_id)
    elif data == "balance":
        show_balance(chat_id, message_id, user_id)
    elif data == "leaderboard":
        show_leaderboard(chat_id, message_id)
    elif data == "back_to_menu":
        msg = "🎲 *مرحباً في لعبة الأصدقاء!*\nاختر أحد الخيارات:"
        edit_message(chat_id, message_id, msg, reply_markup=get_main_keyboard())

# معالجة الرسائل
def handle_updates(updates):
    for update in updates.get("result", []):
        if "message" in update and "text" in update["message"]:
            if update["message"]["text"] == "/start":
                chat_id = update["message"]["chat"]["id"]
                user = update["message"]["from"]
                start_game(chat_id, user["id"], user.get("username", ""), user.get("first_name", ""))
        elif "callback_query" in update:
            handle_callback(update["callback_query"])

# خادم ويب وهمي لإرضاء Render
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', 10000), DummyHandler)
    server.serve_forever()

Thread(target=run_dummy_server, daemon=True).start()

# تشغيل البوت
print("✅ بوت الأصدقاء يعمل...")
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