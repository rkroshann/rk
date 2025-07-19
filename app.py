from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime
import hashlib
from flask_cors import CORS
import pandas as pd
import io

app = Flask(__name__)
CORS(app)
DB_PATH = os.path.join(os.path.dirname(__file__), 'auth_data.db')

def init_db():
    with sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False) as conn:
        c = conn.cursor()
        
        # Drop existing tables to clear data
        c.execute('DROP TABLE IF EXISTS user_data')
        c.execute('DROP TABLE IF EXISTS users')
        
        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password_hash TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create restructured user_data table with proper column management
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                session_id TEXT,
                session_start TEXT,
                session_end TEXT,
                swipe_gesture_coordinates TEXT,
                swipe_gesture_pattern TEXT,
                gyroscope_pattern TEXT,
                wifi_ssid TEXT,
                wifi_bssid TEXT,
                location_lat REAL,
                location_lon REAL,
                login_time TEXT,
                screen_brightness REAL,
                consent INTEGER,
                timestamp TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Create user_sessions table to track session columns
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                session_column INTEGER,
                first_login_date TEXT,
                last_login_date TEXT,
                total_sessions INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_next_session_column(username):
    """Get the next available session column for a user"""
    with sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('SELECT MAX(session_column) FROM user_sessions WHERE username = ?', (username,))
        result = c.fetchone()
        return (result[0] or 0) + 1

def get_or_create_user_session(username):
    """Get or create user session record"""
    with sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM user_sessions WHERE username = ?', (username,))
        user_session = c.fetchone()
        
        if not user_session:
            # Create new user session with next column
            session_column = get_next_session_column(username)
            c.execute('''
                INSERT INTO user_sessions (username, session_column, first_login_date, last_login_date, total_sessions)
                VALUES (?, ?, ?, ?, 1)
            ''', (username, session_column, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
            conn.commit()
            return session_column
        else:
            # Update existing user session
            c.execute('''
                UPDATE user_sessions 
                SET last_login_date = ?, total_sessions = total_sessions + 1
                WHERE username = ?
            ''', (datetime.utcnow().isoformat(), username))
            conn.commit()
            return user_session[2]  # session_column

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
            user_id = c.lastrowid
            conn.commit()
        print('REGISTER success:', username)
        return jsonify({'status': 'registered', 'user_id': user_id})
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
        # Get or create user session
        session_column = get_or_create_user_session(username)
        print('LOGIN success:', username, 'Session column:', session_column)
        return jsonify({'status': 'login_success', 'session_column': session_column})
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

@app.route('/collect_data', methods=['POST'])
def collect_data():
    data = request.json
    print('COLLECT_DATA request:', data)
    
    # Define all possible fields with their default values
    field_defaults = {
        'username': None,
        'session_start': None,
        'session_end': None,
        'swipe_gesture_coordinates': None,
        'swipe_gesture_pattern': None,
        'gyroscope_pattern': None,
        'wifi_ssid': None,
        'wifi_bssid': None,
        'location_lat': 0.0,
        'location_lon': 0.0,
        'login_time': None,
        'screen_brightness': 0.0,
        'consent': True  # Default to True
    }
    
    # Fill missing fields with defaults
    for field, default_value in field_defaults.items():
        if field not in data or data[field] is None:
            data[field] = default_value
    
    # Ensure username is provided
    if not data['username']:
        return jsonify({'error': 'Username is required'}), 400
    
    # Always allow submission regardless of consent (default is True)
    print(f"Processing data for user: {data['username']}, consent: {data['consent']}")
    
    # Check if user exists, if not create them automatically
    try:
        with sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE username=?', (data['username'],))
            user_result = c.fetchone()
            
            if not user_result:
                # Auto-create user if they don't exist
                print(f"Auto-creating user: {data['username']}")
                c.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                         (data['username'], hash_password('default_password')))
                user_id = c.lastrowid
                conn.commit()
            else:
                user_id = user_result[0]
            
            session_id = f"{data['username']}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            c.execute('''
                INSERT INTO user_data (
                    user_id, username, session_id, session_start, session_end,
                    swipe_gesture_coordinates, swipe_gesture_pattern, gyroscope_pattern, 
                    wifi_ssid, wifi_bssid, location_lat, location_lon, 
                    login_time, screen_brightness, consent, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, data['username'], session_id,
                data['session_start'], data['session_end'],
                data['swipe_gesture_coordinates'], data['swipe_gesture_pattern'], data['gyroscope_pattern'],
                data['wifi_ssid'], data['wifi_bssid'],
                data['location_lat'], data['location_lon'],
                data['login_time'], data['screen_brightness'],
                int(data['consent']), datetime.utcnow().isoformat()
            ))
            conn.commit()
        
        print(f"Data collected successfully for user: {data['username']}, session: {session_id}")
        return jsonify({'status': 'success', 'session_id': session_id})
        
    except Exception as e:
        print(f"Error collecting data: {str(e)}")
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/authenticate', methods=['POST'])
def authenticate():
    data = request.json
    result = {
        'authenticated': False,
        'confidence': 0.0,
        'note': 'ML model not integrated yet.'
    }
    return jsonify({'input': data, 'result': result})

@app.route('/export_excel', methods=['GET'])
def export_excel():
    """Export data to Excel with proper column structure"""
    try:
        with sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False) as conn:
            # Get all user sessions to understand column structure
            sessions_df = pd.read_sql_query('''
                SELECT username, session_column, total_sessions, first_login_date, last_login_date
                FROM user_sessions 
                ORDER BY session_column
            ''', conn)
            
            # Get all user data
            data_df = pd.read_sql_query('''
                SELECT username, session_id, session_start, session_end,
                       swipe_gesture_coordinates, swipe_gesture_pattern, gyroscope_pattern,
                       wifi_ssid, wifi_bssid, location_lat, location_lon,
                       login_time, screen_brightness, consent, timestamp
                FROM user_data 
                ORDER BY username, session_start
            ''', conn)
        
        # Create Excel writer
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Write user sessions summary
            sessions_df.to_excel(writer, sheet_name='User_Sessions', index=False)
            
            # Write detailed data
            data_df.to_excel(writer, sheet_name='Session_Data', index=False)
            
            # Create structured data sheet with proper columns
            if not data_df.empty:
                # Group by username and create structured columns
                structured_data = []
                for username in data_df['username'].unique():
                    user_data = data_df[data_df['username'] == username]
                    user_session = sessions_df[sessions_df['username'] == username]
                    
                    if not user_session.empty:
                        session_column = user_session.iloc[0]['session_column']
                        
                        for idx, row in user_data.iterrows():
                            structured_row = {
                                'User': username,
                                'Session_Column': session_column,
                                'Session_ID': row['session_id'],
                                'Session_Start': row['session_start'],
                                'Session_End': row['session_end'],
                                'Swipe_Coordinates': row['swipe_gesture_coordinates'] or 'NULL',
                                'Swipe_Pattern': row['swipe_gesture_pattern'] or 'NULL',
                                'Gyroscope_Pattern': row['gyroscope_pattern'] or 'NULL',
                                'WiFi_SSID': row['wifi_ssid'] or 'NULL',
                                'WiFi_BSSID': row['wifi_bssid'] or 'NULL',
                                'Location_Lat': row['location_lat'] or 'NULL',
                                'Location_Lon': row['location_lon'] or 'NULL',
                                'Login_Time': row['login_time'],
                                'Screen_Brightness': row['screen_brightness'] or 'NULL',
                                'Consent': 'Yes' if row['consent'] else 'No',
                                'Timestamp': row['timestamp']
                            }
                            structured_data.append(structured_row)
                
                structured_df = pd.DataFrame(structured_data)
                structured_df.to_excel(writer, sheet_name='Structured_Data', index=False)
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.read(),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={"Content-Disposition": "attachment;filename=suraksha_data.xlsx"}
        )
        
    except Exception as e:
        print(f"Excel export error: {str(e)}")
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@app.route('/export_csv', methods=['GET'])
def export_csv():
    import csv
    from flask import Response
    with sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute('''
            SELECT username, session_id, session_start, session_end,
                   swipe_gesture_coordinates, swipe_gesture_pattern, gyroscope_pattern,
                   wifi_ssid, wifi_bssid, location_lat, location_lon,
                   login_time, screen_brightness, consent, timestamp
            FROM user_data 
            ORDER BY username, session_start
        ''')
        rows = c.fetchall()
        headers = [desc[0] for desc in c.description]
    def generate():
        yield ','.join(headers) + '\n'
        for row in rows:
            yield ','.join([str(x) if x is not None else 'NULL' for x in row]) + '\n'
    return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=suraksha_data.csv"})

@app.route('/clear_data', methods=['POST'])
def clear_data():
    """Clear all data from database"""
    try:
        with sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute('DELETE FROM user_data')
            c.execute('DELETE FROM user_sessions')
            c.execute('DELETE FROM users')
            conn.commit()
        return jsonify({'status': 'Data cleared successfully'})
    except Exception as e:
        return jsonify({'error': f'Failed to clear data: {str(e)}'}), 500

@app.route("/", methods=["GET"])
def home():
    return "Flask backend is running 🚀"

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0') 