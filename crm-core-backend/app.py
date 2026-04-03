from flask import Flask, render_template_string, request, session, redirect, url_for
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'crm_secret_key_2026'

ADMIN_LOGIN = os.getenv('CRM_ADMIN_LOGIN', 'admin_placeholder')
ADMIN_PASSWORD = os.getenv('CRM_ADMIN_PASSWORD', 'pass_placeholder')

def get_flag():
    try:
        with open('/app/flag', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "CTF{default_flag_if_file_is_missing}"

def init_db():
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY,
                  username TEXT UNIQUE,
                  password TEXT,
                  full_name TEXT,
                  is_admin INTEGER)''')
    c.execute("DELETE FROM users")

    c.execute("INSERT INTO users (username, password, full_name, is_admin) VALUES ('user', 'user123', 'Иван Петров', 0)")
    c.execute("INSERT INTO users (username, password, full_name, is_admin) VALUES (?, ?, 'Алексей Воронов', 1)", (ADMIN_LOGIN, ADMIN_PASSWORD))

    conn.commit()
    conn.close()

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Внутренний портал | CRM</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .card { background: #ffffff; border-top: 5px solid #00529b; border-radius: 8px; padding: 40px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); width: 100%; max-width: 400px; }
        h1 { color: #00529b; text-align: center; margin-top: 0; font-size: 24px; }
        .subtitle { text-align: center; color: #666; margin-bottom: 30px; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 6px; font-weight: 600; font-size: 14px; color: #444; }
        input { width: 100%; padding: 12px; border: 1px solid #ccd0d5; border-radius: 6px; box-sizing: border-box; font-family: monospace; font-size: 15px; transition: border-color 0.3s; }
        input:focus { outline: none; border-color: #00529b; }
        button { width: 100%; padding: 12px; background-color: #00529b; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer; transition: background-color 0.3s; }
        button:hover { background-color: #003d73; }
        .message { margin-top: 20px; padding: 12px; border-radius: 6px; text-align: center; display: none; font-size: 14px; font-weight: 500; }
        .message.error { background: #fee2e2; color: #dc2626; border: 1px solid #f87171; }
        .message.success { background: #d1fae5; color: #059669; border: 1px solid #34d399; }
    </style>
</head>
<body>
    <div class="card">
        <h1>CRM Core</h1>
        <div class="subtitle">Внутренняя система управления</div>
        <form method="POST" id="loginForm">
            <div class="form-group">
                <label>Имя пользователя</label>
                <input type="text" name="username" id="username" required autofocus autocomplete="off">
            </div>
            <div class="form-group">
                <label>Пароль</label>
                <input type="password" name="password" id="password" required>
            </div>
            <button type="submit">Авторизация</button>
        </form>
        <div id="message" class="message"></div>
    </div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const response = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`
            });
            const data = await response.json();
            const msgDiv = document.getElementById('message');
            msgDiv.className = `message ${data.success ? 'success' : 'error'}`;
            msgDiv.textContent = data.message;
            msgDiv.style.display = 'block';
            if (data.success) { setTimeout(() => { window.location.href = data.redirect; }, 1000); }
        });
    </script>
</body>
</html>
'''

DASHBOARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><title>Дашборд</title><style>body{font-family:'Segoe UI',sans-serif;background:#f4f6f9;margin:0;padding:40px;} .card{background:white;padding:40px;border-top:5px solid #00529b;border-radius:8px;box-shadow:0 4px 15px rgba(0,0,0,0.05);max-width:600px;margin:auto;} h1{color:#00529b;margin-top:0;} .flag-box {background:#d1fae5;color:#059669;padding:15px;border-radius:6px;font-family:monospace;font-size:18px;margin:20px 0;} a.btn {display:inline-block;padding:10px 20px;background:#00529b;color:white;border-radius:6px;text-decoration:none;font-weight:600;} a.btn:hover{background:#003d73;}</style></head>
<body>
<div class="card">
<h1>Добро пожаловать, {{ full_name }}</h1>
{% if is_admin %}
    <p>Доступ к закрытому сегменту разрешен.</p>
    <div class="flag-box">Флаг: {{ ctf_flag }}</div>
{% else %}
    <p>Вы вошли как обычный пользователь. Нет доступа к критическим данным.</p>
{% endif %}
<a href="/logout" class="btn">Выйти из системы</a>
</div>
</body>
</html>
'''

@app.route('/', methods=['GET'])
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    conn = sqlite3.connect('crm.db')
    c = conn.cursor()
    check_query = f"SELECT COUNT(*) FROM users WHERE username = '{username}'"

    try:
        c.execute(check_query)
        count = c.fetchone()[0]
        exists = count > 0
    except Exception as e:
        conn.close()
        return {'success': False, 'message': f'Системная ошибка БД: {str(e)}'}

    is_sqli_attempt = any(x in username.lower() for x in ["'", "--", "or ", "substr", "length", "like", "union", "select"])

    if exists:
        auth_query = "SELECT id, full_name, is_admin FROM users WHERE username = ? AND password = ?"
        c.execute(auth_query, (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['full_name'] = user[1]
            session['is_admin'] = user[2]
            return {'success': True, 'message': 'Авторизация успешна. Переадресация...', 'redirect': '/dashboard'}
        else:
            msg = 'Неверный пароль'
            if is_sqli_attempt: msg += ' TRUE'
            return {'success': False, 'message': msg}
    else:
        conn.close()
        msg = 'Пользователь не найден'
        if is_sqli_attempt: msg += ' FALSE'
        return {'success': False, 'message': msg}

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template_string(DASHBOARD_TEMPLATE, full_name=session.get('full_name'), is_admin=session.get('is_admin', False), ctf_flag=get_flag())

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000)
