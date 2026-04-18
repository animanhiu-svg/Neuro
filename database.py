import sqlite3
import json
from typing import List, Dict, Any, Optional

DB_PATH = "neuro_bot.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        # Таблица настроек персонажей (привязка к chat_id + character_id)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS character_settings (
                chat_id INTEGER,
                character_id INTEGER,
                field TEXT,
                value TEXT,
                PRIMARY KEY (chat_id, character_id, field)
            )
        ''')
        # Таблица истории сообщений
        conn.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                character_id INTEGER,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Индекс для быстрой выборки последних сообщений
        conn.execute('CREATE INDEX IF NOT EXISTS idx_history ON chat_history(chat_id, character_id, timestamp)')
        conn.commit()

# Инициализация при старте
init_db()

def init_user(chat_id: int, character_id: int):
    """Не нужна для SQLite, но оставим для совместимости"""
    pass

def update_field(chat_id: int, character_id: int, field: str, value: Any):
    with get_db() as conn:
        # Сохраняем как JSON, чтобы поддерживать любые типы
        val_json = json.dumps(value, ensure_ascii=False)
        conn.execute('''
            INSERT OR REPLACE INTO character_settings (chat_id, character_id, field, value)
            VALUES (?, ?, ?, ?)
        ''', (chat_id, character_id, field, val_json))
        conn.commit()

def get_field(chat_id: int, character_id: int, field: str, default=None):
    with get_db() as conn:
        row = conn.execute('''
            SELECT value FROM character_settings
            WHERE chat_id=? AND character_id=? AND field=?
        ''', (chat_id, character_id, field)).fetchone()
        if row:
            return json.loads(row['value'])
        return default

def add_to_history(chat_id: int, character_id: int, user_msg: Optional[str], bot_msg: Optional[str]):
    with get_db() as conn:
        if user_msg:
            conn.execute('''
                INSERT INTO chat_history (chat_id, character_id, role, content)
                VALUES (?, ?, ?, ?)
            ''', (chat_id, character_id, 'user', user_msg))
        if bot_msg:
            conn.execute(''br
                INSERT INTO chat_history (chat_id, character_id, role, content)
                VALUES (?, ?, ?, ?)
            ''', (chat_id, character_id, 'assistant', bot_msg))
        conn.commit()

def get_history(chat_id: int, character_id: int, limit: int = 60) -> List[Dict[str, str]]:
    with get_db() as conn:
        rows = conn.execute('''
            SELECT role, content FROM chat_history
            WHERE chat_id=? AND character_id=?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (chat_id, character_id, limit)).fetchall()
        # Возвращаем в хронологическом порядке (от старых к новым)
        history = [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
        return history

def clear_history(chat_id: int, character_id: int):
    with get_db() as conn:
        conn.execute('''
            DELETE FROM chat_history
            WHERE chat_id=? AND character_id=?
        ''', (chat_id, character_id))
        conn.commit()

def reset_all(chat_id: int):
    with get_db() as conn:
        # Удаляем все настройки и историю для данного chat_id
        conn.execute('DELETE FROM character_settings WHERE chat_id=?', (chat_id,))
        conn.execute('DELETE FROM chat_history WHERE chat_id=?', (chat_id,))
        conn.commit()
