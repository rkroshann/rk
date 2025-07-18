from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime
import hashlib
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
DB_PATH = os.path.join(os.path.dirname(__file__), 'auth_data.db')

def init_db():
    with sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                session_start TEXT,
                session_end TEXT,
                swipe_gesture TEXT,
                gyroscope_pattern TEXT,
                wifi_ssid TEXT,
                wifi_bssid TEXT,
                location_lat REAL,
                location_lon REAL,
                login_time TEXT,
                screen_brightness REAL,
                consent INTEGER,
                timestamp TEXT
            )
        ''')
        conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    print('REGISTER request:', data)
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        print('REGISTER error: Username and password required')
        return jsonify({'error': 'Username and password required'}), 400
    password_hash = hash_password(password)
    try:
        with sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
            conn.commit()
        print('REGISTER success:', username)
        return jsonify({'status': 'registered'})
    except sqlite3.IntegrityError as e:
        print('REGISTER error: Username already exists')
        return jsonify({'error': 'Username already exists'}), 409
    except Exception as e:
        print('REGISTER error:', str(e))
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    print('LOGIN request:', data)
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        print('LOGIN error: Username and password required')
        return jsonify({'error': 'Username and password required'}), 400
    password_hash = hash_password(password)
    with sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=? AND password_hash=?', (username, password_hash))
        user = c.fetchone()
    if user:
        print('LOGIN success:', username)
        return jsonify({'status': 'login_success'})
    else:
        print('LOGIN error: Invalid credentials')
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.json
    username = data.get('username')
    new_password = data.get('new_password')
    if not username or not new_password:
        return jsonify({'error': 'Username and new password required'}), 400
    password_hash = hash_password(new_password)
    with sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('UPDATE users SET password_hash=? WHERE username=?', (password_hash, username))
        if c.rowcount == 0:
            return jsonify({'error': 'Username not found'}), 404
        conn.commit()
    return jsonify({'status': 'password_updated'})

# Update /collect_data to check if user is registered
@app.route('/collect_data', methods=['POST'])
def collect_data():
    data = request.json
    required_fields = [
        'username', 'session_start', 'session_end',
        'swipe_gesture', 'gyroscope_pattern', 'wifi_ssid', 'wifi_bssid',
        'location_lat', 'location_lon', 'login_time', 'screen_brightness', 'consent'
    ]
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing fields'}), 400
    if not data['consent']:
        return jsonify({'error': 'User consent required'}), 403
    # Check if user exists
    with sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username=?', (data['username'],))
        if not c.fetchone():
            return jsonify({'error': 'User not registered'}), 403
        c.execute('''
            INSERT INTO user_data (
                username, session_start, session_end,
                swipe_gesture, gyroscope_pattern, wifi_ssid, wifi_bssid,
                location_lat, location_lon, login_time, screen_brightness, consent, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['username'],
            data['session_start'],
            data['session_end'],
            data['swipe_gesture'],
            data['gyroscope_pattern'],
            data['wifi_ssid'],
            data['wifi_bssid'],
            data['location_lat'],
            data['location_lon'],
            data['login_time'],
            data['screen_brightness'],
            int(data['consent']),
            datetime.utcnow().isoformat()
        ))
        conn.commit()
    return jsonify({'status': 'success'})

@app.route('/authenticate', methods=['POST'])
def authenticate():
    data = request.json
    result = {
        'authenticated': False,
        'confidence': 0.0,
        'note': 'ML model not integrated yet.'
    }
    return jsonify({'input': data, 'result': result})

@app.route('/export_csv', methods=['GET'])
def export_csv():
    import csv
    from flask import Response
    with sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM user_data ORDER BY username, session_start')
        rows = c.fetchall()
        headers = [desc[0] for desc in c.description]
    def generate():
        yield ','.join(headers) + '\n'
        for row in rows:
            yield ','.join([str(x) for x in row]) + '\n'
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=all_sessions.csv"})

@app.route("/", methods=["GET"])
def home():
    return "Flask backend is running 🚀"

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0') 