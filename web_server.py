import os
import json
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
import config
import utils
from database import init_user, get_field, get_history, add_to_history
from logic import query_dolphin

# Запуск пингера (если есть)
utils.start_pinger()

client = OpenAI(base_url=config.BASE_URL, api_key=config.HF_TOKEN)
app = Flask(__name__, static_folder='mini_app')

# Маршрут для главной страницы (отдаёт мини-апп)
@app.route('/')
@app.route('/app')
def serve_app():
    return send_from_directory('mini_app', 'index.html')

# Маршрут для проверки работы сервера
@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok'})

# Основной маршрут для чата
@app.route('/chat', methods=['POST'])
def chat():
    print("Получен POST-запрос на /chat")  # будет видно в логах Render
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data'}), 400

    chat_id = data.get('chat_id')
    message = data.get('message')
    if not chat_id or not message:
        return jsonify({'error': 'Missing parameters'}), 400

    # Инициализация пользователя в БД (если ещё нет)
    init_user(chat_id)

    # Получаем ответ от ИИ
    reply = query_dolphin(message, chat_id, client)
    return jsonify({'reply': reply})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Запуск Flask на порту {port}")
    app.run(host='0.0.0.0', port=port)
