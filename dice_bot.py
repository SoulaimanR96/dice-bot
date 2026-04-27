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
ADMIN_ID = 123456789  # ⚠️ ضع معرفك الحقيقي هنا

def is_admin(user_id):
    return user_id == ADMIN_ID

# ================== أشكال النرد التفاعلية ==================
DICE_FACES = {
    1: "⚀",
    2: "⚁", 
    3: "⚂",
    4: "⚃",
    5: "⚄",
    6: "⚅"
}

DICE_ANIMATION = ["🎲", "🎲", "🎲", "🎲", "🎲", "🎲"]

# رسائل الفوز والخسارة الجذابة
WIN_MESSAGES = [
    "🎉 *ممتاز!* 🎉",
    "🏆 *عمل رائع!* 🏆", 
    "✨ *حظ سعيد!* ✨",
    "🎊 *أحسنت!* 🎊",
    "💎 *جاكبوت!* 💎"
]

LOSE_MESSAGES = [
    "😅 *قريب جداً!* 😅",
    "🍀 *حظ أوفر المرة القادمة* 🍀",
    "💪 *استمر في المحاولة!* 💪",
    "🎯 *كاد أن يفوز!* 🎯",
    "🌟 *الفرصة القادمة لك* 🌟"
]

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

def send_animation(chat_id, animation_url):
    """إرسال رسالة متحركة (اختياري)"""
    try:
        data = {"chat_id": chat_id, "animation": animation_url}
        requests.post(URL + "sendAnimation", json=data, timeout=10)
    except:
        pass

# ================== لوحة الأزرار الرئيسية ==================
def get_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎲 ابدأ اللعب 🎲", "callback_data": "play"}],
            [{"text": "💰 رصيدي", "callback_data": "balance"}, {"text": "📊 الترتيب", "callback_data": "leaderboard"}],
            [{"text": "❓ المساعدة", "callback_data": "help"}]
        ]
    }

def get_play_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎲 رمي النرد مرة أخرى 🎲", "callback_data": "play"}],
            [{"text": "💰 رصيدي", "callback_data": "balance"}, {"text": "🏠 القائمة الرئيسية", "callback_data": "menu"}]
        ]
    }

def get_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🎲 ابدأ اللعب", "callback_data": "play"}],
            [{"text": "💰 رصيدي", "callback_data": "balance"}, {"text": "📊 الترتيب", "callback_data": "leaderboard"}]
        ]
    }

# ================== دوال اللعبة ==================
def start_game(chat_id, user_id, username, first_name):
    create_user(user_id, username, first_name)
    msg = """🎲 *مرحباً بك في لعبة الحظ والنرد!* 🎲

⚡ *قوانين اللعبة:*
• كل لفة تكلف 1 Coin
• إذا فزت تربح 10 Coins
• كلما زاد رصيدك زادت فرصك للفوز

🎯 *استعد للفوز! اضغط زر ابدأ اللعب* 🎯"""
    send_message(chat_id, msg, reply_markup=get_main_keyboard())

def show_balance(chat_id, message_id, user_id):
    user = get_user(user_id)
    if user:
        coins = user[3]
        rolls = user[4]
        wins = user[5]
        
        # تحديد مستوى المستخدم حسب الرصيد
        if coins >= 1000:
            level = "👑 *أسطورة* 👑"
            icon = "💎"
        elif coins >= 500:
            level = "⭐ *محترف* ⭐"
            icon = "🏆"
        elif coins >= 100:
            level = "🌟 *لاعب نشيط* 🌟"
            icon = "🎯"
        else:
            level = "🌱 *مبتدئ* 🌱"
            icon = "🌱"
        
        msg = f"""💰 *رصيدك الحالي:* 
└─ {icon} {coins} Coin

📊 *إحصائياتك:*
└─ 🎲 عدد اللفات: {rolls}
└─ 🏆 عدد مرات الفوز: {wins}
└─ 📈 نسبة الفوز: {round(wins/rolls*100, 1) if rolls > 0 else 0}%

👤 *مستواك:* {level}"""
        
        edit_message(chat_id, message_id, msg, reply_markup=get_menu_keyboard())
    else:
        edit_message(chat_id, message_id, "❌ حدث خطأ، أعد إرسال /start", reply_markup=get_menu_keyboard())

def show_leaderboard(chat_id, message_id):
    top_users = get_top_users(10)
    if top_users:
        msg = "🏆 *قائمة الأغنياء* 🏆\n\n"
        medals = ["🥇", "🥈", "🥉", "📌", "📌", "📌", "📌", "📌", "📌", "📌"]
        
        for i, user in enumerate(top_users[:10], 1):
            name = user[2] or user[1] or f"مستخدم {user[0]}"
            if len(name) > 20:
                name = name[:17] + "..."
            coins = user[3]
            medal = medals[i-1] if i <= len(medals) else "📍"
            msg += f"{medal} *{i}.* {name}\n   └─ 💰 {coins} Coin\n\n"
        
        edit_message(chat_id, message_id, msg, reply_markup=get_menu_keyboard())
    else:
        edit_message(chat_id, message_id, "📭 لا يوجد مستخدمون بعد. كن أول من يلعب!", reply_markup=get_menu_keyboard())

def show_help(chat_id, message_id):
    msg = """❓ *كيفية اللعب* ❓

🎲 *الهدف:*
احصل على النرد واربح Coins!

⚙️ *طريقة اللعب:*
1. اضغط على زر "ابدأ اللعب"
2. سيتم خصم 1 Coin من رصيدك
3. يظهر النرد بشكل عشوائي
4. إذا حصلت على رقم عشوائي فائز تربح 10 Coins

💡 *نصائح:*
• كلما زادت محاولاتك زادت خبرتك
• تابع رصيدك من زر "رصيدي"
• شاهد منافسيك في "الترتيب"

🎯 *حظاً موفقاً!* 🎯"""
    edit_message(chat_id, message_id, msg, reply_markup=get_menu_keyboard())

def perform_roll(chat_id, message_id, user_id):
    user = get_user(user_id)
    if not user:
        edit_message(chat_id, message_id, "❌ حدث خطأ، أعد إرسال /start", reply_markup=get_menu_keyboard())
        return
    
    coins = user[3]
    cost = int(get_setting("cost_per_roll"))
    
    if coins < cost:
        msg = f"""❌ *رصيدك غير كافٍ* ❌

💰 رصيدك الحالي: {coins} Coin
💸 تحتاج: {cost} Coin

🎯 العب أكثر لتربح المزيد من Coins!
💡 استخدم /start لإعادة المحاولة"""
        edit_message(chat_id, message_id, msg, reply_markup=get_menu_keyboard())
        return
    
    # إظهار تأثير الرمي (متسلسل)
    # مرحمة: إظهار علامة الانتظار
    wait_msg = "🎲 *جاري رمي النرد* 🎲\n" + "".join(["🔴", "🟡", "🟢", "🔵", "🟣"][:3])
    edit_message(chat_id, message_id, wait_msg)
    time.sleep(0.5)
    
    # خصم التكلفة
    new_coins = coins - cost
    
    # تحديد الفوز (يمكن زيادة نسبة الفوز لجعل اللعبة ممتعة أكثر)
    win_prob = float(get_setting("win_probability"))
    # زيادة نسبة الفوز الأساسية قليلاً لجذب المستخدمين (اختياري)
    win_prob = min(win_prob + 0.05, 0.5)  # حد أقصى 50%
    
    is_win = random.random() < win_prob
    
    # تأثير حركة النرد المتسلسلة
    animation_frames = []
    for i in range(3):
        frame = "🎲 *رمي النرد* 🎲\n\n"
        for _ in range(3):
            frame += random.choice(list(DICE_FACES.values())) + " "
        frame += "\n\n" + "⬇️" * (i + 1)
        edit_message(chat_id, message_id, frame)
        time.sleep(0.3)
    
    # رمي النرد الحقيقي
    dice_result = random.randint(1, 6)
    dice_face = DICE_FACES[dice_result]
    
    if is_win:
        reward = int(get_setting("reward_coins"))
        new_coins += reward
        increment_wins_count(user_id)
        win_msg = random.choice(WIN_MESSAGES)
        
        # رسالة خاصة للأرقام الكبيرة
        special_msg = ""
        if dice_result == 6:
            special_msg = "\n🌟 *رقم الحظ!* 🌟"
        elif dice_result == 1:
            special_msg = "\n🍀 *البداية الجيدة!* 🍀"
        
        result_text = f"""{win_msg} {special_msg}

┌─ 🎲 *النتيجة:* {dice_face} {dice_result}
├─ 💰 *المكسب:* +{reward} Coin
└─ 💎 *الرصيد الجديد:* {new_coins} Coin"""
    else:
        lose_msg = random.choice(LOSE_MESSAGES)
        
        # رسائل تشجيعية للخسارة
        encourage_msgs = ["🌱 *استمر في المحاولة!*", "💪 *المرات القادمة أفضل*", "🎯 *قريب جداً!*"]
        encourage = random.choice(encourage_msgs)
        
        result_text = f"""{lose_msg} {encourage}

┌─ 🎲 *النتيجة:* {dice_face} {dice_result}
├─ 💸 *الخصم:* -{cost} Coin
└─ 💰 *الرصيد الجديد:* {new_coins} Coin"""
    
    # تحديث البيانات
    update_user_coins(user_id, new_coins)
    increment_rolls_count(user_id)
    add_roll_log(user_id, user[4] + 1, dice_result, is_win, coins, new_coins)
    
    # عرض النتيجة النهائية
    final_msg = f"{result_text}\n\n✨ *هل تريد المحاولة مرة أخرى؟* ✨"
    edit_message(chat_id, message_id, final_msg, reply_markup=get_play_keyboard())

# ================== أوامر المشرف السرية ==================
def handle_admin_commands(chat_id, text):
    if text.startswith("/win"):
        try:
            percent = float(text.split()[1])
            percent = max(1, min(99, percent))  # بين 1% و 99%
            set_setting("win_probability", str(percent / 100))
            send_message(chat_id, f"✅ تم تغيير نسبة الفوز إلى {percent}%\n🎯 حظاً موفقاً للاعبين!")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /win 30 (نسبة بين 1-99)")
            return True
    
    elif text.startswith("/reward"):
        try:
            reward = int(text.split()[1])
            reward = max(1, min(100, reward))  # بين 1 و 100
            set_setting("reward_coins", str(reward))
            send_message(chat_id, f"✅ تم تغيير مكافأة الفوز إلى {reward} Coin\n💰 جوائز أكبر = متعة أكبر!")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /reward 10")
            return True
    
    elif text.startswith("/cost"):
        try:
            cost = int(text.split()[1])
            cost = max(1, min(10, cost))  # بين 1 و 10
            set_setting("cost_per_roll", str(cost))
            send_message(chat_id, f"✅ تم تغيير تكلفة اللفة إلى {cost} Coin")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /cost 1")
            return True
    
    elif text.startswith("/add"):
        try:
            parts = text.split()
            target_id = int(parts[1])
            amount = int(parts[2])
            user = get_user(target_id)
            if user:
                new_coins = user[3] + amount
                update_user_coins(target_id, new_coins)
                send_message(chat_id, f"✅ تم إضافة {amount} Coin للمستخدم `{target_id}`\n💰 رصيده الآن: {new_coins} Coin")
            else:
                send_message(chat_id, f"❌ المستخدم {target_id} غير موجود")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /add [معرف_المستخدم] [الكمية]")
            return True
    
    elif text.startswith("/set"):
        try:
            parts = text.split()
            target_id = int(parts[1])
            amount = int(parts[2])
            user = get_user(target_id)
            if user:
                update_user_coins(target_id, amount)
                send_message(chat_id, f"✅ تم تعيين رصيد المستخدم `{target_id}` إلى {amount} Coin")
            else:
                send_message(chat_id, f"❌ المستخدم {target_id} غير موجود")
            return True
        except:
            send_message(chat_id, "❌ استخدم: /set [معرف_المستخدم] [الرصيد]")
            return True
    
    elif text == "/settings":
        win = float(get_setting("win_probability")) * 100
        reward = get_setting("reward_coins")
        cost = get_setting("cost_per_roll")
        msg = f"""📊 *الإعدادات الحالية* 📊

🎯 نسبة الفوز: {win:.1f}%
💰 مكافأة الفوز: {reward} Coin
💸 تكلفة اللفة: {cost} Coin

📈 للتعديل استخدم:
/win [نسبة]
/reward [قيمة]
/cost [قيمة]"""
        send_message(chat_id, msg)
        return True
    
    elif text == "/stats":
        total_users = get_total_users()
        total_rolls = get_total_rolls()
        total_wins = sum([u[5] for u in get_all_users()])
        msg = f"""📈 *إحصائيات البوت* 📈

👥 عدد المستخدمين: {total_users}
🎲 إجمالي اللفات: {total_rolls}
🏆 إجمالي الفوز: {total_wins}
📊 نسبة الفوز العامة: {round(total_wins/total_rolls*100, 1) if total_rolls > 0 else 0}%

🎮 دعوة أصدقائك للمشاركة!"""
        send_message(chat_id, msg)
        return True
    
    elif text == "/users":
        users = get_all_users()
        if users:
            msg = "👥 *قائمة المستخدمين* 👥\n\n"
            for u in users[:20]:
                name = u[1] or u[2] or f"مستخدم {u[0]}"
                if len(name) > 15:
                    name = name[:12] + "..."
                msg += f"🆔 `{u[0]}` | {name} | 💰 {u[3]} Coin\n"
            send_message(chat_id, msg)
        else:
            send_message(chat_id, "📭 لا يوجد مستخدمون بعد")
        return True
    
    elif text == "/admin":
        msg = """🔐 *لوحة التحكم السرية* 🔐

🎯 *التحكم في اللعبة:*
/win 30 - تغيير نسبة الفوز
/reward 10 - تغيير المكافأة
/cost 1 - تغيير التكلفة

💰 *التحكم في الأرصدة:*
/add 123456789 100 - إضافة رصيد
/set 123456789 500 - تعيين رصيد

📊 *معلومات:*
/settings - الإعدادات الحالية
/stats - الإحصائيات العامة
/users - قائمة المستخدمين

✨ *استمتع بإدارة البوت!* ✨"""
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
            else:
                if is_admin(user_id):
                    handle_admin_commands(chat_id, text)
        
        elif "callback_query" in update:
            handle_callback(update["callback_query"])

# ================== خادم ويب وهمي ==================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"🎲 Bot is running! 🎲")
    def log_message(self, format, *args):
        pass

def run_dummy_server():
    server = HTTPServer(('0.0.0.0', 10000), DummyHandler)
    server.serve_forever()

Thread(target=run_dummy_server, daemon=True).start()

# ================== تشغيل البوت ==================
print("=" * 50)
print("🎲 بوت النرد الاحترافي يعمل... 🎲")
print("=" * 50)
print("✅ أوامر المشرف: /admin")
print("✅ اللعبة تفاعلية مع أشكال النرد")
print("✅ انتظر المستخدمين...")
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
