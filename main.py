import telebot
from openai import OpenAI
from telebot.types import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

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

# -------------------- Вспомогательные словари --------------------
# Храним message_id последнего запроса на ввод для каждого чата
last_query_message = {}

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

# -------------------- Обработчик текстового ввода (поля) --------------------
def process_field_input(message, field_name):
    cid = message.chat.id
    text = message.text.strip()
    if text:
        if field_name != 'gender':
            text = replace_pronouns(text)
        update_field(cid, field_name, text)
        bot.send_message(cid, f"✅ Поле '{field_name}' обновлено.", reply_markup=kb.reply_main_keyboard())
    else:
        bot.send_message(cid, "❌ Пустое значение не принимается.", reply_markup=kb.reply_main_keyboard())

    # Удаляем сообщение с запросом, если оно сохранено
    if cid in last_query_message:
        try:
            bot.delete_message(cid, last_query_message[cid])
        except:
            pass
        del last_query_message[cid]

    # Возвращаем меню карточки
    markup, txt = kb.character_menu_keyboard(cid)
    sent = bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=markup)
    menu_message_id[cid] = sent.message_id

# -------------------- Обработчик отмены ввода --------------------
def cancel_input(call):
    cid = call.message.chat.id
    if cid in last_query_message:
        try:
            bot.delete_message(cid, last_query_message[cid])
        except:
            pass
        del last_query_message[cid]
    # Возвращаем меню карточки
    markup, txt = kb.character_menu_keyboard(cid)
    sent = bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=markup)
    menu_message_id[cid] = sent.message_id
    bot.answer_callback_query(call.id, "❌ Ввод отменён")

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
        "3. Для фото пришли картинку (бот сохранит её).\n"
        "4. После заполнения нажми «🚀 Запустить» – бот отправит фото персонажа и приветствие.\n"
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
        bot.delete_message(cid, message.message_id)  # удаляем сообщение с текстом кнопки
    except:
        pass

    if text == "🎮 НАЧАТЬ":
        bot.send_message(cid, "🚀 Погнали!", reply_markup=kb.reply_main_keyboard())
        sent = bot.send_message(cid, "🎮 Главное меню", reply_markup=kb.main_menu_keyboard())
        menu_message_id[cid] = sent.message_id

    elif text == "👤 Создать персонажа":
        markup, txt = kb.character_menu_keyboard(cid)
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
            "• «👤 Создать персонажа» – заполни карточку своего героя.\n"
            "• «⚙️ Лимит» – настрой длину ответов.\n"
            "• «ℹ️ О боте» – подробная инструкция.\n"
            "• «🚀 Запустить» – применить карточку (бот покажет фото и поздоровается).",
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
            "4. После заполнения нажми «🚀 Запустить» – бот покажет фото персонажа и отправит приветствие.\n"
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

    # Меняем имя бота
    try:
        bot.set_my_name(name)
        bot.send_message(cid, f"✅ Имя бота изменено на {name}", reply_markup=kb.reply_main_keyboard())
    except Exception as e:
        bot.send_message(cid, f"❌ Ошибка смены имени: {e}", reply_markup=kb.reply_main_keyboard())

    # Меняем описание
    if subtitles:
        try:
            bot.set_my_description(subtitles)
            bot.send_message(cid, "✅ Описание бота обновлено", reply_markup=kb.reply_main_keyboard())
        except Exception as e:
            bot.send_message(cid, f"❌ Ошибка описания: {e}", reply_markup=kb.reply_main_keyboard())

    # Отправляем фото персонажа (один раз)
    photo_file_id = get_field(cid, 'char_photo')
    if photo_file_id:
        try:
            bot.send_photo(cid, photo_file_id, caption=f"📸 **{name}**", parse_mode="Markdown")
        except Exception as e:
            bot.send_message(cid, f"❌ Не удалось отправить фото: {e}", reply_markup=kb.reply_main_keyboard())
    else:
        bot.send_message(cid, "⚠️ Фото не задано, пропускаю.", reply_markup=kb.reply_main_keyboard())

    clear_history(cid)
    bot.send_message(cid, "🧹 История диалога очищена.", reply_markup=kb.reply_main_keyboard())

    # Отправляем приветствие
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
        markup, txt = kb.character_menu_keyboard(cid)
        bot.edit_message_text(txt, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)

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
                InlineKeyboardButton("◀️ Отмена", callback_data="cancel_input")
            )
            bot.edit_message_text("👫 Выбери пол персонажа:", cid, call.message.message_id, reply_markup=gender_markup)
            bot.answer_callback_query(call.id)
            return
        elif field == "photo":
            msg = bot.send_message(cid, "🖼 Отправь фотографию персонажа (только картинка).", reply_markup=ReplyKeyboardRemove())
            bot.register_next_step_handler(msg, process_photo_input)
            bot.answer_callback_query(call.id)
            return
        else:
            instruction = get_instruction(field)
            # Создаём клавиатуру с кнопкой "Отмена"
            cancel_markup = InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Отмена", callback_data="cancel_input"))
            msg = bot.send_message(cid, instruction, reply_markup=cancel_markup)
            # Сохраняем message_id этого сообщения
            last_query_message[cid] = msg.message_id
            bot.register_next_step_handler(msg, process_field_input, field)
            bot.answer_callback_query(call.id)

    elif data == "cancel_input":
        cancel_input(call)

    elif data == "back_to_character":
        markup, txt = kb.character_menu_keyboard(cid)
        bot.edit_message_text(txt, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)

    elif data == "set_gender_male":
        update_field(cid, 'gender', 'male')
        bot.answer_callback_query(call.id, "✅ Пол: Мужской")
        markup, txt = kb.character_menu_keyboard(cid)
        bot.edit_message_text(txt, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif data == "set_gender_female":
        update_field(cid, 'gender', 'female')
        bot.answer_callback_query(call.id, "✅ Пол: Женский")
        markup, txt = kb.character_menu_keyboard(cid)
        bot.edit_message_text(txt, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif data == "reset_card":
        reset_all(cid)
        bot.answer_callback_query(call.id, "♻️ Карточка сброшена")
        markup, txt = kb.character_menu_keyboard(cid)
        bot.edit_message_text(txt, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

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

# -------------------- Обработка ввода своего лимита --------------------
def process_custom_limit(message, menu_msg_id):
    cid = message.chat.id
    try:
        limit = max(10, min(1500, int(message.text)))
        update_field(cid, 'limit', limit)
        bot.send_message(cid, f"✅ Лимит: {limit}", reply_markup=kb.reply_main_keyboard())
    except:
        bot.send_message(cid, "❌ Нужно число от 10 до 1500.", reply_markup=kb.reply_main_keyboard())
    try:
        markup, txt = kb.limit_menu_keyboard(cid)
        bot.edit_message_text(txt, cid, menu_msg_id, parse_mode="Markdown", reply_markup=markup)
    except:
        sent = bot.send_message(cid, "📏 Лимит", reply_markup=markup)
        menu_message_id[cid] = sent.message_id

# -------------------- Обработка загрузки фото --------------------
def process_photo_input(message):
    cid = message.chat.id
    if message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        update_field(cid, 'char_photo', file_id)
        bot.send_message(cid, "✅ Фото сохранено!", reply_markup=kb.reply_main_keyboard())
        # Удаляем сообщение с запросом, если оно есть
        if cid in last_query_message:
            try:
                bot.delete_message(cid, last_query_message[cid])
            except:
                pass
            del last_query_message[cid]
        # Возвращаем меню карточки
        markup, txt = kb.character_menu_keyboard(cid)
        sent = bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=markup)
        menu_message_id[cid] = sent.message_id
    else:
        bot.send_message(cid, "❌ Бро, пришли именно картинку, а не текст!", reply_markup=kb.reply_main_keyboard())
        # Снова запрашиваем фото
        msg = bot.send_message(cid, "🖼 Отправь фотографию персонажа (только картинка).", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_photo_input)

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
from telebot.types import WebAppInfo

@bot.message_handler(commands=['app'])
def open_mini_app(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        return
    # URL для Mini App: используем домен Render или localhost для теста
    if os.getenv('RENDER_EXTERNAL_HOSTNAME'):
        base_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}"
    else:
        base_url = f"http://localhost:{config.PORT}"  # для локального теста
    webapp_url = f"{base_url}/app"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🚀 Открыть конструктор", web_app=WebAppInfo(url=webapp_url)))
    
    bot.send_message(
        message.chat.id,
        "Нажми кнопку ниже, чтобы открыть конструктор персонажа:",
        reply_markup=markup
    )
# -------------------- Запуск --------------------
if __name__ == "__main__":
    print("🚀 Бот с улучшенным интерфейсом запущен!")
    bot.polling(none_stop=True)
