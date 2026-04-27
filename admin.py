from flask import Flask, render_template_string, request
from flask_httpauth import HTTPBasicAuth
from database import *
import sqlite3
import os

app = Flask(__name__)
auth = HTTPBasicAuth()

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"  # غيرها فوراً

@auth.verify_password
def verify_password(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD

HTML_TEMPLATE = """
<!DOCTYPE html>
<html dir="rtl">
<head>
    <title>🎮 لوحة تحكم البوت</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; padding: 20px; min-height: 100vh; }
        .container { max-width: 1400px; margin: auto; }
        .card { background: white; border-radius: 20px; padding: 25px; margin-bottom: 25px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
        h2 { color: #333; margin-top: 0; border-right: 5px solid #667eea; padding-right: 15px; }
        .flex { display: flex; gap: 20px; flex-wrap: wrap; align-items: flex-end; }
        .form-group { flex: 1; min-width: 150px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; color: #555; }
        input, select { width: 100%; padding: 10px 12px; border: 2px solid #e0e0e0; border-radius: 10px; }
        button { background: #667eea; color: white; border: none; padding: 10px 25px; border-radius: 10px; cursor: pointer; }
        button:hover { background: #5a67d8; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 12px; text-align: center; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; }
        .success { color: #28a745; font-weight: bold; }
        .search-box { width: 100%; max-width: 300px; padding: 10px; margin-bottom: 20px; }
        .stats { display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 20px; }
        .stat-card { background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 15px 25px; border-radius: 15px; flex: 1; text-align: center; }
        .stat-number { font-size: 28px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="stats">
            <div class="stat-card"><div class="stat-number">{{ total_users }}</div><div>👥 المستخدمين</div></div>
            <div class="stat-card"><div class="stat-number">{{ total_rolls }}</div><div>🎲 اللفات</div></div>
            <div class="stat-card"><div class="stat-number">{{ total_wins }}</div><div>🏆 الفوز</div></div>
        </div>

        <div class="card">
            <h2>⚙️ إعدادات اللعبة</h2>
            <form method="POST">
                <div class="flex">
                    <div class="form-group">
                        <label>نسبة الفوز (%)</label>
                        <input type="number" step="1" name="win_probability" value="{{ win_percent }}" required>
                    </div>
                    <div class="form-group">
                        <label>مكافأة الفوز (Coin)</label>
                        <input type="number" name="reward_coins" value="{{ reward_coins }}" required>
                    </div>
                    <div class="form-group">
                        <label>تكلفة اللفة (Coin)</label>
                        <input type="number" name="cost_per_roll" value="{{ cost_per_roll }}" required>
                    </div>
                    <div class="form-group">
                        <button type="submit" name="action" value="save_settings">💾 حفظ</button>
                    </div>
                </div>
            </form>
        </div>

        <div class="card">
            <h2>💰 إدارة الرصيد</h2>
            <form method="POST">
                <div class="flex">
                    <div class="form-group">
                        <label>معرف المستخدم</label>
                        <input type="number" name="user_id" placeholder="مثال: 123456789" required>
                    </div>
                    <div class="form-group">
                        <label>إضافة رصيد</label>
                        <input type="number" name="add_coins" placeholder="الكمية">
                    </div>
                    <div class="form-group">
                        <label>تعيين رصيد جديد</label>
                        <input type="number" name="set_coins" placeholder="الرصيد الجديد">
                    </div>
                    <div class="form-group">
                        <button type="submit" name="action" value="manage_coins">تطبيق</button>
                    </div>
                </div>
            </form>
        </div>

        <div class="card">
            <h2>👥 المستخدمين</h2>
            <input type="text" id="search" class="search-box" placeholder="🔍 بحث..." onkeyup="filterTable()">
            <table id="usersTable">
                <thead><tr><th>#</th><th>المعرف</th><th>الاسم</th><th>الرصيد</th><th>اللفات</th><th>الفوز</th></tr></thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>{{ loop.index }}</td>
                        <td>{{ user[0] }}</td>
                        <td>{{ user[2] or user[1] or user[0] }}</td>
                        <td class="success">{{ user[3] }} Coin</td>
                        <td>{{ user[4] }}</td>
                        <td>{{ user[5] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <script>
        function filterTable() {
            let input = document.getElementById("search").value.toLowerCase();
            let rows = document.querySelectorAll("#usersTable tbody tr");
            rows.forEach(row => {
                row.style.display = row.innerText.toLowerCase().includes(input) ? "" : "none";
            });
        }
    </script>
</body>
</html>
"""

def get_stats():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    total_users = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_rolls = c.execute("SELECT SUM(rolls_count) FROM users").fetchone()[0] or 0
    total_wins = c.execute("SELECT SUM(wins_count) FROM users").fetchone()[0] or 0
    conn.close()
    return total_users, total_rolls, total_wins

@app.route('/admin', methods=['GET', 'POST'])  # <- مسار /admin
@auth.login_required
def admin_panel():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'save_settings':
            win_prob = float(request.form['win_probability']) / 100
            set_setting("win_probability", str(win_prob))
            set_setting("reward_coins", request.form['reward_coins'])
            set_setting("cost_per_roll", request.form['cost_per_roll'])
        elif action == 'manage_coins':
            user_id = int(request.form['user_id'])
            add_coins = request.form.get('add_coins', '0')
            set_coins = request.form.get('set_coins', '')
            user = get_user(user_id)
            if user:
                if set_coins:
                    update_user_coins(user_id, int(set_coins))
                elif add_coins:
                    update_user_coins(user_id, user[3] + int(add_coins))
    
    win_percent = float(get_setting("win_probability")) * 100
    reward_coins = get_setting("reward_coins")
    cost_per_roll = get_setting("cost_per_roll")
    total_users, total_rolls, total_wins = get_stats()
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    users = c.execute("SELECT * FROM users ORDER BY coins DESC").fetchall()
    conn.close()
    
    return render_template_string(HTML_TEMPLATE, win_percent=win_percent, reward_coins=reward_coins,
                                  cost_per_roll=cost_per_roll, users=users,
                                  total_users=total_users, total_rolls=total_rolls, total_wins=total_wins)

# مسار رئيسي يعرض حالة البوت
@app.route('/')
def index():
    return "✅ Bot is running! لوحة التحكم: /admin"

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 10000))  # استخدام المنفذ 10000
    app.run(host='0.0.0.0', port=port)
