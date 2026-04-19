import os
import json
import telebot
import time
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
import config
from database import init_user, update_field, get_field, get_history, add_to_history, clear_history
from logic import contains_forbidden, query_dolphin

client = OpenAI(base_url=config.BASE_URL, api_key=config.HF_TOKEN)
bot = telebot.TeleBot(config.TG_TOKEN)

app = Flask(__name__, static_folder='mini_app')

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
    character = data.get('character')
    
    if not chat_id or not character_id or not message:
        return jsonify({'error': 'Missing parameters'}), 400

    init_user(chat_id)
    
    if character and character.get('name'):
        for key, value in character.items():
            if value:
                update_field(chat_id, key, value)
    
    # ПОВТОРНАЯ ОТПРАВКА - 3 попытки
    for attempt in range(3):
        try:
            reply = query_dolphin(message, chat_id, character_id, client)
            if reply and reply != "..." and reply != "Ошибка":
                return jsonify({'reply': reply})
            else:
                print(f"Попытка {attempt+1} не удалась, ответ: {reply}")
                if attempt < 2:
                    time.sleep(1)  # ждем 1 секунду перед повтором
        except Exception as e:
            print(f"Попытка {attempt+1} ошибка: {e}")
            if attempt < 2:
                time.sleep(1)
    
    # Если все попытки провалились
    return jsonify({'reply': "⚠️ Не удалось получить ответ. Нажми «Отправить снова»."}), 500

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

@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return 'ok', 200

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
        web_app=telebot.types.WebAppInfo(url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'neuro-12pd.onrender.com')}/app")
    )
    markup.add(webapp_button)

    bot.send_message(cid, "👋 Привет!\nНажми «Погрузиться», чтобы создать персонажа.", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
def handle_chat(message):
    if message.chat.id != config.ALLOWED_USER_ID:
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
