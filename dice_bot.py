import requests
import json
import time
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from database import *

TOKEN = "8650482506:AAFswJ6DEtb1O_x5sUcUZNlqu5HbeQgQ2bI"
URL = f"https://api.telegram.org/bot{TOKEN}/"

# إعدادات من قاعدة البيانات
def get_win_probability(): return float(get_setting("win_probability"))
def get_reward_coins(): return int(get_setting("reward_coins"))
def get_cost_per_roll(): return int(get_setting("cost_per_roll"))

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup: data["reply_markup"] = json.dumps(reply_markup)
    try: requests.post(URL + "sendMessage", json=data, timeout=10)
    except: pass

def edit_message(chat_id, message_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup: data["reply_markup"] = json.dumps(reply_markup)
    try: requests.post(URL + "editMessageText", json=data, timeout=10)
    except: pass

def answer_callback(callback_id):
    try: requests.post(URL + "answerCallbackQuery", json={"callback_query_id": callback_id}, timeout=10)
    except: pass

def get_main_keyboard():
    return {"inline_keyboard": [[{"text": "🎲 ابدأ اللعب", "callback_data": "play"}], [{"text": "💰 رصيدي", "callback_data": "balance"}], [{"text": "📊 الترتيب", "callback_data": "leaderboard"}]]}

def start_game(chat_id, user_id, username, first_name):
    create_user(user_id, username, first_name)
    send_message(chat_id, "🎲 *مرحباً في لعبة الأصدقاء!*", reply_markup=get_main_keyboard())

def show_balance(chat_id, message_id, user_id):
    user = get_user(user_id)
    if user:
        msg = f"💰 *رصيدك:* {user[3]} Coin\n🎲 *اللفات:* {user[4]}\n🏆 *الفوز:* {user[5]}"
        edit_message(chat_id, message_id, msg, reply_markup=get_main_keyboard())

def show_leaderboard(chat_id, message_id):
    top = get_top_users(10)
    if top:
        msg = "🏆 *الترتيب:*\n" + "\n".join([f"{i}. {u[2] or u[1] or u[0]} — {u[3]} Coin" for i, u in enumerate(top, 1)])
        edit_message(chat_id, message_id, msg, reply_markup=get_main_keyboard())
    else:
        edit_message(chat_id, message_id, "لا يوجد مستخدمون بعد.", reply_markup=get_main_keyboard())

def perform_roll(chat_id, message_id, user_id):
    user = get_user(user_id)
    if not user: return
    coins = user[3]
    cost = get_cost_per_roll()
    if coins < cost:
        edit_message(chat_id, message_id, f"❌ رصيدك {coins} Coin، تحتاج {cost} Coin للعب.", reply_markup=get_main_keyboard())
        return
    new_coins = coins - cost
    is_win = random.random() < get_win_probability()
    result = random.randint(1, 6)
    if is_win:
        reward = get_reward_coins()
        new_coins += reward
        increment_wins_count(user_id)
        msg = f"🎉 *فوز!* النتيجة: {result}\nربحت {reward} Coin!"
    else:
        msg = f"😔 *خسارة* النتيجة: {result}"
    update_user_coins(user_id, new_coins)
    increment_rolls_count(user_id)
    add_roll_log(user_id, user[4]+1, result, is_win, coins, new_coins)
    msg += f"\n💰 رصيدك: {new_coins} Coin"
    edit_message(chat_id, message_id, msg, reply_markup=get_main_keyboard())

def handle_callback(query):
    chat_id = query["message"]["chat"]["id"]
    message_id = query["message"]["message_id"]
    user = query["from"]
    answer_callback(query["id"])
    if query["data"] == "play": perform_roll(chat_id, message_id, user["id"])
    elif query["data"] == "balance": show_balance(chat_id, message_id, user["id"])
    elif query["data"] == "leaderboard": show_leaderboard(chat_id, message_id)

def handle_updates(updates):
    for update in updates.get("result", []):
        if "message" in update and "text" in update["message"] and update["message"]["text"] == "/start":
            u = update["message"]["from"]
            start_game(update["message"]["chat"]["id"], u["id"], u.get("username", ""), u.get("first_name", ""))
        elif "callback_query" in update:
            handle_callback(update["callback_query"])

# خادم ويب وهمي لإرضاء Render
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
threading.Thread(target=lambda: HTTPServer(('0.0.0.0', 10000), DummyHandler).serve_forever(), daemon=True).start()

print("✅ البوت يعمل...")
last_id = 0
while True:
    try:
        resp = requests.get(URL + "getUpdates", params={"offset": last_id + 1, "timeout": 30}, timeout=35)
        updates = resp.json()
        if updates.get("ok") and updates.get("result"):
            handle_updates(updates)
            last_id = updates["result"][-1]["update_id"]
    except: pass
    time.sleep(1)