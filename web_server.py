import os
import json
import telebot
from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
import config

client = OpenAI(base_url=config.BASE_URL, api_key=config.HF_TOKEN)
bot = telebot.TeleBot(config.TG_TOKEN)

app = Flask(__name__, static_folder='mini_app')

# ==================== Mini App & статика ====================
@app.route('/')
@app.route('/app')
def serve_app():
    return send_from_directory('mini_app', 'index.html')

# ==================== Чат для Mini App (stateless) ====================
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No JSON data'}), 400

    message = data.get('message')
    if not message:
        return jsonify({'error': 'Missing message'}), 400

    # Получаем персонажа от фронта (все поля)
    character = data.get('character', {})
    # Получаем историю от фронта (уже в формате [{"role":..., "content":...}])
    history = data.get('history', [])

    # Строим системный промпт из полей персонажа
    system_prompt = build_system_prompt(character)

    # Формируем messages для LLM
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)          # история от фронта
    messages.append({"role": "user", "content": message})

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.8,          # повысил для ролевой игры
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.5
        )
        reply = completion.choices[0].message.content
        if not reply:
            reply = "..."
        return jsonify({'reply': reply})
    except Exception as e:
        print(f"Ошибка в /chat: {e}")
        return jsonify({'reply': "⚠️ Ошибка, попробуй ещё раз"}), 500

def build_system_prompt(character):
    name = character.get('name', 'Персонаж')
    personality = character.get('personality', '')
    scenario = character.get('scenario', 'обычный разговор')
    appearance = character.get('appearance', '')
    memory = character.get('memory', '')
    greeting = character.get('greeting', '')

    prompt = f"""Ты — {name}. {personality}
Сейчас происходит: {scenario}
Внешность: {appearance}
Память: {memory}
Приветствие: {greeting}

Правила:
- Строго следуй своему характеру и сценарию.
- Отвечай от лица {name}.
- Не ломай роль. Ты не ассистент, не языковая модель.
- Используй приветствие, если это начало диалога.
- Учитывай обстоятельства из сценария и память."""
    return prompt

# ==================== Сохранение персонажа (необязательно, клиент сам хранит) ====================
@app.route('/save_character', methods=['POST'])
def save_character():
    # Можно вообще ничего не делать, клиент сам управляет персонажами через localStorage
    # Но оставим для совместимости
    return jsonify({'status': 'ok'})

# ==================== Очистка истории (клиент сам чистит, серверу без разницы) ====================
@app.route('/clear_history', methods=['POST'])
def clear_history_endpoint():
    # Клиент сам удалит свою историю, серверу не нужно хранить
    return jsonify({'status': 'ok'})

# ==================== Webhook для Telegram ====================
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
    text = message.text
    # Простейшая проверка на запрещённые слова (можно доработать)
    if any(word in text.lower() for word in config.FORBIDDEN_WORDS):
        bot.reply_to(message, "⛔ Запрещённая тема.")
        return

    bot.send_chat_action(message.chat.id, 'typing')
    # Для Telegram используем фиксированный системный промпт (без персонажа)
    system_prompt = "Ты — полезный ассистент. Отвечай вежливо и по делу."
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]
    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        reply = completion.choices[0].message.content
        bot.send_message(message.chat.id, reply)
    except Exception as e:
        print(f"Ошибка в Telegram: {e}")
        bot.reply_to(message, "⚠️ Ошибка, попробуй позже.")

# ==================== Настройка вебхука ====================
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

# ==================== Запуск сервера ====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    # В продакшене используйте gunicorn, а не app.run()
    app.run(host='0.0.0.0', port=port)
