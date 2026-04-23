user_settings = {}
user_history = {}

def get_history_key(chat_id, character_id):
    return f"{chat_id}_{character_id}"

def init_user(chat_id):
    if chat_id not in user_settings:
        user_settings[chat_id] = {
            'name': None, 'gender': None, 'age': None,
            'greeting': None, 'appearance': None,
            'personality': None, 'scenario': None,
            'memory': None, 'tags': None, 'photo': None,
            'limit': 400
        }

def update_field(chat_id, field, value):
    init_user(chat_id)
    user_settings[chat_id][field] = value

def get_field(chat_id, field, default=None):
    return user_settings.get(chat_id, {}).get(field, default)

def add_to_history(chat_id, character_id, user_msg, bot_msg):
    key = get_history_key(chat_id, character_id)
    if key not in user_history:
        user_history[key] = []
    if user_msg:
        user_history[key].append({"role": "user", "content": user_msg})
    if bot_msg:
        user_history[key].append({"role": "assistant", "content": bot_msg})
    # Увеличил до 200 сообщений
    if len(user_history[key]) > 200:
        user_history[key] = user_history[key][-200:]

def get_history(chat_id, character_id):
    key = get_history_key(chat_id, character_id)
    # Возвращаем последние 160 сообщений
    return user_history.get(key, [])[-160:]

def clear_history(chat_id, character_id):
    key = get_history_key(chat_id, character_id)
    if key in user_history:
        user_history[key] = []

def reset_all(chat_id):
    if chat_id in user_settings:
        del user_settings[chat_id]
    keys_to_delete = [k for k in user_history if k.startswith(f"{chat_id}_")]
    for k in keys_to_delete:
        del user_history[k]
    init_user(chat_id)
