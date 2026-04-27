from flask import Flask, render_template_string, request, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from database import *

app = Flask(__name__)
auth = HTTPBasicAuth()

# التحقق من كلمة المرور (تأخذها من قاعدة البيانات)
@auth.verify_password
def verify_password(username, password):
    admin_password = get_setting("admin_password")
    if username == "admin" and password == admin_password:
        return True
    return False

# قالب HTML للوحة التحكم
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>لوحة تحكم البوت</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; padding: 20px; direction: rtl; background: #f5f5f5; }
        .container { max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 10px; }
        input, select { width: 100%; padding: 8px; margin: 5px 0 15px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: center; }
        th { background: #007bff; color: white; }
        .success { color: green; }
        .user-card { background: #e9ecef; padding: 10px; margin: 10px 0; border-radius: 5px; }
        .flex { display: flex; gap: 10px; align-items: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 لوحة تحكم البوت</h1>
        
        <form method="POST">
            <h3>⚙️ إعدادات اللعبة</h3>
            <label>نسبة الفوز (مثال: 0.1666 = 16.66%)</label>
            <input type="number" step="0.0001" name="win_probability" value="{{ settings.win_probability }}" required>
            
            <label>مكافأة الفوز (Coin)</label>
            <input type="number" name="reward_coins" value="{{ settings.reward_coins }}" required>
            
            <label>تكلفة اللفة (Coin)</label>
            <input type="number" name="cost_per_roll" value="{{ settings.cost_per_roll }}" required>
            
            <label>كلمة مرور المشرف</label>
            <input type="text" name="admin_password" value="{{ settings.admin_password }}" required>
            
            <button type="submit">💾 حفظ الإعدادات</button>
        </form>
        
        <hr>
        
        <h3>👥 المستخدمون</h3>
        <table>
            <tr><th>المعرف</th><th>الاسم</th><th>الرصيد</th><th>اللفات</th><th>الفوز</th><th>إجراء</th></tr>
            {% for user in users %}
            <tr>
                <td>{{ user[0] }}</td>
                <td>{{ user[2] or user[1] or user[0] }}</td>
                <td>{{ user[3] }}</td>
                <td>{{ user[4] }}</td>
                <td>{{ user[5] }}</td>
                <td>
                    <form method="POST" style="display:inline;">
                        <input type="hidden" name="user_id" value="{{ user[0] }}">
                        <input type="number" name="new_coins" placeholder="تعديل الرصيد" style="width:80px;">
                        <button type="submit" name="action" value="update_coins">تعديل</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
        
        <hr>
        
        <h3>📜 آخر 20 لفة</h3>
        <table>
            <tr><th>المستخدم</th><th>اللفة</th><th>النتيجة</th><th>فوز؟</th><th>الرصيد قبل</th><th>بعد</th><th>التاريخ</th></tr>
            {% for log in logs %}
            <tr>
                <td>{{ log[1] }}</td>
                <td>{{ log[2] }}</td>
                <td>{{ log[3] }}</td>
                <td>{{ '✅' if log[4] else '❌' }}</td>
                <td>{{ log[5] }}</td>
                <td>{{ log[6] }}</td>
                <td>{{ log[7] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def admin_panel():
    if request.method == 'POST':
        if 'win_probability' in request.form:
            # حفظ الإعدادات
            set_setting("win_probability", request.form['win_probability'])
            set_setting("reward_coins", request.form['reward_coins'])
            set_setting("cost_per_roll", request.form['cost_per_roll'])
            set_setting("admin_password", request.form['admin_password'])
        elif request.form.get('action') == 'update_coins':
            user_id = int(request.form['user_id'])
            new_coins = int(request.form['new_coins'])
            update_user_coins(user_id, new_coins)
    
    # جلب البيانات
    settings = {
        "win_probability": get_setting("win_probability"),
        "reward_coins": get_setting("reward_coins"),
        "cost_per_roll": get_setting("cost_per_roll"),
        "admin_password": get_setting("admin_password")
    }
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    users = c.execute("SELECT * FROM users ORDER BY coins DESC").fetchall()
    logs = c.execute('''SELECT * FROM rolls_log 
                        JOIN users ON rolls_log.user_id = users.user_id 
                        ORDER BY rolls_log.created_at DESC LIMIT 20''').fetchall()
    conn.close()
    
    # تنظيف logs للعرض
    clean_logs = []
    for log in logs:
        name = log[10] or log[9] or str(log[8])
        clean_logs.append((name, log[1], log[2], log[3], log[4], log[5], log[6], log[13]))
    
    return render_template_string(HTML_TEMPLATE, settings=settings, users=users, logs=clean_logs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)