import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'neuro_bot.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            chat_id INTEGER PRIMARY KEY,
            name TEXT,
            gender TEXT,
            age TEXT,
            greeting TEXT,
            appearance TEXT,
            personality TEXT,
            scenario TEXT,
            memory TEXT,
            tags TEXT,
            photo TEXT,
            msg_limit INTEGER DEFAULT 400
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def init_user(chat_id):
    conn = get_db()
    cur = conn.execute('SELECT chat_id FROM user_settings WHERE chat_id = ?', (chat_id,))
    if not cur.fetchone():
        conn.execute('INSERT INTO user_settings (chat_id) VALUES (?)', (chat_id,))
        conn.commit()
    conn.close()

def update_field(chat_id, field, value):
    conn = get_db()
    conn.execute(f'UPDATE user_settings SET "{field}" = ? WHERE chat_id = ?', (value, chat_id))
    conn.commit()
    conn.close()

def get_field(chat_id, field, default=None):
    conn = get_db()
    cur = conn.execute(f'SELECT "{field}" FROM user_settings WHERE chat_id = ?', (chat_id,))
    row = cur.fetchone()
    conn.close()
    if row and row[0] is not None:
        return row[0]
    return default

def add_to_history(chat_id, user_msg, bot_msg):
    conn = get_db()
    if user_msg:
        conn.execute('INSERT INTO user_history (chat_id, role, content) VALUES (?, ?, ?)', (chat_id, 'user', user_msg))
    if bot_msg:
        conn.execute('INSERT INTO user_history (chat_id, role, content) VALUES (?, ?, ?)', (chat_id, 'assistant', bot_msg))
    conn.commit()
    conn.close()

def get_history(chat_id):
    conn = get_db()
    cur = conn.execute('SELECT role, content FROM user_history WHERE chat_id = ? ORDER BY timestamp DESC LIMIT 40', (chat_id,))
    rows = cur.fetchall()
    conn.close()
    return [{'role': row['role'], 'content': row['content']} for row in reversed(rows)]

def clear_history(chat_id):
    conn = get_db()
    conn.execute('DELETE FROM user_history WHERE chat_id = ?', (chat_id,))
    conn.commit()
    conn.close()

def reset_all(chat_id):
    conn = get_db()
    conn.execute('DELETE FROM user_history WHERE chat_id = ?', (chat_id,))
    conn.execute('DELETE FROM user_settings WHERE chat_id = ?', (chat_id,))
    conn.commit()
    conn.close()
    init_user(chat_id)

# Инициализация БД при старте
init_db()
