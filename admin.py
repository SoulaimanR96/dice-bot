from flask import Flask, render_template_string, request, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from database import *
import sqlite3

app = Flask(__name__)
auth = HTTPBasicAuth()

# كلمة مرور الدخول للوحة التحكم
ADMIN_PASSWORD = "Jj170315@@@"  # غيّرها فوراً

@auth.verify_password
def verify_password(username, password):
    if username == "admin" and password == ADMIN_PASSWORD:
        return True
    return False

# قالب HTML بسيط
HTML = """
<!DOCTYPE html>
<html dir="rtl">
<head>
    <title>لوحة تحكم البوت</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { font-family: 'Segoe UI', Arial; box-sizing: border-box; }
        body { background: #1e1e2f; padding: 20px; margin: 0; }
        .container { max-width: 1200px; margin: auto; }
        .card { background: white; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h2 { color: #333; margin-top: 0; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        h3 { color: #555; margin-top: 0; }
        .flex { display: flex; gap: 15px; flex-wrap: wrap; align-items: center; }
        input, select, button { padding: 10px 15px; border-radius: 8px; border: 1px solid #ddd; font-size: 14px; }
        button { background: #007bff; color: white; border: none; cursor: pointer; transition: 0.2s; }
        button:hover { background: #0056b3; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { padding: 10px; text-align: center; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; color: #333; }
        .success { color: green; font-weight: bold; }
        .danger { color: red; }
        .badge { background: #28a745; color: white; padding: 4px 8px; border-radius: 20px; font-size: 12px; }
        .search-box { width: 300px; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <!-- إعدادات اللعبة -->
        <div class="card">
            <h2>⚙️ إعدادات اللعبة</h2>
            <form method="POST">
                <div class="flex">
                    <div>
                        <label>نسبة الفوز (%)</label>
                        <input type="number" step="0.1" name="win_probability" value="{{ win_percent }}" required>
                    </div>
                    <div>
                        <label>مكافأة الفوز (Coin)</label>
                        <input type="number" name="reward_coins" value="{{ reward_coins }}" required>
                    </div>
                    <div>
                        <label>تكلفة اللفة (Coin)</label>
                        <input type="number" name="cost_per_roll" value="{{ cost_per_roll }}" required>
                    </div>
                    <div>
                        <label>&nbsp;</label><br>
                        <button type="submit">💾 حفظ الإعدادات</button>
                    </div>
                </div>
            </form>
        </div>
        
        <!-- إضافة رصيد لمستخدم -->
        <div class="card">
            <h2>💰 إدارة أرصدة المستخدمين</h2>
            <form method="POST">
                <div class="flex">
                    <div>
                        <label>معرف المستخدم (ID)</label>
                        <input type="number" name="user_id" placeholder="مثال: 123456789" required>
                    </div>
                    <div>
                        <label>المبلغ (Coin)</label>
                        <input type="number" name="add_coins" placeholder="مثال: 100" required>
                    </div>
                    <div>
                        <label>&nbsp;</label><br>
                        <button type="submit" name="action" value="add_coins">➕ إضافة رصيد</button>
                    </div>
                </div>
            </form>
        </div>
        
        <!-- قائمة المستخدمين -->
        <div class="card">
            <h2>👥 قائمة المستخدمين</h2>
            <input type="text" id="search" class="search-box" placeholder="🔍 بحث باسم أو معرف..." onkeyup="filterTable()">
            <table id="usersTable">
                <thead>
                    <tr>
                        <th>المعرف</th>
                        <th>الاسم</th>
                        <th>الرصيد</th>
                        <th>اللفات</th>
                        <th>الفوز</th>
                        <th>إجراء</th>
                    </tr>
                </thead>
                <tbody>
                    {% for user in users %}
                    <tr>
                        <td>{{ user[0] }}</td>
                        <td>{{ user[2] or user[1] or user[0] }}</td>
                        <td class="{% if user[3] > 0 %}success{% endif %}">{{ user[3] }} Coin</td>
                        <td>{{ user[4] }}</td>
                        <td>{{ user[5] }}</td>
                        <td>
                            <form method="POST" style="display:inline;">
                                <input type="hidden" name="user_id" value="{{ user[0] }}">
                                <input type="number" name="set_coins" placeholder="تعديل" style="width:80px;">
                                <button type="submit" name="action" value="set_coins" style="background:#ffc107; color:#333;">تعديل</button>
                            </form>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        
        <!-- آخر 20 لفة -->
        <div class="card">
            <h2>📜 آخر 20 لفة</h2>
            <table>
                <thead>
                    <tr>
                        <th>المستخدم</th>
                        <th>اللفة</th>
                        <th>النتيجة</th>
                        <th>الحالة</th>
                    </tr>
                </thead>
                <tbody>
                    {% for log in logs %}
                    <tr>
                        <td>{{ log[1] }}</td>
                        <td>{{ log[2] }}</td>
                        <td>{{ log[3] }}</td>
                        <td>{% if log[4] %}✅ فوز{% else %}❌ خسارة{% endif %}</td>
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
                let text = row.innerText.toLowerCase();
                row.style.display = text.includes(input) ? "" : "none";
            });
        }
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def admin():
    if request.method == 'POST':
        if 'win_probability' in request.form:
            # حفظ الإعدادات
            win_prob = float(request.form['win_probability']) / 100
            set_setting("win_probability", str(win_prob))
            set_setting("reward_coins", request.form['reward_coins'])
            set_setting("cost_per_roll", request.form['cost_per_roll'])
        
        elif request.form.get('action') == 'add_coins':
            user_id = int(request.form['user_id'])
            coins = int(request.form['add_coins'])
            user = get_user(user_id)
            if user:
                new_coins = user[3] + coins
                update_user_coins(user_id, new_coins)
        
        elif request.form.get('action') == 'set_coins':
            user_id = int(request.form['user_id'])
            new_coins = int(request.form['set_coins'])
            update_user_coins(user_id, new_coins)
    
    # جلب البيانات
    win_prob = float(get_setting("win_probability")) * 100
    reward_coins = get_setting("reward_coins")
    cost_per_roll = get_setting("cost_per_roll")
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    users = c.execute("SELECT * FROM users ORDER BY coins DESC").fetchall()
    logs = c.execute('''SELECT rolls_log.id, users.first_name, rolls_log.roll_number, 
                        rolls_log.result, rolls_log.is_win
                        FROM rolls_log 
                        JOIN users ON rolls_log.user_id = users.user_id 
                        ORDER BY rolls_log.created_at DESC LIMIT 20''').fetchall()
    conn.close()
    
    return render_template_string(HTML, win_percent=win_prob, reward_coins=reward_coins,
                                  cost_per_roll=cost_per_roll, users=users, logs=logs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)