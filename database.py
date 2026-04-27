import sqlite3
import os
from datetime import datetime

DB_NAME = "game.db"

def init_db():
    """تهيئة قاعدة البيانات"""
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول سجل الرمي
    c.execute('''CREATE TABLE IF NOT EXISTS rolls_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        roll_number INTEGER,
        result INTEGER,
        is_win BOOLEAN,
        coins_before INTEGER,
        coins_after INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول الإعدادات
    c.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    # الإعدادات الافتراضية
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('win_probability', '0.1666')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('reward_coins', '10')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('cost_per_roll', '1')")
    
    conn.commit()
    conn.close()

def get_setting(key):
    """الحصول على إعداد"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_setting(key, value):
    """تحديث إعداد"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_user(user_id):
    """الحصول على مستخدم"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(user_id, username, first_name):
    """إنشاء مستخدم جديد"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, first_name, coins) VALUES (?, ?, ?, ?)",
              (user_id, username, first_name, 100))
    conn.commit()
    conn.close()

def update_user_coins(user_id, new_coins):
    """تحديث رصيد المستخدم"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET coins = ? WHERE user_id = ?", (new_coins, user_id))
    conn.commit()
    conn.close()

def increment_rolls_count(user_id):
    """زيادة عدد اللفات"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET rolls_count = rolls_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def increment_wins_count(user_id):
    """زيادة عدد مرات الفوز"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET wins_count = wins_count + 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def add_roll_log(user_id, roll_number, result, is_win, coins_before, coins_after):
    """إضافة سجل لفة"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO rolls_log (user_id, roll_number, result, is_win, coins_before, coins_after)
                 VALUES (?, ?, ?, ?, ?, ?)''',
              (user_id, roll_number, result, is_win, coins_before, coins_after))
    conn.commit()
    conn.close()

def get_top_users(limit=10):
    """الحصول على الترتيب"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, coins, wins_count FROM users ORDER BY coins DESC LIMIT ?", (limit,))
    users = c.fetchall()
    conn.close()
    return users

def get_all_users():
    """الحصول على جميع المستخدمين"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id, first_name, username, coins FROM users ORDER BY coins DESC")
    users = c.fetchall()
    conn.close()
    return users

def get_total_users():
    """عدد المستخدمين"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return total

def get_total_rolls():
    """عدد اللفات الكلي"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    total = c.execute("SELECT SUM(rolls_count) FROM users").fetchone()[0] or 0
    conn.close()
    return total

init_db()
