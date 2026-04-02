import os
import json
import telebot
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
import config
import utils
from database import init_user, update_field, get_field, get_history, add_to_history
from logic import contains_forbidden, query_dolphin, query_dolphin_with_character

# Отключаем пингер, чтобы не конфликтовать с gunicorn
# utils.start_pinger()

client = OpenAI(base_url=config.BASE_URL, api_key=config.HF_TOKEN)
bot = telebot.TeleBot(config.TG_TOKEN)

app = Flask(__name__, static_folder='mini_app')

# --- Отдача статики ---
@app.route('/')
@app.route('/app')
def serve_app():
    return send_from_directory('mini_app', 'index.html')

# --- Эндпоинт для чата (мини-апп) ---
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data'}), 400
    chat_id = data.get('chat_id')
    message = data.get('message')
    character = data.get('character')
    history = data.get('history', [])
    if not chat_id or not message:
        return jsonify({'error': 'Missing parameters'}), 400

    init_user(chat_id)

    try:
        if character:
            reply = query_dolphin_with_character(message, chat_id, client, character, history)
        else:
            reply = query_dolphin(message, chat_id, client)
        return jsonify({'reply': reply})
    except Exception as e:
        print(f"❌ Ошибка в /chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'reply': f"⚠️ Ошибка: {str(e)[:100]}"}), 500

# --- Эндпоинт для сохранения персонажа ---
@app.route('/save_character', methods=['POST'])
def save_character():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data'}), 400
    chat_id = data.get('chat_id')
    character = data.get('character')
    if not chat_id or not character:
        return jsonify({'error': 'Missing data'}), 400
    init_user(chat_id)
    for key, value in character.items():
        if value:
            update_field(chat_id, key, value)
    return jsonify({'status': 'ok'})

# --- Вебхук для бота ---
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'ok', 200

# --- Ручная установка вебхука (для отладки) ---
@app.route('/set_webhook')
def set_webhook():
    base_url = os.getenv('RENDER_EXTERNAL_HOSTNAME', 'neuro-12pd.onrender.com')
    webhook_url = f"https://{base_url}/webhook"
    try:
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        return f"✅ Вебхук установлен: {webhook_url}"
    except Exception as e:
        return f"❌ Ошибка: {e}"

# --- Обработчики бота ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ Только для владельца.")
        return
    cid = message.chat.id
    init_user(cid)

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    webapp_button = telebot.types.KeyboardButton(
        text="🚀 Погрузиться",
        web_app=telebot.types.WebAppInfo(url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'neuro-12pd.onrender.com')}/app"),
        style="primary"
    )
    markup.add(webapp_button)

    bot.send_message(
        cid,
        "👋 Привет, друг!\n\n"
        "Я помогу тебе создать уникального персонажа с помощью нейросети.\n"
        "Нажимай кнопку **«Погрузиться»** — там ты сможешь задать имя, внешность, характер и даже загрузить фото.\n\n"
        "После сохранения просто пиши мне, и я буду отвечать от лица твоего героя 😊",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    cid = message.chat.id
    if cid != config.ALLOWED_USER_ID:
        return
    try:
        data = json.loads(message.web_app_data.data)
        if 'character' in data:
            for key, value in data['character'].items():
                if value:
                    update_field(cid, key, value)
        else:
            for key, value in data.items():
                if value:
                    update_field(cid, key, value)
        bot.send_message(cid, "✅ Персонаж сохранён! Теперь можно общаться.")
    except Exception as e:
        bot.send_message(cid, f"❌ Ошибка при сохранении: {e}")

@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
def handle_chat(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        print(f"⚠️ Доступ запрещён для {message.chat.id}")
        return
    cid = message.chat.id
    text = message.text
    if contains_forbidden(text):
        bot.reply_to(message, "⛔ Запрещённая тема.")
        return
    init_user(cid)
    bot.send_chat_action(cid, 'typing')
    try:
        reply = query_dolphin(text, cid, client)
        if not reply or str(reply).strip() == "":
            bot.send_message(cid, "⚠️ Нейросеть вернула пустой ответ.")
        else:
            bot.send_message(cid, reply)
    except Exception as e:
        print(f"💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        bot.send_message(cid, f"❌ Ошибка сервера: {e}")

# --- Установка вебхука при запуске ---
def setup_webhook():
    base_url = os.getenv('RENDER_EXTERNAL_HOSTNAME', 'neuro-12pd.onrender.com')
    webhook_url = f"https://{base_url}/webhook"
    try:
        bot.remove_webhook()
        bot.set_webhook(url=webhook_url)
        print(f"✅ Вебхук установлен: {webhook_url}")
    except Exception as e:
        print(f"❌ Ошибка установки вебхука: {e}")

setup_webhook()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
