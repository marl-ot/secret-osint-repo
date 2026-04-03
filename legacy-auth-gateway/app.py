#!/usr/bin/env python3
from flask import Flask, request, render_template_string, jsonify
import sqlite3
import os

app = Flask(__name__)

ADMIN_LOGIN = os.getenv('LEGACY_ADMIN_LOGIN', 'admin')
ADMIN_PASSWORD = os.getenv('LEGACY_ADMIN_PASSWORD', 'placeholder')

def get_flag():
    try:
        with open('/app/flag', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return "FLAG{default_flag_if_file_is_missing}"

def init_database():
    conn = sqlite3.connect('ctf.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, login TEXT NOT NULL, password TEXT NOT NULL)''')
    cursor.execute('DELETE FROM users')
    cursor.execute('INSERT INTO users (id, login, password) VALUES (1, ?, ?)', (ADMIN_LOGIN, ADMIN_PASSWORD))
    conn.commit()
    conn.close()

MAIN_PAGE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Внутренний портал | Auth Gateway</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .card { background: #ffffff; border-top: 5px solid #00529b; border-radius: 8px; padding: 40px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); width: 100%; max-width: 400px; }
        h1 { color: #00529b; text-align: center; margin-top: 0; font-size: 24px; }
        .subtitle { text-align: center; color: #666; margin-bottom: 30px; font-size: 14px; }
        .badge { display: inline-block; background: #e2e8f0; color: #475569; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-bottom: 20px; font-weight: 600; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 6px; font-weight: 600; font-size: 14px; color: #444; }
        input { width: 100%; padding: 12px; border: 1px solid #ccd0d5; border-radius: 6px; box-sizing: border-box; font-family: monospace; font-size: 15px; }
        input:focus { outline: none; border-color: #00529b; }
        button { width: 100%; padding: 12px; background-color: #00529b; color: white; border: none; border-radius: 6px; font-size: 16px; font-weight: 600; cursor: pointer; transition: background-color 0.3s; }
        button:hover { background-color: #003d73; }
        .result { margin-top: 20px; padding: 15px; border-radius: 6px; font-size: 13px; display: none; background: #f8fafc; border: 1px solid #e2e8f0; }
        .result.success { border-left: 4px solid #059669; display: block; }
        .result.error { border-left: 4px solid #dc2626; display: block; }
        .flag { color: #059669; font-weight: bold; font-family: monospace; font-size: 16px; margin-top: 10px; padding-top: 10px; border-top: 1px solid #e2e8f0; }
    </style>
</head>
<body>
    <div class="card">
        <div style="text-align: center;"><span class="badge">LEGACY SYSTEM V1.2</span></div>
        <h1>Auth Gateway</h1>
        <div class="subtitle">Устаревший шлюз авторизации</div>
        <form id="loginForm">
            <div class="form-group">
                <label>Логин служебной УЗ</label>
                <input type="text" id="login" autocomplete="off">
            </div>
            <div class="form-group">
                <label>Пароль</label>
                <input type="password" id="password">
            </div>
            <button type="submit">Подключиться</button>
        </form>
        <div id="result" class="result"></div>
    </div>
    <script>
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new URLSearchParams();
            formData.append('login', document.getElementById('login').value);
            formData.append('password', document.getElementById('password').value);
            const resultDiv = document.getElementById('result');
            
            try {
                const response = await fetch('/login', { method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body: formData });
                const data = await response.json();
                if (data.success) {
                    resultDiv.className = 'result success';
                    resultDiv.innerHTML = `<div style="color:#059669;font-weight:bold;margin-bottom:10px;">Доступ разрешен</div><div class="flag">${data.flag}</div>`;
                } else {
                    resultDiv.className = 'result error';
                    resultDiv.innerHTML = `<div style="color:#dc2626;font-weight:bold;">Ошибка доступа</div><div>${data.message}</div>`;
                }
            } catch (error) {
                resultDiv.className = 'result error';
                resultDiv.innerHTML = `<div style="color:#dc2626;">Системная ошибка связи</div>`;
            }
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(MAIN_PAGE)

@app.route('/login', methods=['POST'])
def login():
    login = request.form.get('login', '')
    password = request.form.get('password', '')
    conn = sqlite3.connect('ctf.db')
    cursor = conn.cursor()
    try:
        query = f"SELECT * FROM users WHERE login = '{login}' AND password = '{password}'"
        cursor.execute(query)
        result = cursor.fetchone()
        if result:
            return jsonify({'success': True, 'flag': get_flag(), 'query': query})
        else:
            return jsonify({'success': False, 'message': 'Access Denied', 'query': query})
    except Exception as e:
        return jsonify({'success': False, 'message': f'SQL Error: {str(e)}', 'query': query})
    finally:
        conn.close()

if __name__ == '__main__':
    if not os.path.exists('ctf.db'): init_database()
    app.run(host='0.0.0.0', port=5000, debug=False)
