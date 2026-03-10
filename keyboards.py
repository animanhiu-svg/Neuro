from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database import get_user_setting, user_history
from logic import get_personality_name

# -------------------- Reply-клавиатуры --------------------
def reply_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("📜 Сценарии"),
        KeyboardButton("⚙️ Настройки"),
        KeyboardButton("❓ Помощь"),
        KeyboardButton("ℹ️ О боте"),
        KeyboardButton("🎮 Меню")
    )
    return markup

def reply_start_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("🎮 НАЧАТЬ РОЛЕВУЮ ИГРУ"))
    return markup

# -------------------- Inline-меню --------------------
def main_menu_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📜 Сценарии", callback_data="main_scenarios"),
        InlineKeyboardButton("⚙️ Настройки", callback_data="main_settings"),
        InlineKeyboardButton("❓ Помощь", callback_data="main_help"),
        InlineKeyboardButton("ℹ️ О боте", callback_data="main_about"),
        InlineKeyboardButton("❌ Закрыть", callback_data="close_menu")
    )
    return markup

def settings_main_keyboard(chat_id):
    limit = get_user_setting(chat_id, 'limit', 400)
    personality = get_user_setting(chat_id, 'personality', 'neutral')
    history_count = len(user_history.get(chat_id, [])) // 2
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎭 Характер", callback_data="settings_character"),
        InlineKeyboardButton("📏 Лимит", callback_data="settings_limit"),
        InlineKeyboardButton("📊 История", callback_data="settings_history"),
        InlineKeyboardButton("🔄 Сбросить всё", callback_data="reset_all"),
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"),
        InlineKeyboardButton("❌ Закрыть", callback_data="close_menu")
    )
    text = (f"⚙️ **Настройки**\n\n"
            f"• Характер: {get_personality_name(personality)}\n"
            f"• Лимит: {limit} токенов\n"
            f"• История: {history_count} диалогов")
    return markup, text

def character_menu_keyboard(chat_id):
    current = get_user_setting(chat_id, 'personality', 'neutral')
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🌸 Милая" + (" ✅" if current=='soft' else ""), callback_data="set_pers_soft"),
        InlineKeyboardButton("😐 Нейтральная" + (" ✅" if current=='neutral' else ""), callback_data="set_pers_neutral"),
        InlineKeyboardButton("🔥 Горячая" + (" ✅" if current=='hot' else ""), callback_data="set_pers_hot"),
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_settings")
    )
    text = f"🎭 **Выбор характера**\n\nТекущий: {get_personality_name(current)}"
    return markup, text

def limit_menu_keyboard(chat_id):
    current = get_user_setting(chat_id, 'limit', 400)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔹 100-200", callback_data="set_limit_150"),
        InlineKeyboardButton("🔸 400-600", callback_data="set_limit_500"),
        InlineKeyboardButton("🔹 800-1000", callback_data="set_limit_900"),
        InlineKeyboardButton("✏️ Свой", callback_data="custom_limit"),
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_settings")
    )
    text = f"📏 **Лимит токенов**\n\nТекущий: {current}"
    return markup, text

def history_menu_keyboard(chat_id):
    history_count = len(user_history.get(chat_id, [])) // 2
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📄 Показать историю", callback_data="show_history"),
        InlineKeyboardButton("🗑️ Очистить историю", callback_data="clear_history"),
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_settings")
    )
    text = f"📊 **История**\n\nВсего диалогов: {history_count}"
    return markup, text
