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

# ================== مضاعفات الفوز ==================
WIN_MULTIPLIERS = {
    1: 2,
    2: 2,
    3: 3,
    4: 4,
    5: 5,
    6: 10
}

# جوائز الجاكبوت
JACKPOT_MULTIPLIERS = [20, 30, 50, 100]

# أشكال النرد الكبيرة
DICE_LARGE = {
    1: "┌─────────┐\n│         │\n│    ●    │\n│         │\n└─────────┘",
    2: "┌─────────┐\n│  ●      │\n│         │\n│      ●  │\n└─────────┘",
    3: "┌─────────┐\n│  ●      │\n│    ●    │\n│      ●  │\n└─────────┘",
    4: "┌─────────┐\n│  ●   ●  │\n│         │\n│  ●   ●  │\n└─────────┘",
    5: "┌─────────┐\n│  ●   ●  │\n│    ●    │\n│  ●   ●  │\n└─────────┘",
    6: "┌─────────┐\n│  ●   ●  │\n│  ●   ●  │\n│  ●   ●  │\n└─────────┘"
}

# خيارات الرهان
BET_OPTIONS = [1, 2, 5, 10, 25, 30, 50, 100]

# تخزين الرهان المختار لكل مستخدم
user_selected_bet = {}

# ================== دوال مساعدة سريعة ==================
def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(URL + "sendMessage", json=data, timeout=5)
    except:
        pass

def edit_message(chat_id, message_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        requests.post(URL + "editMessageText", json=data, timeout=5)
    except:
        pass

def answer_callback(callback_id):
    try:
        requests.post(URL + "answerCallbackQuery", json={"callback_query_id": callback_id}, timeout=3)
    except:
        pass

def answer_callback_alert(callback_id, text):
    """إرسال تنبيه منبثق للمستخدم"""
    try:
        requests.post(URL + "answerCallbackQuery", json={"callback_query_id": callback_id, "text": text, "show_alert": True}, timeout=3)
    except:
        pass

# ================== أزرار اللعبة ==================
def get_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎲 ابدأ اللعب", "callback_data": "play"}],
            [{"text": "💰 رصيدي", "callback_data": "balance"}],
            [{"text": "❓ المساعدة", "callback_data": "help"}]
        ]
    }

def get_bet_keyboard():
    buttons = []
    row = []
    for i, bet in enumerate(BET_OPTIONS):
        row.append({"text": f"💰 {bet}", "callback_data": f"select_bet_{bet}"})
        if (i + 1) % 4 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([{"text": "🏠 القائمة الرئيسية", "callback_data": "menu"}])
    return {"inline_keyboard": buttons}

def get_roll_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎲 رمي النرد 🎲", "callback_data": "roll_now"}],
            [{"text": "💰 تغيير الرهان", "callback_data": "change_bet"}, {"text": "🏠 الرئيسية", "callback_data": "menu"}]
        ]
    }

def get_play_again_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎲 لعب مرة أخرى", "callback_data": "play"}],
            [{"text": "💰 رصيدي", "callback_data": "balance"}, {"text": "🏠 الرئيسية", "callback_data": "menu"}]
        ]
    }

def get_main_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🏠 القائمة الرئيسية", "callback_data": "menu"}]
        ]
    }

# ================== دوال اللعبة ==================
def start_game(chat_id, user_id, username, first_name):
    create_user(user_id, username, first_name)
    global user_selected_bet
    user_selected_bet[user_id] = None
    
    user = get_user(user_id)
    coins = user[3] if user else 0
    
    msg = f"""🎲 *مرحباً بك في لعبة النرد!* 🎲

💰 رصيدك الحالي: {coins} Coin

✨ *اختر رهانك وابدأ اللعب* ✨"""
    send_message(chat_id, msg, reply_markup=get_menu_keyboard())

def show_balance(chat_id, message_id, user_id):
    user = get_user(user_id)
    if user:
        coins = user[3]
        rolls = user[4]
        wins = user[5]
        
        msg = f"""💰 *رصيدك:* {coins} Coin

📊 *إحصائياتك:*
├─ 🎲 عدد اللفات: {rolls}
├─ 🏆 عدد مرات الفوز: {wins}
└─ 📈 نسبة الفوز: {round(wins/rolls*100, 1) if rolls > 0 else 0}%"""
        
        edit_message(chat_id, message_id, msg, reply_markup=get_menu_keyboard())
    else:
        edit_message(chat_id, message_id, "❌ حدث خطأ", reply_markup=get_menu_keyboard())

def show_help(chat_id, message_id):
    msg = """❓ *كيفية اللعب* ❓

🎲 *طريقة اللعب:*
1. اضغط "ابدأ اللعب"
2. اختر مبلغ الرهان
3. اضغط "رمي النرد"
4. شاهد النتيجة!

💰 *الربح:* يعتمد على الرقم الذي يظهر
🎯 *حظاً موفقاً!* 🎯"""
    edit_message(chat_id, message_id, msg, reply_markup=get_menu_keyboard())

def show_bet_selection(chat_id, message_id, user_id):
    user = get_user(user_id)
    if not user:
        edit_message(chat_id, message_id, "❌ حدث خطأ", reply_markup=get_menu_keyboard())
        return
    
    msg = f"""🎲 *اختر رهانك* 🎲

💰 رصيدك الحالي: {user[3]} Coin

✨ *اختر المبلغ الذي تريد المراهنة به:* ✨"""
    edit_message(chat_id, message_id, msg, reply_markup=get_bet_keyboard())

def select_bet(chat_id, message_id, user_id, bet_amount):
    user = get_user(user_id)
    if not user:
        return
    
    if user[3] < bet_amount:
        msg = f"❌ *رصيدك غير كافٍ*\n💰 رصيدك: {user[3]} Coin\n🎯 الرهان المطلوب: {bet_amount} Coin"
        edit_message(chat_id, message_id, msg, reply_markup=get_bet_keyboard())
        return
    
    global user_selected_bet
    user_selected_bet[user_id] = bet_amount
    
    msg = f"""✅ *تم اختيار الرهان:* {bet_amount} Coin

🎲 *الآن اضغط على زر "رمي النرد" لبدء اللعب*

💰 رصيدك الحالي: {user[3]} Coin"""
    edit_message(chat_id, message_id, msg, reply_markup=get_roll_keyboard())

def perform_roll_animation(chat_id, message_id):
    """حركة النرد السريعة"""
    for i in range(4):
        random_dice = random.randint(1, 6)
        frame = f"🎲 *جاري الرمي...* 🎲\n\n```\n{DICE_LARGE[random_dice]}\n```"
        edit_message(chat_id, message_id, frame)
        time.sleep(0.15)

def perform_roll(chat_id, message_id, user_id):
    global user_selected_bet
    
    bet_amount = user_selected_bet.get(user_id)
    if not bet_amount:
        msg = "❌ *لم تختر رهاناً بعد*\n\nيرجى اختيار مبلغ الرهان أولاً"
        edit_message(chat_id, message_id, msg, reply_markup=get_bet_keyboard())
        return
    
    user = get_user(user_id)
    if not user:
        return
    
    coins = user[3]
    if coins < bet_amount:
        msg = f"❌ *رصيدك غير كافٍ*\n💰 رصيدك: {coins} Coin"
        edit_message(chat_id, message_id, msg, reply_markup=get_menu_keyboard())
        user_selected_bet[user_id] = None
        return
    
    # خصم الرهان
    new_coins = coins - bet_amount
    update_user_coins(user_id, new_coins)
    update_total_bets(user_id, bet_amount)
    update_pool_bets(bet_amount)
    
    # حركة النرد
    perform_roll_animation(chat_id, message_id)
    
    # النتيجة النهائية
    dice_result = random.randint(1, 6)
    dice_face_large = DICE_LARGE[dice_result]
    multiplier = WIN_MULTIPLIERS[dice_result]
    win_amount = bet_amount * multiplier
    
    # نظام Pool
    pool_total, pool_payout, pool_percent = get_pool_data()
    available_payout = int(pool_total * pool_percent / 100)
    remaining_payout = available_payout - pool_payout
    
    # الجاكبوت
    jackpot_chance = get_jackpot_chance() / 100
    is_jackpot = random.random() < jackpot_chance
    
    if is_jackpot and remaining_payout > 0:
        jackpot_multiplier = random.choice(JACKPOT_MULTIPLIERS)
        win_amount = min(bet_amount * jackpot_multiplier, remaining_payout)
        
        if win_amount > 0:
            remaining_payout -= win_amount
            update_pool_payout(pool_payout + win_amount)
            new_coins += win_amount
            update_user_coins(user_id, new_coins)
            increment_wins_count(user_id, win_amount)
            add_jackpot_log(user_id, bet_amount, win_amount, jackpot_multiplier)
            
            result_text = f"""🎰 *جاكبوت!* 🎰

```\n{dice_face_large}\n```

✨ *فوز كبير!* ✨
💰 المكسب: +{win_amount} Coin
💎 الرصيد الجديد: {new_coins} Coin"""
            
            # إرسال تنبيه منبثق للمستخدم
            answer_callback_alert(None, f"🎰 مبروك! ربحت جاكبوت بقيمة {win_amount} Coin! 🎰")
        else:
            result_text = f"""🎲 *النتيجة*

```\n{dice_face_large}\n```

💸 خسارة: -{bet_amount} Coin
💰 رصيدك: {new_coins} Coin"""
    else:
        if win_amount <= remaining_payout and remaining_payout > 0:
            remaining_payout -= win_amount
            update_pool_payout(pool_payout + win_amount)
            new_coins += win_amount
            update_user_coins(user_id, new_coins)
            increment_wins_count(user_id, win_amount)
            
            result_text = f"""🎉 *فوز!* 🎉

```\n{dice_face_large}\n```

💰 المكسب: +{win_amount} Coin
💎 الرصيد الجديد: {new_coins} Coin"""
        else:
            result_text = f"""🎲 *النتيجة*

```\n{dice_face_large}\n```

💸 خسارة: -{bet_amount} Coin
💰 رصيدك: {new_coins} Coin"""
    
    # تسجيل اللفة
    increment_rolls_count(user_id)
    add_roll_log(user_id, user[4] + 1, bet_amount, dice_result, win_amount <= remaining_payout, win_amount if win_amount <= remaining_payout else 0, coins, new_coins)
    
    final_msg = f"{result_text}\n\n✨ *هل تريد اللعب مرة أخرى؟* ✨"
    edit_message(chat_id, message_id, final_msg, reply_markup=get_play_again_keyboard())

def change_bet(chat_id, message_id, user_id):
    global user_selected_bet
    user_selected_bet[user_id] = None
    show_bet_selection(chat_id, message_id, user_id)

# ================== أوامر المشرف ==================
def handle_admin_commands(chat_id, text):
    # تغيير نسبة Pool
    if text.startswith("/set_pool"):
        try:
            percent = float(text.split()[1])
            percent = max(5, min(80, percent))
            set_pool_percentage(percent)
            send_message(chat_id, f"✅ تم تغيير نسبة أرباح Pool إلى {percent}%")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /set_pool 30")
            return True
    
    # تغيير نسبة الجاكبوت
    if text.startswith("/set_jackpot"):
        try:
            percent = float(text.split()[1])
            percent = max(1, min(20, percent))
            set_setting("jackpot_chance", str(percent))
            send_message(chat_id, f"✅ تم تغيير نسبة الجاكبوت إلى {percent}%")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /set_jackpot 5")
            return True
    
    # إضافة رصيد لمستخدم
    if text.startswith("/add"):
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
                send_message(chat_id, f"❌ المستخدم {target_id} غير موجود\n💡 أرسل /start أولاً")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /add [ID] [المبلغ]")
            return True
    
    # تعيين رصيد لمستخدم
    if text.startswith("/set"):
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
            send_message(chat_id, "❌ استخدم: /set [ID] [الرصيد]")
            return True
    
    # عرض إحصائيات Pool
    if text == "/pool_stats":
        total_bets, total_payout, pool_percent = get_pool_data()
        remaining = int(total_bets * pool_percent / 100) - total_payout
        msg = f"""📊 *إحصائيات Pool*

💰 إجمالي الرهانات: {total_bets} Coin
🎯 نسبة الأرباح: {pool_percent}%
💎 الأرباح الموزعة: {total_payout} Coin
✨ الأرباح المتبقية: {max(0, remaining)} Coin

🎰 نسبة الجاكبوت: {get_jackpot_chance()}%"""
        send_message(chat_id, msg)
        return True
    
    # عرض قائمة المستخدمين
    if text == "/users":
        users = get_all_users()
        if users:
            msg = "👥 *قائمة المستخدمين*\n\n"
            for u in users[:20]:
                name = u[1] or u[2] or f"مستخدم {u[0]}"
                if len(name) > 15:
                    name = name[:12] + "..."
                msg += f"🆔 `{u[0]}` | {name} | 💰 {u[3]} Coin\n"
            send_message(chat_id, msg)
        else:
            send_message(chat_id, "📭 لا يوجد مستخدمون بعد")
        return True
    
    # إعادة تعيين Pool
    if text == "/reset_pool":
        reset_pool()
        send_message(chat_id, "✅ تم إعادة تعيين Pool")
        return True
    
    # المساعدة
    if text == "/admin":
        msg = """🔐 *أوامر المشرف*

🎯 *الإعدادات:*
/set_pool 30 - نسبة أرباح Pool
/set_jackpot 5 - نسبة الجاكبوت

💰 *الأرصدة:*
/add [ID] [مبلغ] - إضافة رصيد
/set [ID] [رصيد] - تعيين رصيد

📊 *الإحصائيات:*
/pool_stats - حالة Pool
/users - قائمة المستخدمين
/reset_pool - إعادة تعيين Pool"""
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
        change_bet(chat_id, message_id, user_id)
    elif data.startswith("select_bet_"):
        bet_amount = int(data.split("_")[2])
        select_bet(chat_id, message_id, user_id, bet_amount)
    elif data == "roll_now":
        perform_roll(chat_id, message_id, user_id)
    elif data == "balance":
        show_balance(chat_id, message_id, user_id)
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

# ================== إعدادات المضاعفات ==================
def init_multipliers():
    for i in range(1, 7):
        default = 2 if i <= 2 else (3 if i == 3 else (4 if i == 4 else (5 if i == 5 else 10)))
        set_setting(f"multiplier_{i}", str(default))

init_multipliers()

# ================== خادم ويب ==================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', 10000), DummyHandler)
    server.serve_forever()

Thread(target=run_dummy_server, daemon=True).start()

# ================== تشغيل البوت ==================
print("=" * 50)
print("🎲 بوت النرد السريع يعمل... 🎲")
print("=" * 50)
print("✅ رصيد ابتدائي: 0 Coin")
print("✅ الرهان يبقى محفوظاً")
print("✅ رسائل منبثقة للجاكبوت")
print("=" * 50)

last_update_id = 0
while True:
    try:
        response = requests.get(URL + "getUpdates", params={"offset": last_update_id + 1, "timeout": 25}, timeout=30)
        updates = response.json()
        if updates.get("ok") and updates.get("result"):
            handle_updates(updates)
            last_update_id = updates["result"][-1]["update_id"]
    except:
        pass
    time.sleep(0.5)
