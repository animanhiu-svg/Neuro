# Хранилища данных
user_settings = {}
user_history = {}

def init_user(chat_id):
    if chat_id not in user_settings:
        user_settings[chat_id] = {
            'name': None,
            'gender': None,
            'age': None,
            'greeting': None,
            'appearance': None,
            'personality': None,
            'scenario': None,
            'memory': None,
            'tags': None,
            'photo': None,
            'limit': 400
        }

def update_field(chat_id, field, value):
    init_user(chat_id)
    user_settings[chat_id][field] = value

def get_field(chat_id, field, default=None):
    return user_settings.get(chat_id, {}).get(field, default)

def add_to_history(chat_id, user_msg, bot_msg):
    if chat_id not in user_history:
        user_history[chat_id] = []
    if user_msg:
        user_history[chat_id].append({"role": "user", "content": user_msg})
    if bot_msg:
        user_history[chat_id].append({"role": "assistant", "content": bot_msg})
    if len(user_history[chat_id]) > 50:
        user_history[chat_id] = user_history[chat_id][-50:]

def get_history(chat_id):
    return user_history.get(chat_id, [])[-40:]

def clear_history(chat_id):
    if chat_id in user_history:
        user_history[chat_id] = []

def reset_all(chat_id):
    if chat_id in user_settings:
        del user_settings[chat_id]
    if chat_id in user_history:
        del user_history[chat_id]
    init_user(chat_id)
