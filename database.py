# Хранилища данных пользователей (в памяти)
user_settings = {}      # {chat_id: {'limit': 400, 'personality': 'neutral', 'custom_prompt': None,
                        #            'char_name': None, 'char_description': None, 'char_scenario': None}}
user_history = {}       # {chat_id: [messages]}
menu_message_id = {}    # {chat_id: message_id} — текущее открытое Inline-меню

def update_user_setting(chat_id, key, value):
    if chat_id not in user_settings:
        user_settings[chat_id] = {
            'limit': 400,
            'personality': 'neutral',
            'custom_prompt': None,
            'char_name': None,
            'char_description': None,
            'char_scenario': None
        }
    user_settings[chat_id][key] = value

def get_user_setting(chat_id, key, default=None):
    return user_settings.get(chat_id, {}).get(key, default)

def add_to_history(chat_id, user_msg, bot_msg):
    if chat_id not in user_history:
        user_history[chat_id] = []
    user_history[chat_id].append({"role": "user", "content": user_msg})
    user_history[chat_id].append({"role": "assistant", "content": bot_msg})
    if len(user_history[chat_id]) > 40:
        user_history[chat_id] = user_history[chat_id][-40:]

def clear_history(chat_id):
    user_history[chat_id] = []

def get_history(chat_id):
    return user_history.get(chat_id, [])[-20:]

def reset_all(chat_id):
    user_settings[chat_id] = {
        'limit': 400,
        'personality': 'neutral',
        'custom_prompt': None,
        'char_name': None,
        'char_description': None,
        'char_scenario': None
    }
    user_history[chat_id] = []
