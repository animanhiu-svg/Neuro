import telebot
from openai import OpenAI
from telebot.types import ReplyKeyboardRemove
import requests

import config
import utils
import keyboards as kb
from database import (
    user_settings, user_history, menu_message_id,
    init_user, update_field, get_field, reset_all,
    clear_history, add_to_history
)
from logic import contains_forbidden, query_dolphin

utils.start_pinger()

client = OpenAI(base_url=config.BASE_URL, api_key=config.HF_TOKEN)
bot = telebot.TeleBot(config.TG_TOKEN)

# -------------------- Утилиты --------------------
def replace_pronouns(text):
    """Заменяет 'Я' на 'Ты' в начале предложений и отдельно стоящее."""
    if not text:
        return text
    # Заменяем "Я " на "Ты " и " я " на " ты "
    text = text.replace("Я ", "Ты ").replace(" я ", " ты ")
    # Если текст начинается с "Я", заменяем
    if text.startswith("Я"):
        text = "Ты" + text[1:]
    return text

def process_field_input(message, field_name, next_step=None):
    """Общий обработчик для ввода любого поля."""
    cid = message.chat.id
    text = message.text.strip()
    if text:
        # Автозамена
        if field_name not in ['gender']:  # пол не заменяем
            text = replace_pronouns(text)
        update_field(cid, field_name, text)
        bot.send_message(cid, f"✅ Поле '{field_name}' обновлено.")
    else:
        bot.send_message(cid, "❌ Пустое значение не принимается.")
    # Возвращаемся в меню конструктора
    markup, txt = kb.constructor_menu_keyboard(cid)
    sent = bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=markup)
    menu_message_id[cid] = sent.message_id

# -------------------- Команды --------------------
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ Только для владельца.")
        return
    cid = message.chat.id
    init_user(cid)
    if cid in menu_message_id:
        try:
            bot.delete_message(cid, menu_message_id.pop(cid))
        except:
            pass
    bot.send_message(
        cid,
        f"👋 Привет, {message.from_user.first_name}!\nЯ — конструктор персонажей. Готов создать клона?",
        reply_markup=kb.reply_start_keyboard()
    )

# -------------------- Обработчик Reply-кнопок --------------------
@bot.message_handler(func=lambda m: m.text in ["🎮 НАЧАТЬ", "🎴 Конструктор", "⚙️ Лимит", "❓ Помощь", "ℹ️ О боте", "🚀 Запустить"])
def handle_reply_buttons(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        return
    cid, text = message.chat.id, message.text
    try:
        bot.delete_message(cid, message.message_id)
    except:
        pass

    if text == "🎮 НАЧАТЬ":
        bot.send_message(cid, "🚀 Погнали!", reply_markup=kb.reply_main_keyboard())
        # Показываем главное Inline-меню
        sent = bot.send_message(cid, "🎮 Главное меню", reply_markup=kb.main_menu_keyboard())
        menu_message_id[cid] = sent.message_id

    elif text == "🎴 Конструктор":
        markup, txt = kb.constructor_menu_keyboard(cid)
        sent = bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=markup)
        menu_message_id[cid] = sent.message_id

    elif text == "⚙️ Лимит":
        markup, txt = kb.limit_menu_keyboard(cid)
        sent = bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=markup)
        menu_message_id[cid] = sent.message_id

    elif text == "❓ Помощь":
        sent = bot.send_message(
            cid,
            "❓ **Помощь**\n\n"
            "• Конструктор — создай карточку персонажа.\n"
            "• Заполни все поля, затем нажми «Запустить».\n"
            "• Бот сменит имя, описание и фото, начнёт диалог с приветствия.",
            parse_mode="Markdown",
            reply_markup=kb.InlineKeyboardMarkup().add(kb.InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
        )
        menu_message_id[cid] = sent.message_id

    elif text == "ℹ️ О боте":
        sent = bot.send_message(
            cid,
            "ℹ️ **О боте**\nВерсия 8.0 (Конструктор клонов)\nМодель: Dolphin-Mistral-24B",
            parse_mode="Markdown",
            reply_markup=kb.InlineKeyboardMarkup().add(kb.InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
        )
        menu_message_id[cid] = sent.message_id

    elif text == "🚀 Запустить":
        # Проверка заполненности обязательных полей
        required = ['name', 'gender', 'greeting']
        missing = [f for f in required if not get_field(cid, f)]
        if missing:
            bot.send_message(cid, f"❌ Сначала заполни: {', '.join(missing)}")
            return
        # Запуск перевоплощения
        run_metamorphosis(cid)

def run_metamorphosis(cid):
    name = get_field(cid, 'name')
    gender = get_field(cid, 'gender')
    greeting = get_field(cid, 'greeting')
    subtitles = get_field(cid, 'subtitles', '')

    # 1. Меняем имя бота
    try:
        bot.set_my_name(name)
        bot.send_message(cid, f"✅ Имя бота изменено на {name}")
    except Exception as e:
        bot.send_message(cid, f"❌ Ошибка смены имени: {e}")

    # 2. Меняем описание (subtitles) — "о боте"
    if subtitles:
        try:
            bot.set_my_description(subtitles)
            bot.send_message(cid, "✅ Описание бота обновлено")
        except Exception as e:
            bot.send_message(cid, f"❌ Ошибка описания: {e}")

    # 3. Меняем аватарку
    photo_file_id = get_field(cid, 'char_photo')
    if photo_file_id:
        try:
            file_info = bot.get_file(photo_file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open('temp_avatar.jpg', 'wb') as f:
                f.write(downloaded_file)
            with open('temp_avatar.jpg', 'rb') as f:
                bot.set_my_profile_photo(f)
            bot.send_message(cid, "✅ Аватарка обновлена")
        except Exception as e:
            bot.send_message(cid, f"❌ Ошибка смены фото: {e}")
    else:
        bot.send_message(cid, "⚠️ Фото не задано, пропускаю.")

    # 4. Очищаем историю диалога
    clear_history(cid)
    bot.send_message(cid, "🧹 История диалога очищена.")

    # 5. Отправляем приветствие от лица персонажа
    bot.send_message(cid, f"**{greeting}**", parse_mode="Markdown")

    # Возвращаем главное меню
    sent = bot.send_message(cid, "🎮 Главное меню", reply_markup=kb.main_menu_keyboard())
    menu_message_id[cid] = sent.message_id

# -------------------- Обработчик Inline-колбэков --------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.message.chat.id != config.ALLOWED_USER_ID:
        bot.answer_callback_query(call.id, "⛔ Доступ запрещён", show_alert=True)
        return
    cid, data = call.message.chat.id, call.data

    # Закрыть меню
    if data == "close_menu":
        try:
            bot.delete_message(cid, call.message.message_id)
        except:
            pass
        menu_message_id.pop(cid, None)
        bot.answer_callback_query(call.id)

    # Назад в главное меню
    elif data == "back_to_main":
        bot.edit_message_text("🎮 Главное меню", cid, call.message.message_id, reply_markup=kb.main_menu_keyboard())
        bot.answer_callback_query(call.id)

    # Главное меню: конструктор
    elif data == "main_constructor":
        markup, txt = kb.constructor_menu_keyboard(cid)
        bot.edit_message_text(txt, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)

    # Главное меню: лимит
    elif data == "main_limit":
        markup, txt = kb.limit_menu_keyboard(cid)
        bot.edit_message_text(txt, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)

    # Главное меню: помощь/о боте (alert)
    elif data == "main_help":
        bot.answer_callback_query(call.id, "❓ Используй конструктор для создания персонажа", show_alert=True)
    elif data == "main_about":
        bot.answer_callback_query(call.id, "ℹ️ Версия 8.0 — Конструктор клонов", show_alert=True)

    # Обработчики редактирования полей конструктора
    elif data.startswith("edit_"):
        field_map = {
            "edit_name": "name", "edit_gender": "gender", "edit_subtitles": "subtitles",
            "edit_greeting": "greeting", "edit_memory": "memory_cards", "edit_photo": "char_photo",
            "edit_location": "location", "edit_scenario": "scenario", "edit_relation": "relation"
        }
        field = field_map.get(data)
        if field:
            msg = bot.send_message(cid, f"✏️ Введите новое значение для поля '{field}':", reply_markup=ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, process_field_input, field, call.message.message_id)
            bot.answer_callback_query(call.id)

    # Сброс карточки
    elif data == "reset_card":
        reset_all(cid)
        bot.answer_callback_query(call.id, "♻️ Карточка сброшена")
        markup, txt = kb.constructor_menu_keyboard(cid)
        bot.edit_message_text(txt, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    # Установка лимита
    elif data.startswith("set_limit_"):
        limits = {"set_limit_150":150, "set_limit_500":500, "set_limit_900":900}
        limit = limits.get(data, 400)
        update_field(cid, 'limit', limit)
        bot.answer_callback_query(call.id, f"✅ Лимит: {limit}")
        markup, txt = kb.limit_menu_keyboard(cid)
        bot.edit_message_text(txt, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif data == "custom_limit":
        msg = bot.send_message(cid, "✏️ Введи число токенов (10-1500):", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_custom_limit, call.message.message_id)
        bot.answer_callback_query(call.id)

# -------------------- Обработка ввода лимита --------------------
def process_custom_limit(message, menu_msg_id):
    cid = message.chat.id
    try:
        limit = max(10, min(1500, int(message.text)))
        update_field(cid, 'limit', limit)
        bot.send_message(cid, f"✅ Лимит: {limit}")
    except:
        bot.send_message(cid, "❌ Нужно число от 10 до 1500.")
    try:
        markup, txt = kb.limit_menu_keyboard(cid)
        bot.edit_message_text(txt, cid, menu_msg_id, parse_mode="Markdown", reply_markup=markup)
    except:
        sent = bot.send_message(cid, "📏 Лимит", reply_markup=kb.limit_menu_keyboard(cid)[0])
        menu_message_id[cid] = sent.message_id

# -------------------- Основной обработчик RP-сообщений --------------------
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/') and m.text not in ["🎮 НАЧАТЬ", "🎴 Конструктор", "⚙️ Лимит", "❓ Помощь", "ℹ️ О боте", "🚀 Запустить"])
def handle_rp(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        return
    cid = message.chat.id
    if contains_forbidden(message.text):
        bot.reply_to(message, "⛔ Запрещённая тема.")
        return
    if cid not in user_settings:
        init_user(cid)
    bot.send_chat_action(cid, 'typing')
    reply = query_dolphin(message.text, cid, client)
    bot.send_message(cid, reply)

# -------------------- Запуск --------------------
if __name__ == "__main__":
    print("🚀 Конструктор клонов запущен!")
    bot.polling(none_stop=True)
