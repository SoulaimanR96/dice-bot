import os
import psycopg2
from psycopg2.extras import RealDictCursor

# استبدل YOUR_PASSWORD بكلمة السر الحقيقية التي أدخلتها في Supabase
DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@db.sukawtxjruvooisebdyb.supabase.co:5432/postgres"

def get_connection():
    """إنشاء اتصال بقاعدة البيانات"""
    return psycopg2.connect(DATABASE_URL)

def init_db():
    """تهيئة قاعدة البيانات - يتم إنشاء الجداول يدوياً عبر SQL Editor"""
    pass  # الجداول تم إنشاؤها بالفعل في Supabase

def get_setting(key):
    """الحصول على إعداد من قاعدة البيانات"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = %s", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_setting(key, value):
    """تحديث إعداد في قاعدة البيانات"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO settings (key, value) 
        VALUES (%s, %s) 
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
    """, (key, value))
    conn.commit()
    conn.close()

def get_user(user_id):
    """الحصول على معلومات مستخدم"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def create_user(user_id, username, first_name):
    """إنشاء مستخدم جديد"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO users (user_id, username, first_name, coins) 
        VALUES (%s, %s, %s, %s) 
        ON CONFLICT (user_id) DO NOTHING
    """, (user_id, username, first_name, 0))
    conn.commit()
    conn.close()

def update_user_coins(user_id, new_coins):
    """تحديث رصيد المستخدم"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET coins = %s WHERE user_id = %s", (new_coins, user_id))
    conn.commit()
    conn.close()

def increment_rolls_count(user_id):
    """زيادة عدد اللفات للمستخدم"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET rolls_count = rolls_count + 1 WHERE user_id = %s", (user_id,))
    conn.commit()
    conn.close()

def increment_wins_count(user_id):
    """زيادة عدد مرات الفوز للمستخدم"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET wins_count = wins_count + 1 WHERE user_id = %s", (user_id,))
    conn.commit()
    conn.close()

def add_roll_log(user_id, roll_number, result, is_win, coins_before, coins_after):
    """إضافة سجل لفة جديدة"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO rolls_log (user_id, roll_number, result, is_win, coins_before, coins_after)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (user_id, roll_number, result, is_win, coins_before, coins_after))
    conn.commit()
    conn.close()

def get_top_users(limit=10):
    """الحصول على قائمة المستخدمين حسب الرصيد"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT user_id, username, first_name, coins, wins_count 
        FROM users 
        ORDER BY coins DESC 
        LIMIT %s
    """, (limit,))
    users = c.fetchall()
    conn.close()
    return users

# اختبار الاتصال (اختياري)
def test_connection():
    try:
        conn = get_connection()
        print("✅ الاتصال بقاعدة البيانات ناجح!")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ خطأ في الاتصال: {e}")
        return False

# إذا تم تشغيل الملف مباشرة، اختبر الاتصال
if __name__ == "__main__":
    test_connection()
