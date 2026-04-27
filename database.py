import sqlite3
import os
from datetime import datetime

DB_NAME = "game.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # جدول المستخدمين
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        coins INTEGER DEFAULT 100,
        rolls_count INTEGER DEFAULT 0,
        wins_count INTEGER DEFAULT 0,
        total_bets INTEGER DEFAULT 0,
        total_wins INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول سجل الرمي
    c.execute('''CREATE TABLE IF NOT EXISTS rolls_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        roll_number INTEGER,
        bet_amount INTEGER,
        result INTEGER,
        is_win BOOLEAN,
        win_amount INTEGER,
        coins_before INTEGER,
        coins_after INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول إدارة الـ Pool
    c.execute('''CREATE TABLE IF NOT EXISTS pool_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        total_bets INTEGER DEFAULT 0,
        total_payout INTEGER DEFAULT 0,
        pool_percentage REAL DEFAULT 30,
        last_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول سجل الجاكبوت
    c.execute('''CREATE TABLE IF NOT EXISTS jackpot_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        bet_amount INTEGER,
        win_amount INTEGER,
        multiplier INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول الإعدادات
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    # الإعدادات الافتراضية
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('pool_percentage', '30')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('jackpot_chance', '1')")  # 1%
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('jackpot_percentage', '2')")  # 2% من الـ Pool
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('cost_per_roll', '1')")
    
    # إدخال أولي للـ Pool
    c.execute("INSERT OR IGNORE INTO pool_data (id, total_bets, total_payout) VALUES (1, 0, 0)")
    
    conn.commit()
    conn.close()

# ================== دوال المستخدمين ==================
def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

# تعديل دالة create_user - الرصيد الافتراضي 0
def create_user(user_id, username, first_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, coins) VALUES (?, ?, ?, ?)",
              (user_id, username, first_name, 0))  # <- رصيد ابتدائي 0
    conn.commit()
    conn.close()

def update_user_coins(user_id, new_coins):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET coins = ? WHERE user_id = ?", (new_coins, user_id))
    conn.commit()
    conn.close()

def increment_rolls_count(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET rolls_count = rolls_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def increment_wins_count(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET wins_count = wins_count + 1, total_wins = total_wins + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def update_total_bets(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET total_bets = total_bets + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def get_top_users(limit=10):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, coins, wins_count FROM users ORDER BY coins DESC LIMIT ?", (limit,))
    users = c.fetchall()
    conn.close()
    return users

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id, first_name, username, coins FROM users ORDER BY coins DESC")
    users = c.fetchall()
    conn.close()
    return users

def get_total_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return total

def get_total_rolls():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    total = c.execute("SELECT SUM(rolls_count) FROM users").fetchone()[0] or 0
    conn.close()
    return total

def get_total_wins():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    total = c.execute("SELECT SUM(wins_count) FROM users").fetchone()[0] or 0
    conn.close()
    return total

# ================== دوال الـ Pool ==================
def get_pool_data():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT total_bets, total_payout, pool_percentage FROM pool_data WHERE id = 1")
    data = c.fetchone()
    conn.close()
    return data if data else (0, 0, 30)

def update_pool_bets(amount):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE pool_data SET total_bets = total_bets + ? WHERE id = 1", (amount,))
    conn.commit()
    conn.close()

def update_pool_payout(amount):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE pool_data SET total_payout = total_payout + ? WHERE id = 1", (amount,))
    conn.commit()
    conn.close()

def reset_pool():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE pool_data SET total_bets = 0, total_payout = 0, last_reset = CURRENT_TIMESTAMP WHERE id = 1")
    conn.commit()
    conn.close()

def set_pool_percentage(percentage):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE pool_data SET pool_percentage = ? WHERE id = 1", (percentage,))
    c.execute("UPDATE settings SET value = ? WHERE key = 'pool_percentage'", (str(percentage),))
    conn.commit()
    conn.close()

def get_pool_percentage():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    result = c.execute("SELECT value FROM settings WHERE key = 'pool_percentage'").fetchone()
    conn.close()
    return float(result[0]) if result else 30

# ================== دوال الجاكبوت ==================
def add_jackpot_log(user_id, bet_amount, win_amount, multiplier):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO jackpot_log (user_id, bet_amount, win_amount, multiplier) VALUES (?, ?, ?, ?)",
              (user_id, bet_amount, win_amount, multiplier))
    conn.commit()
    conn.close()

def get_jackpot_chance():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    result = c.execute("SELECT value FROM settings WHERE key = 'jackpot_chance'").fetchone()
    conn.close()
    return float(result[0]) if result else 1

def get_jackpot_percentage():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    result = c.execute("SELECT value FROM settings WHERE key = 'jackpot_percentage'").fetchone()
    conn.close()
    return float(result[0]) if result else 2

# ================== دوال الإعدادات العامة ==================
def get_setting(key):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def add_roll_log(user_id, roll_number, bet_amount, result, is_win, win_amount, coins_before, coins_after):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO rolls_log (user_id, roll_number, bet_amount, result, is_win, win_amount, coins_before, coins_after)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
              (user_id, roll_number, bet_amount, result, is_win, win_amount, coins_before, coins_after))
    conn.commit()
    conn.close()
def get_jackpot_chance():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    result = c.execute("SELECT value FROM settings WHERE key = 'jackpot_chance'").fetchone()
    conn.close()
    return float(result[0]) if result else 5

def get_jackpot_percentage():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    result = c.execute("SELECT value FROM settings WHERE key = 'jackpot_percentage'").fetchone()
    conn.close()
    return float(result[0]) if result else 2
init_db()
