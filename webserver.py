import os
import json
import telebot
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
import config
from database import init_user, update_field, get_field, get_history, add_to_history, clear_history
from logic import contains_forbidden, query_dolphin
from threading import Thread

client = OpenAI(base_url=config.BASE_URL, api_key=config.HF_TOKEN)
bot = telebot.TeleBot(config.TG_TOKEN)

app = Flask(__name__, static_folder='mini_app')

# Railway URL
RAILWAY_URL = os.getenv('RAILWAY_PUBLIC_DOMAIN', 'neuro-production-c40f.up.railway.app')

@app.route('/')
@app.route('/app')
def serve_app():
    return send_from_directory('mini_app', 'index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data'}), 400
    chat_id = data.get('chat_id')
    character_id = data.get('character_id')
    message = data.get('message')
    if not chat_id or not character_id or not message:
        return jsonify({'error': 'Missing parameters'}), 400

    init_user(chat_id)
    try:
        reply = query_dolphin(message, chat_id, character_id, client)
        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'reply': f"⚠️ Ошибка: {str(e)[:100]}"}), 500

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

@app.route('/clear_history', methods=['POST'])
def clear_history_endpoint():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data'}), 400
    chat_id = data.get('chat_id')
    character_id = data.get('character_id')
    if not chat_id or not character_id:
        return jsonify({'error': 'Missing chat_id or character_id'}), 400
    clear_history(chat_id, character_id)
    return jsonify({'status': 'ok'})

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ Только для владельца.")
        return
    cid = message.chat.id
    init_user(cid)

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    webapp_button = telebot.types.KeyboardButton(
        text="🚀 Погрузиться",
        web_app=telebot.types.WebAppInfo(url=f"https://{RAILWAY_URL}/app")
    )
    markup.add(webapp_button)

    bot.send_message(cid, "👋 Привет!\nНажми «Погрузиться», чтобы создать персонажа.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
def handle_chat(message):
    print(f"📨 Получено сообщение: {message.text}")  # Диагностика
    if message.chat.id != config.ALLOWED_USER_ID:
        print(f"⛔ Не тот юзер: {message.chat.id}")
        return
    cid = message.chat.id
    text = message.text
    if contains_forbidden(text):
        bot.reply_to(message, "⛔ Запрещённая тема.")
        return
    init_user(cid)
    bot.send_chat_action(cid, 'typing')
    reply = query_dolphin(text, cid, 0, client)
    bot.send_message(cid, reply)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    
    # Запускаем Flask в отдельном потоке
    Thread(target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False)).start()
    
    # Удаляем вебхук нахуй
    print("🚀 Удаляем вебхук...")
    try:
        bot.remove_webhook()
        print("✅ Вебхук удален")
    except Exception as e:
        print(f"⚠️ Ошибка удаления: {e}")
    
    print(f"🤖 Запускаем polling...")
    print(f"📱 Mini-app: https://{RAILWAY_URL}/app")
    
    # Запускаем бота
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
