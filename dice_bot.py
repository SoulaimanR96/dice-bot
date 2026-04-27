import requests
import json
import time
import random
from database import *
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# ================== إعدادات البوت ==================
TOKEN = "8650482506:AAFswJ6DEtb1O_x5sUcUZNlqu5HbeQgQ2bI"
URL = f"https://api.telegram.org/bot{TOKEN}/"

# ================== معرف المشرف ==================
ADMIN_ID = 8317757440  # ⚠️ ضع معرفك الحقيقي هنا

def is_admin(user_id):
    return user_id == ADMIN_ID

# ================== مضاعفات الفوز حسب النرد ==================
WIN_MULTIPLIERS = {
    1: 2,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 10
}

# جوائز الجاكبوت المحتملة
JACKPOT_MULTIPLIERS = [20, 30, 50, 100]

# أشكال النرد
DICE_FACES = {
    1: "⚀",
    2: "⚁",
    3: "⚂",
    4: "⚃",
    5: "⚄",
    6: "⚅"
}

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

# ================== أزرار اللعبة ==================
BET_OPTIONS = [1, 2, 5, 10, 25, 30, 50, 100]

def get_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎲 ابدأ اللعب", "callback_data": "play"}],
            [{"text": "💰 رصيدي", "callback_data": "balance"}, {"text": "📊 الترتيب", "callback_data": "leaderboard"}],
            [{"text": "📈 حالة الـ Pool", "callback_data": "pool_status"}, {"text": "❓ المساعدة", "callback_data": "help"}]
        ]
    }

def get_bet_keyboard():
    buttons = []
    row = []
    for i, bet in enumerate(BET_OPTIONS):
        row.append({"text": f"💰 {bet} Coin", "callback_data": f"bet_{bet}"})
        if (i + 1) % 4 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([{"text": "🔙 القائمة الرئيسية", "callback_data": "menu"}])
    return {"inline_keyboard": buttons}

def get_play_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎲 رمي النرد مرة أخرى 🎲", "callback_data": "play"}],
            [{"text": "💰 تغيير الرهان", "callback_data": "change_bet"}, {"text": "🏠 الرئيسية", "callback_data": "menu"}]
        ]
    }

# ================== دوال اللعبة ==================
def start_game(chat_id, user_id, username, first_name):
    create_user(user_id, username, first_name)
    pool_total, pool_payout, pool_percent = get_pool_data()
    msg = f"""🎲 *مرحباً بك في لعبة Pool النرد!* 🎲

⚡ *نظام اللعب:*
• اللاعبون يتنافسون على Pool واحد
• نسبة أرباح الـ Pool حالياً: *{pool_percent}%*
• المضاعفات: ×2 إلى ×10 حسب الرقم

💰 *حالة الـ Pool:*
└─ إجمالي الرهانات: {pool_total} Coin

🎯 *اختر رهانك وابدأ* 🎯"""
    send_message(chat_id, msg, reply_markup=get_menu_keyboard())

def show_balance(chat_id, message_id, user_id):
    user = get_user(user_id)
    if user:
        coins = user[3]
        rolls = user[4]
        wins = user[5]
        total_bets = user[6] if len(user) > 6 else 0
        total_wins = user[7] if len(user) > 7 else 0
        
        msg = f"""💰 *رصيدك:* {coins} Coin

📊 *إحصائياتك:*
├─ 🎲 اللفات: {rolls}
├─ 🏆 الفوز: {wins}
├─ 📈 نسبة الفوز: {round(wins/rolls*100, 1) if rolls > 0 else 0}%
├─ 💰 إجمالي الرهانات: {total_bets} Coin
└─ 💎 إجمالي الأرباح: {total_wins} Coin"""
        
        edit_message(chat_id, message_id, msg, reply_markup=get_menu_keyboard())
    else:
        edit_message(chat_id, message_id, "❌ حدث خطأ", reply_markup=get_menu_keyboard())

def show_leaderboard(chat_id, message_id):
    top_users = get_top_users(10)
    if top_users:
        msg = "🏆 *قائمة الأغنياء* 🏆\n\n"
        medals = ["🥇", "🥈", "🥉", "📌", "📌", "📌", "📌", "📌", "📌", "📌"]
        for i, user in enumerate(top_users[:10], 1):
            name = user[2] or user[1] or f"مستخدم {user[0]}"
            if len(name) > 15:
                name = name[:12] + "..."
            msg += f"{medals[i-1]} *{i}.* {name}\n   └─ 💰 {user[3]} Coin | 🏆 {user[4]} فوز\n\n"
        edit_message(chat_id, message_id, msg, reply_markup=get_menu_keyboard())
    else:
        edit_message(chat_id, message_id, "📭 لا يوجد مستخدمون بعد", reply_markup=get_menu_keyboard())

def show_pool_status(chat_id, message_id):
    pool_total, pool_payout, pool_percent = get_pool_data()
    available_payout = int(pool_total * pool_percent / 100)
    remaining = available_payout - pool_payout
    
    msg = f"""📊 *حالة الـ Pool* 📊

💰 إجمالي الرهانات: {pool_total} Coin
🎯 نسبة الأرباح: {pool_percent}%
💎 إجمالي الأرباح الموزعة: {pool_payout} Coin
✨ الأرباح المتبقية: {max(0, remaining)} Coin

⚡ *مضاعفات الفوز:*
• رقم 1-2: ×2
• رقم 3: ×3
• رقم 4: ×4
• رقم 5: ×5
• رقم 6: ×10

🎰 *الجاكبوت:* فرصة 1% للفوز بـ ×20 إلى ×100!"""
    edit_message(chat_id, message_id, msg, reply_markup=get_menu_keyboard())

def show_help(chat_id, message_id):
    msg = """❓ *كيفية اللعب* ❓

🎲 *الهدف:*
اربح أكبر قدر من الـ Pool المشترك!

⚙️ *طريقة اللعب:*
1. اختر مبلغ الرهان
2. ار النرد
3. الرقم يحدد مضاعف فوزك

💰 *نظام Pool:*
• جميع الرهانات تُجمع في Pool واحد
• نسبة من الـ Pool توزع على الفائزين
• اللاعبون يتنافسون على الـ Pool

🎯 *حظاً موفقاً!* 🎯"""
    edit_message(chat_id, message_id, msg, reply_markup=get_menu_keyboard())

def show_bet_selection(chat_id, message_id, user_id):
    user = get_user(user_id)
    if not user:
        edit_message(chat_id, message_id, "❌ حدث خطأ", reply_markup=get_menu_keyboard())
        return
    
    pool_total, pool_payout, pool_percent = get_pool_data()
    msg = f"""🎲 *اختر رهانك* 🎲

💰 رصيدك: {user[3]} Coin
📊 Pool الحالي: {pool_total} Coin
🎯 نسبة الأرباح: {pool_percent}%

✨ *اختر مبلغ الرهان:* ✨"""
    edit_message(chat_id, message_id, msg, reply_markup=get_bet_keyboard())

def perform_roll(chat_id, message_id, user_id, bet_amount):
    user = get_user(user_id)
    if not user:
        return False
    
    coins = user[3]
    if coins < bet_amount:
        edit_message(chat_id, message_id, f"❌ رصيدك غير كافٍ!\n💰 رصيدك: {coins} Coin", reply_markup=get_bet_keyboard())
        return False
    
    # خصم الرهان من اللاعب
    new_coins = coins - bet_amount
    update_user_coins(user_id, new_coins)
    update_total_bets(user_id, bet_amount)
    
    # إضافة الرهان إلى Pool
    update_pool_bets(bet_amount)
    pool_total, pool_payout, pool_percent = get_pool_data()
    available_payout = int(pool_total * pool_percent / 100)
    remaining_payout = available_payout - pool_payout
    
    # تأثير الرمي
    for i in range(2):
        frame = "🎲 *جاري الرمي* 🎲\n" + "".join(random.choice(["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]) for _ in range(3))
        edit_message(chat_id, message_id, frame)
        time.sleep(0.3)
    
    # رمي النرد
    dice_result = random.randint(1, 6)
    dice_face = DICE_FACES[dice_result]
    multiplier = WIN_MULTIPLIERS[dice_result]
    base_win = bet_amount * multiplier
    
    # التحقق من الجاكبوت (1% فرصة)
    jackpot_chance = get_jackpot_chance() / 100
    is_jackpot = random.random() < jackpot_chance
    
    if is_jackpot:
        # اختيار مضاعف عشوائي للجاكبوت
        jackpot_multiplier = random.choice(JACKPOT_MULTIPLIERS)
        win_amount = bet_amount * jackpot_multiplier
        
        # خصم الجائزة من Pool
        jackpot_percent = get_jackpot_percentage() / 100
        jackpot_from_pool = int(pool_total * jackpot_percent)
        win_amount = min(win_amount, jackpot_from_pool)
        
        if win_amount <= remaining_payout:
            remaining_payout -= win_amount
            update_pool_payout(pool_payout + win_amount)
            new_coins += win_amount
            update_user_coins(user_id, new_coins)
            increment_wins_count(user_id, win_amount)
            add_jackpot_log(user_id, bet_amount, win_amount, jackpot_multiplier)
            
            result_text = f"""🎰 *الجاكبوت!* 🎰

┌─ 🎲 رقم الحظ: {dice_face} **{dice_result}**
├─ 💰 الرهان: {bet_amount} Coin
├─ 🎯 المضاعف: ×{jackpot_multiplier}
├─ 💎 المكسب: +{win_amount} Coin
└─ 💰 الرصيد الجديد: {new_coins} Coin

✨ *مبروك! فوز كبير!* ✨"""
        else:
            result_text = f"🎲 *النتيجة:* {dice_face} {dice_result}\n💸 خسارة: -{bet_amount} Coin\n💰 رصيدك: {new_coins} Coin"
    else:
        # الفوز العادي
        if base_win <= remaining_payout:
            remaining_payout -= base_win
            update_pool_payout(pool_payout + base_win)
            new_coins += base_win
            increment_wins_count(user_id, base_win)
            
            result_text = f"""🎉 *فوز!* 🎉

┌─ 🎲 الرقم: {dice_face} **{dice_result}**
├─ 💰 الرهان: {bet_amount} Coin
├─ 🎯 المضاعف: ×{multiplier}
├─ 💎 المكسب: +{base_win} Coin
└─ 💰 الرصيد الجديد: {new_coins} Coin"""
        else:
            result_text = f"🎲 *النتيجة:* {dice_face} {dice_result}\n💸 خسارة: -{bet_amount} Coin\n💰 رصيدك: {new_coins} Coin"
    
    # تحديث رصيد اللاعب
    update_user_coins(user_id, new_coins)
    increment_rolls_count(user_id)
    add_roll_log(user_id, user[4] + 1, bet_amount, dice_result, base_win <= remaining_payout, base_win if base_win <= remaining_payout else 0, coins, new_coins)
    
    final_msg = f"{result_text}\n\n📊 *Pool:* {pool_total} Coin | متبقي: {max(0, remaining_payout)} Coin\n\n✨ *هل تريد اللعب مرة أخرى؟* ✨"
    edit_message(chat_id, message_id, final_msg, reply_markup=get_play_keyboard())
    return True

# ================== أوامر المشرف ==================
def handle_admin_commands(chat_id, text):
    if text.startswith("/set_pool"):
        try:
            percent = float(text.split()[1])
            percent = max(10, min(80, percent))
            set_pool_percentage(percent)
            send_message(chat_id, f"✅ تم تغيير نسبة Pool إلى {percent}%")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /set_pool 30")
            return True
    
    if text.startswith("/add"):
        try:
            parts = text.split()
            target_id = int(parts[1])
            amount = int(parts[2])
            user = get_user(target_id)
            if user:
                new_coins = user[3] + amount
                update_user_coins(target_id, new_coins)
                send_message(chat_id, f"✅ تم إضافة {amount} Coin للمستخدم {target_id}")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /add [ID] [المبلغ]")
            return True
    
    if text == "/reset_pool":
        reset_pool()
        send_message(chat_id, "✅ تم إعادة تعيين Pool")
        return True
    
    if text == "/pool_stats":
        total_bets, total_payout, pool_percent = get_pool_data()
        msg = f"📊 *إحصائيات Pool:*\n💰 إجمالي الرهانات: {total_bets}\n💎 الأرباح الموزعة: {total_payout}\n🎯 النسبة: {pool_percent}%"
        send_message(chat_id, msg)
        return True
    
    if text == "/admin":
        msg = """🔐 *أوامر المشرف*

/set_pool 30 - تغيير نسبة Pool
/add [ID] [مبلغ] - إضافة رصيد
/reset_pool - إعادة تعيين Pool
/pool_stats - إحصائيات Pool"""
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
        show_bet_selection(chat_id, message_id, user_id)
    elif data == "change_bet":
        show_bet_selection(chat_id, message_id, user_id)
    elif data.startswith("bet_"):
        bet_amount = int(data.split("_")[1])
        perform_roll(chat_id, message_id, user_id, bet_amount)
    elif data == "balance":
        show_balance(chat_id, message_id, user_id)
    elif data == "leaderboard":
        show_leaderboard(chat_id, message_id)
    elif data == "pool_status":
        show_pool_status(chat_id, message_id)
    elif data == "menu":
        start_game(chat_id, user_id, user.get("username", ""), user.get("first_name", ""))
    elif data == "help":
        show_help(chat_id, message_id)

# ================== معالجة التحديثات ==================
def handle_updates(updates):
    for update in updates.get("result", []):
        if "message" in update and "text" in update["message"]:
            text = update["message"]["text"]
            chat_id = update["message"]["chat"]["id"]
            user_id = update["message"]["from"]["id"]
            
            if text == "/start":
                user = update["message"]["from"]
                start_game(chat_id, user["id"], user.get("username", ""), user.get("first_name", ""))
            elif is_admin(user_id):
                handle_admin_commands(chat_id, text)
        
        elif "callback_query" in update:
            handle_callback(update["callback_query"])

# ================== خادم ويب ==================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Pool Bot is running!")
    def log_message(self, format, *args):
        pass

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', 10000), DummyHandler)
    server.serve_forever()

Thread(target=run_dummy_server, daemon=True).start()

# ================== تشغيل البوت ==================
print("=" * 50)
print("🎲 بوت Pool النرد يعمل... 🎲")
print("=" * 50)
print("✅ نظام Pool: جميع اللاعبين يتنافسون")
print("✅ نسبة الجاكبوت: 1%")
print("✅ نسبة Pool قابلة للتغيير")
print("=" * 50)

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
        print(f"⚠️ خطأ: {e}")
        time.sleep(5)
    time.sleep(1)
