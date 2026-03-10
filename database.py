# Хранилища данных
user_settings = {}      # {chat_id: {name, gender, greeting, subtitles, memory_cards, char_photo, location, scenario, relation, limit?}}
user_history = {}       # {chat_id: [messages]}
menu_message_id = {}    # {chat_id: message_id} — текущее открытое меню

def init_user(chat_id):
    if chat_id not in user_settings:
        user_settings[chat_id] = {
            'name': None,
            'gender': None,
            'greeting': None,
            'subtitles': None,
            'memory_cards': None,
            'char_photo': None,
            'location': None,
            'scenario': None,
            'relation': None,
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
    user_history[chat_id].append({"role": "user", "content": user_msg})
    user_history[chat_id].append({"role": "assistant", "content": bot_msg})
    if len(user_history[chat_id]) > 40:
        user_history[chat_id] = user_history[chat_id][-40:]

def get_history(chat_id):
    return user_history.get(chat_id, [])[-20:]

def clear_history(chat_id):
    user_history[chat_id] = []

def reset_all(chat_id):
    user_settings[chat_id] = {
        'name': None,
        'gender': None,
        'greeting': None,
        'subtitles': None,
        'memory_cards': None,
        'char_photo': None,
        'location': None,
        'scenario': None,
        'relation': None,
        'limit': 400
    }
    clear_history(chat_id)
