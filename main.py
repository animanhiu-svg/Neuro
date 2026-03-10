import telebot
from openai import OpenAI
from telebot.types import ReplyKeyboardRemove

import config
import utils
import keyboards as kb
from database import user_settings, user_history, menu_message_id, reset_all, update_user_setting, clear_history
from logic import contains_forbidden, query_dolphin, get_personality_name

utils.start_pinger()

client = OpenAI(base_url=config.BASE_URL, api_key=config.HF_TOKEN)
bot = telebot.TeleBot(config.TG_TOKEN)

# -------------------- КОМАНДЫ --------------------
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ Этот бот только для владельца.")
        return
    cid = message.chat.id
    reset_all(cid)
    if cid in menu_message_id:
        try:
            bot.delete_message(cid, menu_message_id.pop(cid))
        except:
            pass
    bot.send_message(
        cid,
        f"👋 Привет, {message.from_user.first_name}!\nЯ — ролевой бот. Готов начать?",
        reply_markup=kb.reply_start_keyboard()
    )

# -------------------- ОБРАБОТЧИК REPLY-КНОПОК --------------------
@bot.message_handler(func=lambda m: m.text in [
    "🎮 НАЧАТЬ РОЛЕВУЮ ИГРУ",
    "⚙️ Настройки",
    "🎴 Мой персонаж",
    "❓ Помощь",
    "ℹ️ О боте",
    "🎮 Меню"
])
def handle_reply_buttons(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        return
    cid, text = message.chat.id, message.text
    try:
        bot.delete_message(cid, message.message_id)
    except:
        pass

    if text == "🎮 НАЧАТЬ РОЛЕВУЮ ИГРУ":
        bot.send_message(cid, "🚀 Погнали! Пиши с чего начнём.", reply_markup=kb.reply_main_keyboard())

    elif text == "❓ Помощь":
        sent = bot.send_message(
            cid,
            "❓ Кнопки внизу — меню. Настройки: лимит и характер. История 20 сообщений.",
            parse_mode="Markdown",
            reply_markup=kb.InlineKeyboardMarkup().add(kb.InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
        )
        menu_message_id[cid] = sent.message_id

    elif text == "ℹ️ О боте":
        sent = bot.send_message(
            cid,
            "ℹ️ Версия 8.0 (Character AI style). Dolphin-Mistral-24B, защита от запрещённых тем.",
            parse_mode="Markdown",
            reply_markup=kb.InlineKeyboardMarkup().add(kb.InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
        )
        menu_message_id[cid] = sent.message_id

    elif text == "⚙️ Настройки":
        markup, txt = kb.settings_main_keyboard(cid)
        sent = bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=markup)
        menu_message_id[cid] = sent.message_id

    elif text == "🎴 Мой персонаж":
        markup, txt = kb.character_card_keyboard(cid)
        sent = bot.send_message(cid, txt, parse_mode="Markdown", reply_markup=markup)
        menu_message_id[cid] = sent.message_id

    elif text == "🎮 Меню":
        if cid in menu_message_id:
            try:
                bot.delete_message(cid, menu_message_id.pop(cid))
            except:
                pass
        sent = bot.send_message(cid, "🎮 Главное меню", reply_markup=kb.main_menu_keyboard())
        menu_message_id[cid] = sent.message_id

# -------------------- ОБРАБОТЧИК INLINE-КОЛБЭКОВ --------------------
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

    # Назад в меню настроек
    elif data == "back_to_settings":
        markup, text = kb.settings_main_keyboard(cid)
        bot.edit_message_text(text, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)

    # Информационные разделы (alert)
    elif data in ["main_help", "main_about"]:
        texts = {
            "main_help": "❓ Используй кнопки внизу.",
            "main_about": "ℹ️ Бот на базе Dolphin-Mistral-24B с карточкой персонажа."
        }
        bot.answer_callback_query(call.id, texts[data], show_alert=True)

    # Вход в настройки
    elif data == "main_settings":
        markup, text = kb.settings_main_keyboard(cid)
        bot.edit_message_text(text, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)

    # Вход в меню персонажа
    elif data == "main_character":
        markup, text = kb.character_card_keyboard(cid)
        bot.edit_message_text(text, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)

    # Вход в подменю настроек
    elif data in ["settings_character", "settings_limit", "settings_history"]:
        funcs = {
            "settings_character": kb.character_menu_keyboard,
            "settings_limit": kb.limit_menu_keyboard,
            "settings_history": kb.history_menu_keyboard
        }
        markup, text = funcs[data](cid)
        bot.edit_message_text(text, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)

    # Выбор характера
    elif data.startswith("set_pers_"):
        pers = data.split("_")[2]
        update_user_setting(cid, 'personality', pers)
        bot.send_message(cid, f"🎭 **Характер изменён!**\n\nТеперь я **{get_personality_name(pers)}**!", parse_mode="Markdown")
        bot.answer_callback_query(call.id, f"✅ Характер: {get_personality_name(pers)}")
        markup, text = kb.character_menu_keyboard(cid)
        bot.edit_message_text(text, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    # Выбор лимита
    elif data.startswith("set_limit_"):
        limits = {"set_limit_150":150, "set_limit_500":500, "set_limit_900":900}
        limit = limits.get(data, 400)
        update_user_setting(cid, 'limit', limit)
        bot.answer_callback_query(call.id, f"✅ Лимит: {limit}")
        markup, text = kb.limit_menu_keyboard(cid)
        bot.edit_message_text(text, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    # Свой лимит
    elif data == "custom_limit":
        msg = bot.send_message(cid, "✏️ Введи число токенов (10-1500):", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_custom_limit, call.message.message_id)
        bot.answer_callback_query(call.id)

    # Показать историю
    elif data == "show_history":
        hc = len(user_history.get(cid, [])) // 2
        bot.answer_callback_query(call.id, f"В истории {hc} пар сообщений", show_alert=True)

    # Очистить историю
    elif data == "clear_history":
        clear_history(cid)
        bot.answer_callback_query(call.id, "🗑️ История очищена")
        markup, text = kb.history_menu_keyboard(cid)
        bot.edit_message_text(text, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    # Сбросить всё
    elif data == "reset_all":
        reset_all(cid)
        bot.answer_callback_query(call.id, "🔄 Настройки сброшены")
        markup, text = kb.settings_main_keyboard(cid)
        bot.edit_message_text(text, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    # --- ОБРАБОТЧИКИ ДЛЯ КАРТОЧКИ ПЕРСОНАЖА ---
    elif data == "char_edit_name":
        msg = bot.send_message(cid, "✏️ Введи **имя** персонажа:", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_char_name, call.message.message_id)

    elif data == "char_edit_desc":
        msg = bot.send_message(cid, "📝 Введи **описание** персонажа (характер, внешность, манера речи):", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_char_desc, call.message.message_id)

    elif data == "char_edit_scene":
        msg = bot.send_message(cid, "🎬 Введи **начальную ситуацию** (где мы находимся, что происходит):", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_char_scene, call.message.message_id)

    elif data == "char_reset":
        update_user_setting(cid, 'char_name', None)
        update_user_setting(cid, 'char_description', None)
        update_user_setting(cid, 'char_scenario', None)
        clear_history(cid)
        bot.answer_callback_query(call.id, "♻️ Карточка персонажа очищена")
        markup, text = kb.character_card_keyboard(cid)
        bot.edit_message_text(text, cid, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

# -------------------- ОБРАБОТЧИКИ ШАГОВ (ВВОД ПОЛЕЙ КАРТОЧКИ) --------------------
def process_char_name(message, menu_msg_id):
    cid = message.chat.id
    name = message.text.strip()
    if name:
        update_user_setting(cid, 'char_name', name)
        clear_history(cid)  # очищаем историю при смене персонажа
        bot.send_message(cid, f"✅ Имя сохранено: {name}")
    else:
        bot.send_message(cid, "❌ Имя не может быть пустым.")
    # Возвращаем меню персонажа
    try:
        markup, text = kb.character_card_keyboard(cid)
        bot.edit_message_text(text, cid, menu_msg_id, parse_mode="Markdown", reply_markup=markup)
    except:
        sent = bot.send_message(cid, "🎴 Мой персонаж", reply_markup=kb.character_card_keyboard(cid)[0])
        menu_message_id[cid] = sent.message_id

def process_char_desc(message, menu_msg_id):
    cid = message.chat.id
    desc = message.text.strip()
    if desc:
        # Автоматическая замена "Я" на "Ты"
        desc = desc.replace("Я ", "Ты ").replace("я ", "ты ")
        update_user_setting(cid, 'char_description', desc)
        clear_history(cid)
        bot.send_message(cid, f"✅ Описание сохранено: {desc[:50]}...")
    else:
        bot.send_message(cid, "❌ Описание не может быть пустым.")
    try:
        markup, text = kb.character_card_keyboard(cid)
        bot.edit_message_text(text, cid, menu_msg_id, parse_mode="Markdown", reply_markup=markup)
    except:
        sent = bot.send_message(cid, "🎴 Мой персонаж", reply_markup=kb.character_card_keyboard(cid)[0])
        menu_message_id[cid] = sent.message_id

def process_char_scene(message, menu_msg_id):
    cid = message.chat.id
    scene = message.text.strip()
    if scene:
        # Автозамена "Я" на "Ты" (на всякий случай)
        scene = scene.replace("Я ", "Ты ").replace("я ", "ты ")
        update_user_setting(cid, 'char_scenario', scene)
        clear_history(cid)
        bot.send_message(cid, f"✅ Ситуация сохранена: {scene[:50]}...")
    else:
        bot.send_message(cid, "❌ Ситуация не может быть пустой.")
    try:
        markup, text = kb.character_card_keyboard(cid)
        bot.edit_message_text(text, cid, menu_msg_id, parse_mode="Markdown", reply_markup=markup)
    except:
        sent = bot.send_message(cid, "🎴 Мой персонаж", reply_markup=kb.character_card_keyboard(cid)[0])
        menu_message_id[cid] = sent.message_id

# -------------------- ОБРАБОТКА ВВОДА СВОЕГО ЛИМИТА --------------------
def process_custom_limit(message, menu_msg_id):
    cid = message.chat.id
    try:
        limit = max(10, min(1500, int(message.text)))
        update_user_setting(cid, 'limit', limit)
        bot.send_message(cid, f"✅ Лимит: {limit}")
    except:
        bot.send_message(cid, "❌ Нужно число от 10 до 1500.")
    try:
        markup, text = kb.limit_menu_keyboard(cid)
        bot.edit_message_text(text, cid, menu_msg_id, parse_mode="Markdown", reply_markup=markup)
    except:
        sent = bot.send_message(cid, "📏 Лимит", reply_markup=kb.limit_menu_keyboard(cid)[0])
        menu_message_id[cid] = sent.message_id

# -------------------- ОСНОВНОЙ ОБРАБОТЧИК RP-СООБЩЕНИЙ --------------------
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/') and m.text not in [
    "🎮 НАЧАТЬ РОЛЕВУЮ ИГРУ",
    "⚙️ Настройки",
    "🎴 Мой персонаж",
    "❓ Помощь",
    "ℹ️ О боте",
    "🎮 Меню"
])
def handle_rp(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        return
    cid = message.chat.id

    if contains_forbidden(message.text):
        bot.reply_to(message, "⛔ Запрещённая тема.")
        return

    if cid not in user_settings:
        reset_all(cid)

    bot.send_chat_action(cid, 'typing')
    reply = query_dolphin(message.text, cid, client)
    bot.send_message(cid, reply)

# -------------------- ЗАПУСК --------------------
if __name__ == "__main__":
    print("🚀 Бот с карточкой персонажа (Character AI) запущен!")
    bot.polling(none_stop=True)
