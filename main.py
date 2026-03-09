import telebot
import requests
import os
import time
from threading import Thread

# Берем токены из настроек Render (Environment)
TG_TOKEN = os.getenv("TG_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# Проверка наличия токенов
if not TG_TOKEN:
    raise ValueError("TG_TOKEN не найден в переменных окружения!")
if not HF_TOKEN:
    raise ValueError("HF_TOKEN не найден в переменных окружения!")

# Правильный адрес для Hugging Face Inference API
MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.3"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"

bot = telebot.TeleBot(TG_TOKEN)

# Хранилище для истории диалогов (в памяти, для Render лучше использовать Redis)
user_conversations = {}

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        "👋 Привет! Я бот на основе Mistral-7B.\n\n"
        "📝 Просто напиши мне сообщение, и я отвечу.\n"
        "🔄 Используй /clear чтобы очистить историю диалога.\n"
        "ℹ️ Используй /info для информации о боте."
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['clear'])
def clear_history(message):
    user_id = message.from_user.id
    if user_id in user_conversations:
        del user_conversations[user_id]
    bot.reply_to(message, "🧹 История диалога очищена!")

@bot.message_handler(commands=['info'])
def show_info(message):
    info_text = (
        f"🤖 Модель: {MODEL_ID}\n"
        f"⚙️ Максимальная длина ответа: 500 токенов\n"
        f"💬 Поддержка истории диалога: Да\n"
        f"🌐 Работает через Hugging Face Inference API"
    )
    bot.reply_to(message, info_text)

@bot.message_handler(func=lambda message: True)
def chat(message):
    user_id = message.from_user.id
    user_message = message.text
    
    # Показываем, что бот печатает
    bot.send_chat_action(message.chat.id, 'typing')
    
    # Добавляем наш HF_TOKEN в заголовки
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # Получаем или создаем историю диалога для пользователя
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    
    # Добавляем сообщение пользователя в историю
    user_conversations[user_id].append({"role": "user", "content": user_message})
    
    # Ограничиваем историю последними 5 сообщениями (чтобы не превышать лимиты)
    if len(user_conversations[user_id]) > 10:
        user_conversations[user_id] = user_conversations[user_id][-10:]
    
    # Формируем промпт с историей
    conversation_history = ""
    for msg in user_conversations[user_id][:-1]:  # Все кроме последнего
        role = "Пользователь" if msg["role"] == "user" else "Ассистент"
        conversation_history += f"{role}: {msg['content']}\n"
    
    # Формируем полный промпт
    full_prompt = f"{conversation_history}Пользователь: {user_message}\nАссистент:"
    
    payload = {
        "inputs": full_prompt,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.7,
            "top_p": 0.95,
            "do_sample": True
        }
    }

    try:
        # Отправляем запрос в Hugging Face с таймаутом
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        result = response.json()

        # Проверяем, не «спит» ли модель (она может загружаться)
        if isinstance(result, dict):
            if "estimated_time" in result:
                bot.reply_to(message, "⏳ Модель загружается... Подожди 30 секунд и попробуй снова!")
                return
            if "error" in result:
                error_msg = result.get('error', 'Неизвестная ошибка')
                if "loading" in error_msg.lower():
                    bot.reply_to(message, "⏳ Модель загружается на сервере. Попробуй через минуту!")
                else:
                    bot.reply_to(message, f"❌ Ошибка API: {error_msg[:200]}")
                return

        # Достаем ответ (Hugging Face возвращает список словарей)
        if isinstance(result, list) and len(result) > 0:
            raw_text = result[0].get('generated_text', '')
            
            # Извлекаем только ответ ассистента
            if 'Ассистент:' in raw_text:
                clean_reply = raw_text.split('Ассистент:')[-1].strip()
            else:
                clean_reply = raw_text.strip()
            
            # Добавляем ответ ассистента в историю
            if clean_reply:
                user_conversations[user_id].append({"role": "assistant", "content": clean_reply})
                bot.reply_to(message, clean_reply)
            else:
                bot.reply_to(message, "🤔 Я задумалась, попробуй переформулировать вопрос!")
        else:
            bot.reply_to(message, "❓ Что-то пошло не так. Попробуй позже!")
            
    except requests.exceptions.Timeout:
        bot.reply_to(message, "⏰ Время ожидания ответа истекло. Попробуй еще раз!")
    except requests.exceptions.ConnectionError:
        bot.reply_to(message, "🔌 Проблемы с подключением к API. Проверь интернет!")
    except Exception as e:
        print(f"Ошибка в коде: {e}")
        bot.reply_to(message, "😵 Ой, у меня головка разболелась... Попробуй еще раз!")

# Функция для очистки старых диалогов
def cleanup_old_conversations():
    while True:
        time.sleep(3600)  # Каждый час
        # Здесь можно добавить логику очистки старых диалогов
        print("Очистка диалогов...")

if __name__ == "__main__":
    print("🚀 Бот запускается...")
    print(f"📝 Модель: {MODEL_ID}")
    
    # Запускаем фоновую очистку
    cleanup_thread = Thread(target=cleanup_old_conversations, daemon=True)
    cleanup_thread.start()
    
    # Запускаем бота с обработкой ошибок
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"❌ Ошибка polling: {e}")
            time.sleep(5)
