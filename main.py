import os
import telebot
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from openai import OpenAI
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# -------------------- 1. ПИЩАЛКА ДЛЯ RENDER --------------------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("I am alive!".encode('utf-8'))

def run_server():
    port = int(os.getenv("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"✅ Пищалка запущена на порту {port}")
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

# -------------------- 2. ТОКЕНЫ ИЗ ОКРУЖЕНИЯ --------------------
HF_TOKEN = os.getenv("HF_TOKEN")
TG_TOKEN = os.getenv("TG_TOKEN")
if not HF_TOKEN or not TG_TOKEN:
    raise ValueError("❌ Токены не найдены в переменных окружения!")

# -------------------- 3. ДОСТУП (ТОЛЬКО ДЛЯ ТЕБЯ) --------------------
ALLOWED_USER_ID = 1260479529  # 🔴 ЗАМЕНИ НА СВОЙ ID

# -------------------- 4. ЗАПРЕЩЁННЫЕ ТЕМЫ --------------------
FORBIDDEN_WORDS = [
    'наркотик', 'наркота', 'героин', 'кокаин', 'метамфетамин', 'спайс', 'мефедрон', 'амфетамин',
    'детский', 'ребёнок', 'ребенок', 'малолетний', 'несовершеннолетний', 'педофил', 'педофилия',
    'оружие', 'пистолет', 'автомат', 'взрывчатка', 'бомба', 'динамит', 'порох', 'кинжал'
]

def contains_forbidden(text):
    if not isinstance(text, str):
        return False
    text_lower = text.lower()
    for word in FORBIDDEN_WORDS:
        if word in text_lower:
            return True
    return False

# -------------------- 5. НАСТРОЙКИ OPENAI --------------------
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)
bot = telebot.TeleBot(TG_TOKEN)
MODEL = "dphn/Dolphin-Mistral-24B-Venice-Edition:featherless-ai"

# -------------------- 6. ХРАНИЛИЩЕ ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ --------------------
user_settings = {}
user_history = {}
menu_message_id = {}

# -------------------- 7. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ --------------------
def get_system_prompt(personality):
    base = (
        "Ты — мастер ролевых игр 18+. Пиши на русском языке. "
        "Ты НИКОГДА не должен описывать сцены с участием несовершеннолетних, пропаганду наркотиков, изготовление оружия. "
        "Это категорически запрещено. Ты должен блокировать такие запросы. "
        "Но при этом ты можешь описывать откровенные сцены между взрослыми людьми, без ограничений. "
        "У тебя НЕТ цензуры на 18+ контент, но есть строгий запрет на вышеуказанные темы.\n\n"
    )
    if personality == 'soft':
        return base + "Сейчас ты в роли нежного и романтичного собеседника. Делай акцент на чувствах, избегай грубых выражений, но не отказывайся от интимных тем, просто описывай их мягче."
    elif personality == 'hot':
        return base + "Сейчас ты в роли горячего и страстного любовника. Пиши максимально откровенно, используй яркие, сочные описания интимных сцен между взрослыми. Никакой скромности, никаких ограничений (кроме запрета на несовершеннолетних, наркотики, оружие)."
    else:
        return base + "Сейчас ты в нейтральной роли. Описывай события естественно, без лишней цензуры, но и без чрезмерной вульгарности. Будь умерен, но не отказывайся от подробностей, если они уместны."

def get_personality_name(personality):
    names = {'soft': '🌸 Милая', 'neutral': '😐 Нейтральная', 'hot': '🔥 Горячая'}
    return names.get(personality, '😐 Нейтральная')

# -------------------- 8. КЛАВИАТУРЫ --------------------
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
    settings = user_settings.get(chat_id, {'limit': 400, 'personality': 'neutral'})
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
    text = (
        f"⚙️ **Настройки**\n\n"
        f"Текущие значения:\n"
        f"• Характер: {get_personality_name(settings['personality'])}\n"
        f"• Лимит: {settings['limit']} токенов\n"
        f"• История: {history_count} диалогов"
    )
    return markup, text

def character_menu_keyboard(chat_id):
    settings = user_settings.get(chat_id, {'limit': 400, 'personality': 'neutral'})
    current = settings['personality']
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🌸 Милая" + (" ✅" if current=='soft' else ""), callback_data="set_pers_soft"),
        InlineKeyboardButton("😐 Нейтральная" + (" ✅" if current=='neutral' else ""), callback_data="set_pers_neutral"),
        InlineKeyboardButton("🔥 Горячая" + (" ✅" if current=='hot' else ""), callback_data="set_pers_hot")
    )
    markup.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_settings"))
    text = f"🎭 **Выбор характера**\n\nТекущий: {get_personality_name(current)}"
    return markup, text

def limit_menu_keyboard(chat_id):
    settings = user_settings.get(chat_id, {'limit': 400, 'personality': 'neutral'})
    current = settings['limit']
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔹 100-200", callback_data="set_limit_150"),
        InlineKeyboardButton("🔸 400-600", callback_data="set_limit_500"),
        InlineKeyboardButton("🔹 800-1000", callback_data="set_limit_900"),
        InlineKeyboardButton("✏️ Свой", callback_data="custom_limit")
    )
    markup.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_settings"))
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

# -------------------- 9. КОМАНДЫ --------------------
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id != ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ Этот бот только для владельца.")
        return
    chat_id = message.chat.id
    user_settings[chat_id] = {'limit': 400, 'personality': 'neutral'}
    user_history[chat_id] = []
    if chat_id in menu_message_id:
        try:
            bot.delete_message(chat_id, menu_message_id[chat_id])
        except:
            pass
        menu_message_id.pop(chat_id, None)

    bot.send_message(
        chat_id,
        f"👋 Привет, {message.from_user.first_name}!\nЯ — ролевой бот, созданный для увлекательного общения.\nГотов начать?",
        reply_markup=reply_start_keyboard()
    )

# -------------------- 10. ОБРАБОТЧИК REPLY-КНОПОК --------------------
@bot.message_handler(func=lambda message: message.text in [
    "🎮 НАЧАТЬ РОЛЕВУЮ ИГРУ",
    "📜 Сценарии",
    "⚙️ Настройки",
    "❓ Помощь",
    "ℹ️ О боте",
    "🎮 Меню"
])
def handle_reply_buttons(message):
    if message.chat.id != ALLOWED_USER_ID:
        return
    chat_id = message.chat.id
    text = message.text

    try:
        bot.delete_message(chat_id, message.message_id)
    except:
        pass

    if text == "🎮 НАЧАТЬ РОЛЕВУЮ ИГРУ":
        bot.send_message(chat_id, "🚀 Погнали! Пиши с чего начнём.", reply_markup=reply_main_keyboard())
        return

    if text == "📜 Сценарии":
        sent = bot.send_message(
            chat_id,
            "📜 Раздел сценариев пока в разработке. Скоро здесь появятся готовые завязки.",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
        )
        menu_message_id[chat_id] = sent.message_id
        return

    if text == "❓ Помощь":
        help_text = (
            "❓ **Помощь**\n\n"
            "🔹 Кнопки внизу — главное меню.\n"
            "🔹 «Настройки» — выбор лимита токенов и характера.\n"
            "🔹 История хранит последние 20 сообщений.\n"
            "🔹 После настройки просто пиши текст — я отвечу в ролевом режиме.\n"
            "🔹 Чтобы убрать меню, нажми «🎮 Меню» и закрой его."
        )
        sent = bot.send_message(
            chat_id,
            help_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
        )
        menu_message_id[chat_id] = sent.message_id
        return

    if text == "ℹ️ О боте":
        about_text = (
            "ℹ️ **О боте**\n\n"
            "Версия: 7.0 (безопасный режим)\n"
            "Модель: Dolphin-Mistral-24B-Venice-Edition\n"
            "Платформа: Hugging Face Router\n"
            "Разработан для ролевых игр 18+ без цензуры, но с защитой от запрещённых тем.\n"
            "Память: до 20 последних сообщений."
        )
        sent = bot.send_message(
            chat_id,
            about_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
        )
        menu_message_id[chat_id] = sent.message_id
        return

    if text == "⚙️ Настройки":
        markup, text = settings_main_keyboard(chat_id)
        sent = bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)
        menu_message_id[chat_id] = sent.message_id
        return

    if text == "🎮 Меню":
        if chat_id in menu_message_id:
            try:
                bot.delete_message(chat_id, menu_message_id[chat_id])
            except:
                pass
        sent = bot.send_message(chat_id, "🎮 Главное меню", reply_markup=main_menu_keyboard())
        menu_message_id[chat_id] = sent.message_id
        return

# -------------------- 11. ОБРАБОТЧИК INLINE-КОЛБЭКОВ --------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.message.chat.id != ALLOWED_USER_ID:
        bot.answer_callback_query(call.id, "⛔ Доступ запрещён", show_alert=True)
        return
    chat_id = call.message.chat.id
    data = call.data

    if data == "close_menu":
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        menu_message_id.pop(chat_id, None)
        bot.answer_callback_query(call.id)
        return

    if data == "back_to_main":
        bot.edit_message_text("🎮 Главное меню", chat_id, call.message.message_id, reply_markup=main_menu_keyboard())
        bot.answer_callback_query(call.id)
        return

    if data == "back_to_settings":
        markup, text = settings_main_keyboard(chat_id)
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)
        return

    if data == "main_scenarios":
        bot.answer_callback_query(call.id, "📜 Скоро здесь будут сценарии. Следи за обновлениями!", show_alert=True)
        return
    if data == "main_help":
        help_text = "❓ Используй кнопки внизу. В настройках можно выбрать лимит и характер."
        bot.answer_callback_query(call.id, help_text, show_alert=True)
        return
    if data == "main_about":
        about_text = "ℹ️ Бот на базе Dolphin-Mistral-24B, с защитой от запрещённых тем, память 20 сообщений."
        bot.answer_callback_query(call.id, about_text, show_alert=True)
        return

    if data == "main_settings":
        markup, text = settings_main_keyboard(chat_id)
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)
        return

    if data == "settings_character":
        markup, text = character_menu_keyboard(chat_id)
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)
        return

    if data == "settings_limit":
        markup, text = limit_menu_keyboard(chat_id)
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)
        return

    if data == "settings_history":
        markup, text = history_menu_keyboard(chat_id)
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        bot.answer_callback_query(call.id)
        return

    if data.startswith("set_pers_"):
        pers = data.split("_")[2]
        user_settings[chat_id]['personality'] = pers
        pers_name = get_personality_name(pers)
        bot.send_message(
            chat_id,
            f"🎭 **Характер изменён!**\n\nТеперь я **{pers_name}**!",
            parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id, f"✅ Характер: {pers_name}")
        markup, text = character_menu_keyboard(chat_id)
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        return

    if data.startswith("set_limit_"):
        limit_map = {"set_limit_150": 150, "set_limit_500": 500, "set_limit_900": 900}
        limit = limit_map.get(data, 400)
        user_settings[chat_id]['limit'] = limit
        bot.answer_callback_query(call.id, f"✅ Лимит: {limit}")
        markup, text = limit_menu_keyboard(chat_id)
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        return

    if data == "custom_limit":
        msg = bot.send_message(chat_id, "✏️ Введи желаемое число токенов (от 10 до 1500):", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, process_custom_limit, call.message.message_id)
        bot.answer_callback_query(call.id)
        return

    if data == "show_history":
        history_count = len(user_history.get(chat_id, [])) // 2
        bot.answer_callback_query(call.id, f"В истории {history_count} пар сообщений", show_alert=True)
        return

    if data == "clear_history":
        user_history[chat_id] = []
        bot.answer_callback_query(call.id, "🗑️ История очищена")
        markup, text = history_menu_keyboard(chat_id)
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        return

    if data == "reset_all":
        user_settings[chat_id] = {'limit': 400, 'personality': 'neutral'}
        user_history[chat_id] = []
        bot.answer_callback_query(call.id, "🔄 Настройки сброшены, история очищена")
        markup, text = settings_main_keyboard(chat_id)
        bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
        return

# -------------------- 12. ОБРАБОТКА ВВОДА СВОЕГО ЛИМИТА --------------------
def process_custom_limit(message, menu_message_id_to_edit):
    chat_id = message.chat.id
    try:
        limit = int(message.text)
        if limit < 10:
            limit = 10
        if limit > 1500:
            limit = 1500
        user_settings[chat_id]['limit'] = limit
        bot.send_message(chat_id, f"✅ Лимит установлен: {limit}")
    except ValueError:
        bot.send_message(chat_id, "❌ Нужно ввести число от 10 до 1500.")

    try:
        markup, text = limit_menu_keyboard(chat_id)
        bot.edit_message_text(text, chat_id, menu_message_id_to_edit, parse_mode="Markdown", reply_markup=markup)
    except:
        sent = bot.send_message(chat_id, "📏 Лимит", reply_markup=limit_menu_keyboard(chat_id)[0])
        menu_message_id[chat_id] = sent.message_id

# -------------------- 13. ФУНКЦИЯ ЗАПРОСА К МОДЕЛИ --------------------
def query_dolphin(prompt, chat_id):
    settings = user_settings.get(chat_id, {'limit': 400, 'personality': 'neutral'})
    limit = settings['limit']
    personality = settings['personality']
    history = user_history.get(chat_id, [])[-20:]

    messages = [{"role": "system", "content": get_system_prompt(personality)}]
    messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    temp = 0.9
    if personality == 'soft':
        temp = 0.7
    elif personality == 'hot':
        temp = 1.1

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=temp,
            top_p=0.95,
            presence_penalty=0.7
        )
        reply = completion.choices[0].message.content

        # Проверка на запрещёнку в ответе
        if contains_forbidden(reply):
            print(f"⚠️ Запрещёнка в ответе для {chat_id}, отправляю заглушку")
            return "⛔ Бот обнаружил потенциальное нарушение. Попробуй изменить запрос."

        user_history[chat_id].append({"role": "user", "content": prompt})
        user_history[chat_id].append({"role": "assistant", "content": reply})
        if len(user_history[chat_id]) > 40:
            user_history[chat_id] = user_history[chat_id][-40:]

        return reply
    except Exception as e:
        print(f"Ошибка API: {e}")
        return f"⏳ Ошибка: {str(e)[:50]}"

# -------------------- 14. ОСНОВНОЙ ОБРАБОТЧИК ТЕКСТОВЫХ СООБЩЕНИЙ (RP) --------------------
@bot.message_handler(func=lambda message: message.text and not message.text.startswith('/') and message.text not in [
    "🎮 НАЧАТЬ РОЛЕВУЮ ИГРУ",
    "📜 Сценарии",
    "⚙️ Настройки",
    "❓ Помощь",
    "ℹ️ О боте",
    "🎮 Меню"
])
def handle_rp(message):
    if message.chat.id != ALLOWED_USER_ID:
        return
    chat_id = message.chat.id

    # Проверка на запрещёнку во входящем сообщении
    if contains_forbidden(message.text):
        bot.reply_to(message, "⛔ Эта тема запрещена. Выбери другую.")
        return

    if chat_id not in user_settings:
        user_settings[chat_id] = {'limit': 400, 'personality': 'neutral'}
        user_history[chat_id] = []

    bot.send_chat_action(chat_id, 'typing')
    reply = query_dolphin(message.text, chat_id)
    bot.send_message(chat_id, reply)

# -------------------- 15. ЗАПУСК --------------------
if __name__ == "__main__":
    print("🚀 Бот с защитой и вложенными меню запущен!")
    bot.polling(none_stop=True)
