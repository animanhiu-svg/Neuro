import telebot
from openai import OpenAI
from telebot.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
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
    if not text:
        return text
    text = text.replace("Я ", "Ты ").replace(" я ", " ты ")
    if text.startswith("Я"):
        text = "Ты" + text[1:]
    return text

def get_instruction(field):
    instructions = {
        'name': "👤 Имя: Как зовут твоего персонажа?",
        'gender': "👫 Пол: Выбери пол персонажа (кнопками ниже).",
        'subtitles': "📝 Описание: Опиши персонажа (внешность, характер, цели).",
        'greeting': "👋 Приветствие: Напиши фразу, которую бот скажет при старте.",
        'memory_cards': "🧠 Память: Важные факты, которые персонаж всегда должен помнить.",
        'location': "📍 Локация: Где сейчас находится персонаж?",
        'scenario': "🎬 Сюжет: С чего начинается ваша встреча? Опиши ситуацию.",
        'relation': "👥 Твоя роль: Кем ты приходишься этому персонажу? (друг, враг, случайный прохожий...)"
    }
    return instructions.get(field, f"✏️ Введите значение для поля '{field}':")

def return_to_character_menu(chat_id, message_id_to_delete=None):
    """Возвращает пользователя в меню карточки, удаляя предыдущее сообщение."""
    if message_id_to_delete:
        try:
            bot.delete_message(chat_id, message_id_to_delete)
        except:
            pass
    markup, txt = kb.character_menu_keyboard(chat_id)
    sent = bot.send_message(chat_id, txt, parse_mode="Markdown", reply_markup=markup)
    menu_message_id[chat_id] = sent.message_id
    # Возвращаем Reply-клавиатуру
    bot.send_message(chat_id, "👤 Меню:", reply_markup=kb.reply_main_keyboard())

def process_field_input(message, field_name, prompt_msg_id):
    """Обработчик текстовых полей (кроме фото и пола)."""
    cid = message.chat.id
    text = message.text.strip()
    # Удаляем сообщение с запросом и сообщение пользователя
    try:
        bot.delete_message(cid, prompt_msg_id)
        bot.delete_message(cid, message.message_id)
    except:
        pass
    if text:
        if field_name != 'gender':
            text = replace_pronouns(text)
        update_field(cid, field_name, text)
        bot.send_message(cid, f"✅ Поле '{field_name}' обновлено.", reply_markup=kb.reply_main_keyboard())
    else:
        bot.send_message(cid, "❌ Пустое значение не принимается.", reply_markup=kb.reply_main_keyboard())
    return_to_character_menu(cid, None)

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
    welcome_text = (
        "👋 Привет! Это конструктор твоего идеального персонажа (вайфу, мужа, кого захочешь).\n\n"
        "📝 **Как пользоваться:**\n"
        "1. Нажми «👤 Создать персонажа» и заполни карточку.\n"
        "2. Для пола нажми на кнопку и выбери из вариантов.\n"
        "3. Для фото пришли картинку (бот сам её сохранит).\n"
        "4. После заполнения нажми «🚀 Запустить» – бот применит карточку.\n"
        "5. Дальше просто общайся – персонаж будет вести себя согласно роли.\n\n"
        "Готов? Жми кнопку внизу!"
    )
    bot.send_message(cid, welcome_text, parse_mode="Markdown", reply_markup=kb.reply_start_keyboard())

# -------------------- Обработчик Reply-кнопок --------------------
@bot.message_handler(func=lambda m: m.text in ["🎮 НАЧАТЬ", "👤 Создать персонажа", "⚙️ Лимит", "❓ Помощь", "ℹ️ О боте", "🚀 Запустить"])
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
        sent = bot.send_message(cid, "🎮 Главное меню", reply_markup=kb.main_menu_keyboard())
        menu_message_id[cid] = sent.message_id

    elif text == "👤 Создать персонажа":
        return_to_character_menu(cid, None)

    elif text == "⚙️ Лимит":
        markup, txt = kb.limit_menu_keyboard(cid)
        sent = bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=markup)
        menu_message_id[cid] = sent.message_id

    elif text == "❓ Помощь":
        sent = bot.send_message(
            cid,
            "❓ **Помощь**\n\n"
            "• «👤 Создать персонажа» – заполни карточку своего героя.\n"
            "• «⚙️ Лимит» – настрой длину ответов.\n"
            "• «ℹ️ О боте» – подробная инструкция.\n"
            "• «🚀 Запустить» – применить карточку.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
        )
        menu_message_id[cid] = sent.message_id

    elif text == "ℹ️ О боте":
        about_text = (
            "ℹ️ **О боте**\n\n"
            "Этот бот – твой личный конструктор персонажей.\n\n"
            "**Инструкция:**\n"
            "1. Нажми «👤 Создать персонажа».\n"
            "2. Заполни поля (имя, пол и приветствие обязательны).\n"
            "3. Для фото нажми «🖼 Фото» и отправь картинку.\n"
            "4. После заполнения нажми «🚀 Запустить» – бот применит карточку.\n"
            "5. Теперь просто общайся – персонаж будет вести себя согласно роли.\n\n"
            "**Важно:** Во всех полях «Я» автоматически заменяется на «Ты»."
        )
        sent = bot.send_message(
            cid,
            about_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
        )
        menu_message_id[cid] = sent.message_id

    elif text == "🚀 Запустить":
        required = ['name', 'gender', 'greeting']
        missing = [f for f in required if not get_field(cid, f)]
        if missing:
            bot.send_message(cid, f"❌ Сначала заполни обязательные поля: {', '.join(missing)}", reply_markup=kb.reply_main_keyboard())
            return
        run_metamorphosis(cid)

def run_metamorphosis(cid):
    name = get_field(cid, 'name')
    gender = get_field(cid, 'gender')
    greeting = get_field(cid, 'greeting')
    subtitles = get_field(cid, 'subtitles', '')

    try:
        bot.set_my_name(name)
        bot.send_message(cid, f"✅ Имя бота изменено на {name}", reply_markup=kb.reply_main_keyboard())
    except Exception as e:
        bot.send_message(cid, f"❌ Ошибка смены имени: {e}", reply_markup=kb.reply_main_keyboard())

    if subtitles:
        try:
            bot.set_my_description(subtitles)
            bot.send_message(cid, "✅ Описание бота обновлено", reply_markup=kb.reply_main_keyboard())
        except Exception as e:
            bot.send_message(cid, f"❌ Ошибка описания: {e}", reply_markup=kb.reply_main_keyboard())

    # Фото больше не меняем, а будем присылать в чат при старте (добавим позже)
    clear_history(cid)
    bot.send_message(cid, "🧹 История диалога очищена.", reply_markup=kb.reply_main_keyboard())

    bot.send_message(cid, f"**{greeting}**", parse_mode="Markdown", reply_markup=kb.reply_main_keyboard())

    sent = bot.send_message(cid, "🎮 Главное меню", reply_markup=kb.main_menu_keyboard())
    menu_message_id[cid] = sent.message_id

# -------------------- Обработчик Inline-колбэков --------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.message.chat.id != config.ALLOWED_USER_ID:
        bot.answer_callback_query(call.id, "⛔ Доступ запрещён", show_alert=True)
        return
    cid, data = call.message.chat.id, call.data

    if data == "close_menu":
        try:
            bot.delete_message(cid, call.message.message_id)
        except:
            pass
        menu_message_id.pop(cid, None)
        bot.answer_callback_query(call.id)

    elif data == "back_to_main":
        bot.edit_message_text("🎮 Главное меню", cid, call.message.message_id, reply_markup=kb.main_menu_keyboard())
        bot.answer_callback_query(call.id)

    elif data == "main_character":
        return_to_character_menu(cid, call.message.message_id)

    elif data == "main_limit":
        markup, txt = kb.limit_menu_keyboard(cid)
        bot.edit_message_text(txt, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)

    elif data == "main_help":
        bot.answer_callback_query(call.id, "❓ Используй кнопки внизу.", show_alert=True)
    elif data == "main_about":
        bot.answer_callback_query(call.id, "ℹ️ Подробная инструкция в разделе «О боте».", show_alert=True)

    # --- Редактирование полей ---
    elif data.startswith("edit_"):
        field = data[5:]
        if field == "gender":
            gender_markup = InlineKeyboardMarkup(row_width=2)
            gender_markup.add(
                InlineKeyboardButton("👨 Мужской", callback_data="set_gender_male"),
                InlineKeyboardButton("👩 Женский", callback_data="set_gender_female"),
                InlineKeyboardButton("🔙 Назад", callback_data="back_to_character")
            )
            bot.edit_message_text("👫 Выбери пол персонажа:", cid, call.message.message_id, reply_markup=gender_markup)
            bot.answer_callback_query(call.id)
            return
        elif field == "photo":
            # Запрос фото с кнопкой отмены
            cancel_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Отмена", callback_data="cancel_photo"))
            msg = bot.send_message(cid, "🖼 Отправь фотографию персонажа (только картинка).", reply_markup=cancel_markup)
            bot.register_next_step_handler(msg, process_photo_input, call.message.message_id, msg.message_id)
            bot.answer_callback_query(call.id)
            return
        else:
            # Текстовые поля – добавляем кнопку отмены
            cancel_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Отмена", callback_data="cancel_input"))
            instruction = get_instruction(field)
            msg = bot.send_message(cid, instruction, reply_markup=cancel_markup)
            bot.register_next_step_handler(msg, process_field_input, field, msg.message_id)
            bot.answer_callback_query(call.id)

    elif data == "cancel_input":
        # Отмена ввода текстового поля
        bot.delete_message(cid, call.message.message_id)
        return_to_character_menu(cid, None)
        bot.answer_callback_query(call.id)

    elif data == "cancel_photo":
        # Отмена загрузки фото
        bot.delete_message(cid, call.message.message_id)
        return_to_character_menu(cid, None)
        bot.answer_callback_query(call.id)

    elif data == "back_to_character":
        return_to_character_menu(cid, call.message.message_id)
        bot.answer_callback_query(call.id)

    elif data == "set_gender_male":
        update_field(cid, 'gender', 'male')
        bot.answer_callback_query(call.id, "✅ Пол: Мужской")
        return_to_character_menu(cid, call.message.message_id)

    elif data == "set_gender_female":
        update_field(cid, 'gender', 'female')
        bot.answer_callback_query(call.id, "✅ Пол: Женский")
        return_to_character_menu(cid, call.message.message_id)

    elif data == "reset_card":
        reset_all(cid)
        bot.answer_callback_query(call.id, "♻️ Карточка сброшена")
        return_to_character_menu(cid, call.message.message_id)

    elif data.startswith("set_limit_"):
        limits = {"set_limit_150":150, "set_limit_500":500, "set_limit_900":900}
        limit = limits.get(data, 400)
        update_field(cid, 'limit', limit)
        bot.answer_callback_query(call.id, f"✅ Лимит: {limit}")
        markup, txt = kb.limit_menu_keyboard(cid)
        bot.edit_message_text(txt, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif data == "custom_limit":
        # Запрос лимита с кнопкой отмены
        cancel_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Отмена", callback_data="cancel_limit"))
        msg = bot.send_message(cid, "✏️ Введи число токенов (10-1500):", reply_markup=cancel_markup)
        bot.register_next_step_handler(msg, process_custom_limit, call.message.message_id, msg.message_id)
        bot.answer_callback_query(call.id)

    elif data == "cancel_limit":
        bot.delete_message(cid, call.message.message_id)
        # Возвращаемся в меню лимита
        markup, txt = kb.limit_menu_keyboard(cid)
        bot.edit_message_text(txt, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)

# -------------------- Обработка ввода своего лимита --------------------
def process_custom_limit(message, menu_msg_id, prompt_msg_id):
    cid = message.chat.id
    try:
        limit = max(10, min(1500, int(message.text)))
        update_field(cid, 'limit', limit)
        bot.send_message(cid, f"✅ Лимит: {limit}", reply_markup=kb.reply_main_keyboard())
    except:
        bot.send_message(cid, "❌ Нужно число от 10 до 1500.", reply_markup=kb.reply_main_keyboard())
    # Удаляем сообщение с запросом и сообщение пользователя
    try:
        bot.delete_message(cid, prompt_msg_id)
        bot.delete_message(cid, message.message_id)
    except:
        pass
    # Возвращаемся в меню лимита
    markup, txt = kb.limit_menu_keyboard(cid)
    try:
        bot.edit_message_text(txt, cid, menu_msg_id, parse_mode="Markdown", reply_markup=markup)
    except:
        sent = bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=markup)
        menu_message_id[cid] = sent.message_id

# -------------------- Обработка загрузки фото --------------------
def process_photo_input(message, menu_msg_id, prompt_msg_id):
    cid = message.chat.id
    # Удаляем сообщение с запросом и сообщение пользователя
    try:
        bot.delete_message(cid, prompt_msg_id)
    except:
        pass
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        update_field(cid, 'char_photo', file_id)
        bot.send_message(cid, "✅ Фото сохранено!", reply_markup=kb.reply_main_keyboard())
        try:
            bot.delete_message(cid, message.message_id)
        except:
            pass
        return_to_character_menu(cid, None)
    else:
        bot.send_message(cid, "❌ Бро, пришли именно картинку, а не текст!", reply_markup=kb.reply_main_keyboard())
        # Повторяем запрос с кнопкой отмены
        cancel_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🔙 Отмена", callback_data="cancel_photo"))
        msg = bot.send_message(cid, "🖼 Отправь фотографию персонажа (только картинка).", reply_markup=cancel_markup)
        bot.register_next_step_handler(msg, process_photo_input, menu_msg_id, msg.message_id)

# -------------------- Основной обработчик RP-сообщений --------------------
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/') and m.text not in ["🎮 НАЧАТЬ", "👤 Создать персонажа", "⚙️ Лимит", "❓ Помощь", "ℹ️ О боте", "🚀 Запустить"])
def handle_rp(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        return
    cid = message.chat.id
    if contains_forbidden(message.text):
        bot.reply_to(message, "⛔ Запрещённая тема.", reply_markup=kb.reply_main_keyboard())
        return
    if cid not in user_settings:
        init_user(cid)
    bot.send_chat_action(cid, 'typing')
    reply = query_dolphin(message.text, cid, client)
    bot.send_message(cid, reply, reply_markup=kb.reply_main_keyboard())

# -------------------- Запуск --------------------
if __name__ == "__main__":
    print("🚀 Бот с улучшенным интерфейсом запущен!")
    bot.polling(none_stop=True)
