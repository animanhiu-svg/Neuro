 import telebot
import requests
import os

# Берем токены из настроек Render (Environment)
TG_TOKEN = os.getenv("TG_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# Правильный адрес для Hugging Face Inference API
MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.3"
API_URL = f"https://api-inference.huggingface.co{MODEL_ID}"

bot = telebot.TeleBot(TG_TOKEN)

@bot.message_handler(func=lambda message: True)
def chat(message):
    # Добавляем наш HF_TOKEN в заголовки
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    # Формируем запрос
    payload = {
        "inputs": f"<s>[INST] {message.text} [/INST]",
        "parameters": {"max_new_tokens": 500}
    }

    try:
        # Отправляем запрос в Hugging Face
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        result = response.json()

        # 1. Проверяем, не «спит» ли модель (она может загружаться)
        if isinstance(result, dict) and "estimated_time" in result:
            bot.reply_to(message, "Мисти еще спит (загрузка модели). Напиши через 30 секунд!")
            return

        # 2. Если API вернуло конкретную ошибку (например, плохой токен)
        if isinstance(result, dict) and "error" in result:
            bot.reply_to(message, f"Ошибка API: {result.get('error')}")
            return

        # 3. Достаем ответ (Hugging Face возвращает список словарей: [ {'generated_text': '...'} ])
        if isinstance(result, list) and len(result) > 0:
            # Берем первый словарь [0] и извлекаем текст по ключу 'generated_text'
            raw_text = result[0].get('generated_text', '')
            
            # Очищаем ответ от системных тегов [INST]
            if '[/INST]' in raw_text:
                clean_reply = raw_text.split('[/INST]')[-1].strip()
            else:
                clean_reply = raw_text.strip()
                
            bot.reply_to(message, clean_reply if clean_reply else "Я задумалась, попробуй еще раз!")
        else:
            bot.reply_to(message, "Что-то пошло не так. Попробуй позже!")
            
    except Exception as e:
        print(f"Ошибка в коде: {e}")
        bot.reply_to(message, "Ой, у меня голова разболелась... Проверь логи в Render!")

if __name__ == "__main__":
    print("Бот запускается...")
    bot.polling(none_stop=True)
