from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database import get_field

def reply_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("👤 Создать персонажа"),
        KeyboardButton("⚙️ Лимит"),
        KeyboardButton("❓ Помощь"),
        KeyboardButton("ℹ️ О боте"),
        KeyboardButton("🚀 Запустить")
    )
    return markup

def reply_start_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("🎮 НАЧАТЬ"))
    return markup

def character_menu_keyboard(chat_id):
    markup = InlineKeyboardMarkup(row_width=2)

    def status(field):
        return "✅" if get_field(chat_id, field) else "❌"

    markup.add(
        InlineKeyboardButton(f"👤 Имя {status('name')}", callback_data="edit_name"),
        InlineKeyboardButton(f"👫 Пол {status('gender')}", callback_data="edit_gender"),
        InlineKeyboardButton(f"📝 Описание {status('subtitles')}", callback_data="edit_subtitles"),
        InlineKeyboardButton(f"👋 Приветствие {status('greeting')}", callback_data="edit_greeting"),
        InlineKeyboardButton(f"🧠 Память {status('memory_cards')}", callback_data="edit_memory"),
        InlineKeyboardButton(f"🖼 Фото {status('char_photo')}", callback_data="edit_photo"),
        InlineKeyboardButton(f"📍 Локация {status('location')}", callback_data="edit_location"),
        InlineKeyboardButton(f"🎬 Сюжет {status('scenario')}", callback_data="edit_scenario"),
        InlineKeyboardButton(f"👥 Твоя роль {status('relation')}", callback_data="edit_relation"),
        InlineKeyboardButton("♻️ Сбросить всё", callback_data="reset_card"),
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")
    )
    return markup, "👤 **Создать персонажа**\nЗаполни поля ниже:"

def limit_menu_keyboard(chat_id):
    current = get_field(chat_id, 'limit', 400)
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔹 100-200", callback_data="set_limit_150"),
        InlineKeyboardButton("🔸 400-600", callback_data="set_limit_500"),
        InlineKeyboardButton("🔹 800-1000", callback_data="set_limit_900"),
        InlineKeyboardButton("✏️ Свой", callback_data="custom_limit"),
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")
    )
    text = f"📏 **Лимит токенов**\nТекущий: {current}"
    return markup, text

def main_menu_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("👤 Создать персонажа", callback_data="main_character"),
        InlineKeyboardButton("⚙️ Лимит", callback_data="main_limit"),
        InlineKeyboardButton("❓ Помощь", callback_data="main_help"),
        InlineKeyboardButton("ℹ️ О боте", callback_data="main_about"),
        InlineKeyboardButton("❌ Закрыть", callback_data="close_menu")
    )
    return markup
