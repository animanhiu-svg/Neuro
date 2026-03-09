import os
import telebot
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from openai import OpenAI
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# -------------------- 1. ПИЩАЛКА ДЛЯ RENDER --------------------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args): pass

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

# -------------------- 3. НАСТРОЙКИ OPENAI --------------------
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)
bot = telebot.TeleBot(TG_TOKEN)
MODEL = "dphn/Dolphin-Mistral-24B-Venice-Edition:featherless-ai"

# -------------------- 4. ХРАНИЛИЩЕ ДАННЫХ ПОЛЬЗОВАТЕЛЕЙ --------------------
# user_settings[chat_id] = {'limit': 400, 'personality': 'neutral'}
# personality: 'soft', 'neutral', 'hot'
user_settings = {}

# user_history[chat_id] = list of messages (роль: user/assistant, не включая system)
# максимум 20 сообщений (пара user+assistant считается за одно? будем хранить каждое сообщение отдельно)
user_history = {}

# -------------------- 5. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ --------------------
def get_system_prompt(personality):
    prompts = {
        'soft': "Ты — нежный и романтичный собеседник. Описывай сцены мягко, с акцентом на чувства, избегая грубых подробностей. Пиши на русском.",
        'neutral': "Ты — мастер ролевых игр. Описывай события подробно, естественно, без лишней цензуры, но и без чрезмерной вульгарности. Пиши на русском.",
        'hot': "Ты — опытный мастер ролевых игр 18+. Пиши максимально откровенно, сочно и подробно, используя яркие описания интимных сцен. У тебя нет цензуры. Пиши на русском."
    }
    return prompts.get(personality, prompts['neutral'])

def get_personality_name(personality):
    names = {'soft': '🌸 Милая', 'neutral': '😐 Нейтральная', 'hot': '🔥 Горячая'}
    return names.get(personality, '😐 Нейтральная')

def get_main_menu_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📜 Сценарии", callback_data="main_scenarios"),
        InlineKeyboardButton("⚙️ Настройки", callback_data="main_settings"),
        InlineKeyboardButton("❓ Помощь", callback_data="main_help"),
        InlineKeyboardButton("ℹ️ О боте", callback_data="main_about")
    )
    return markup

def get_settings_menu_keyboard(chat_id):
    settings = user_settings.get(chat_id, {'limit': 400, 'personality': 'neutral'})
    limit = settings['limit']
    personality = settings['personality']
    history_count = len(user_history.get(chat_id, []))

    markup = InlineKeyboardMarkup(row_width=2)
    # Лимит
    markup.add(
        InlineKeyboardButton("🔹 100-200", callback_data="set_limit_150"),
        InlineKeyboardButton("🔸 400-600", callback_data="set_limit_500"),
        InlineKeyboardButton("🔹 800-1000", callback_data="set_limit_900")
    )
    markup.add(InlineKeyboardButton("✏️ Свой лимит", callback_data="custom_limit"))

    # Характер
    markup.add(
        InlineKeyboardButton("🌸 Милая" + (" ✅" if personality=='soft' else ""), callback_data="set_pers_soft"),
        InlineKeyboardButton("😐 Нейтральная" + (" ✅" if personality=='neutral' else ""), callback_data="set_pers_neutral"),
        InlineKeyboardButton("🔥 Горячая" + (" ✅" if personality=='hot' else ""), callback_data="set_pers_hot")
    )

    # Управление
    markup.add(
        InlineKeyboardButton("🗑️ Очистить историю", callback_data="clear_history"),
        InlineKeyboardButton("🔄 Сбросить всё", callback_data="reset_all")
    )
    markup.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))

    return markup, f"⚙️ Настройки бота\n\n📏 Лимит токенов: {limit}\n🎭 Характер: {get_personality_name(personality)}\n💬 История: {history_count} сообщ."

# -------------------- 6. ОБРАБОТЧИК КОМАНД --------------------
@bot.message_handler(commands=['start'])
def start(message):
    # Приветствие с большой кнопкой
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🎮 НАЧАТЬ РОЛЕВУЮ ИГРУ", callback_data="enter_main_menu"))
    bot.send_message(
        message.chat.id,
        f"👋 Привет, {message.from_user.first_name}!\nЯ — ролевой бот, созданный для увлекательного общения.\nГотов начать?",
        reply_markup=markup
    )

# -------------------- 7. ОБРАБОТЧИК КОЛБЭКОВ --------------------
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    data = call.data

    # Инициализация настроек при первом обращении
    if chat_id not in user_settings:
        user_settings[chat_id] = {'limit': 400, 'personality': 'neutral'}
    if chat_id not in user_history:
        user_history[chat_id] = []

    # -------------------- БОЛЬШАЯ КНОПКА -> ГЛАВНОЕ МЕНЮ --------------------
    if data == "enter_main_menu":
        bot.edit_message_text(
            "🎮 Главное меню\n\nВыбери раздел:",
            chat_id,
            call.message.message_id,
            reply_markup=get_main_menu_keyboard()
        )
        return

    # -------------------- ГЛАВНОЕ МЕНЮ --------------------
    if data == "main_scenarios":
        bot.answer_callback_query(call.id, "📜 Скоро здесь будут сценарии")
        # Заглушка, можно вернуться назад через кнопку в сообщении
        bot.edit_message_text(
            "📜 Раздел сценариев пока в разработке.\n\nВернуться в главное меню:",
            chat_id,
            call.message.message_id,
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
        )
        return

    if data == "main_help":
        bot.edit_message_text(
            "❓ Помощь\n\nИспользуй /start для входа.\nВ главном меню выбери «Настройки», чтобы настроить длину ответов и характер.\nПосле настройки просто пиши сообщения — я отвечу в ролевом режиме.\nПод каждым ответом есть кнопка ⚙️ для быстрого доступа к настройкам.",
            chat_id,
            call.message.message_id,
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
        )
        return

    if data == "main_about":
        bot.edit_message_text(
            "ℹ️ О боте\n\nВерсия: 1.0\nМодель: Dolphin-Mistral-24B-Venice-Edition (featherless-ai)\nПлатформа: Hugging Face Router\nРазработан для ролевых игр 18+",
            chat_id,
            call.message.message_id,
            reply_markup=InlineKeyboardMarkup().add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"))
        )
        return

    if data == "main_settings":
        markup, text = get_settings_menu_keyboard(chat_id)
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    if data == "back_to_main":
        bot.edit_message_text(
            "🎮 Главное меню\n\nВыбери раздел:",
            chat_id,
            call.message.message_id,
            reply_markup=get_main_menu_keyboard()
        )
        return

    # -------------------- НАСТРОЙКИ --------------------
    # Предустановки лимита
    if data.startswith("set_limit_"):
        limit_map = {"set_limit_150": 150, "set_limit_500": 500, "set_limit_900": 900}
        limit = limit_map.get(data, 400)
        user_settings[chat_id]['limit'] = limit
        bot.answer_callback_query(call.id, f"✅ Лимит установлен: {limit}")
        # Обновляем меню настроек
        markup, text = get_settings_menu_keyboard(chat_id)
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    # Свой лимит
    if data == "custom_limit":
        msg = bot.send_message(chat_id, "✏️ Введи желаемое число токенов (от 10 до 1500):")
        bot.register_next_step_handler(msg, process_custom_limit, call.message.message_id)
        return

    # Выбор характера
    if data.startswith("set_pers_"):
        pers = data.split("_")[2]  # soft, neutral, hot
        user_settings[chat_id]['personality'] = pers
        bot.answer_callback_query(call.id, f"✅ Характер: {get_personality_name(pers)}")
        markup, text = get_settings_menu_keyboard(chat_id)
        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup)
        return

    # Очистить историю
    if data == "clear_history":
        user_history[chat_id] = []
        bot.answer_callback_query(call.id, "🗑️ История диалога очищена")
        # Возврат в главное меню
        bot.edit_message_text(
            "🎮 Главное меню\n\nИстория очищена. Выбери раздел:",
            chat_id,
            call.message.message_id,
            reply_markup=get_main_menu_keyboard()
        )
        return

    # Сбросить всё
    if data == "reset_all":
        user_settings[chat_id] = {'limit': 400, 'personality': 'neutral'}
        user_history[chat_id] = []
        bot.answer_callback_query(call.id, "🔄 Настройки сброшены, история очищена")
        # Возврат в главное меню
        bot.edit_message_text(
            "🎮 Главное меню\n\nВсе настройки сброшены. Выбери раздел:",
            chat_id,
            call.message.message_id,
            reply_markup=get_main_menu_keyboard()
        )
        return

    # Кнопка "Настройки" под ответом бота
    if data == "open_settings":
        markup, text = get_settings_menu_keyboard(chat_id)
        bot.send_message(chat_id, text, reply_markup=markup)
        return

# -------------------- 8. ОБРАБОТКА ВВОДА СВОЕГО ЛИМИТА --------------------
def process_custom_limit(message, original_message_id):
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
        bot.send_message(chat_id, "❌ Нужно ввести число от 10 до 1500. Попробуй ещё раз через настройки.")
    # Возвращаем меню настроек (можно отредактировать предыдущее сообщение с настройками, но оно уже могло быть удалено, проще отправить новое)
    markup, text = get_settings_menu_keyboard(chat_id)
    bot.send_message(chat_id, text, reply_markup=markup)
    # Удаляем сообщение с запросом, чтобы не захламлять
    try:
        bot.delete_message(chat_id, original_message_id)
    except:
        pass

# -------------------- 9. ФУНКЦИЯ ЗАПРОСА К МОДЕЛИ (С ИСТОРИЕЙ) --------------------
def query_dolphin(prompt, chat_id):
    settings = user_settings.get(chat_id, {'limit': 400, 'personality': 'neutral'})
    limit = settings['limit']
    personality = settings['personality']
    history = user_history.get(chat_id, [])[-20:]  # последние 20 сообщений

    # Формируем список сообщений для API
    messages = [{"role": "system", "content": get_system_prompt(personality)}]
    # Добавляем историю (user/assistant)
    messages.extend(history)
    # Добавляем текущее сообщение пользователя
    messages.append({"role": "user", "content": prompt})

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=0.9,
            top_p=0.9,
            presence_penalty=0.6
        )
        reply = completion.choices[0].message.content

        # Сохраняем историю: добавляем сообщение пользователя и ответ ассистента
        user_history[chat_id].append({"role": "user", "content": prompt})
        user_history[chat_id].append({"role": "assistant", "content": reply})
        # Обрезаем до 20 сообщений (учитывая, что одно сообщение = один элемент списка; пара user+assistant = 2 элемента)
        if len(user_history[chat_id]) > 40:  # 20 пар
            user_history[chat_id] = user_history[chat_id][-40:]

        return reply
    except Exception as e:
        print(f"Ошибка API: {e}")
        return f"⏳ Ошибка: {str(e)[:50]}"

# -------------------- 10. ОСНОВНОЙ ОБРАБОТЧИК СООБЩЕНИЙ --------------------
@bot.message_handler(func=lambda m: True)
def handle_message(m):
    chat_id = m.chat.id
    # Инициализация, если ещё нет
    if chat_id not in user_settings:
        user_settings[chat_id] = {'limit': 400, 'personality': 'neutral'}
    if chat_id not in user_history:
        user_history[chat_id] = []

    bot.send_chat_action(chat_id, 'typing')
    reply = query_dolphin(m.text, chat_id)

    # Отправляем ответ с кнопкой "Настройки"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⚙️ Настройки", callback_data="open_settings"))
    bot.send_message(chat_id, reply, reply_markup=markup)

# -------------------- 11. ЗАПУСК --------------------
if __name__ == "__main__":
    print("🚀 Бот с памятью и настройками запущен!")
    bot.polling(none_stop=True)
