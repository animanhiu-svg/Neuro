import telebot
import requests
import os
import time

# Берем токены из настроек Render (Environment)
TG_TOKEN = os.getenv("TG_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# Модель Mistral (исправленный путь со слэшем)
MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.3"
API_URL = f"https://api-inference.huggingface.co{MODEL_ID}"

bot = telebot.TeleBot(TG_TOKEN)

@bot.message_handler(func=lambda message: True)
def chat(message):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": f"<s>[INST] Ты дерзкая нейросеть 18+. Отвечай на русском. {message.text} [/INST]",
        "parameters": {"max_new_tokens": 500, "return_full_text": False}
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=25)
        result = response.json()

        # Если модель еще загружается на серверах Hugging Face
        if isinstance(result, dict) and "estimated_time" in result:
            wait_time = int(result.get("estimated_time", 10))
            bot.reply_to(message, f"Мисти еще спит (загрузка модели). Попробуй через {wait_time} сек.!")
            return

        if isinstance(result, list) and len(result) > 0:
            reply = result[0].get('generated_text', "Что-то пошло не так...").strip()
            # Убираем системные теги из ответа, если они остались
            clean_reply = reply.replace(f"<s>[INST] Ты дерзкая нейросеть 18+. Отвечай на русском. {message.text} [/INST]", "").strip()
            bot.reply_to(message, clean_reply if clean_reply else "Я задумалась, попробуй еще раз!")
        else:
            print(f"Странный ответ от API: {result}")
            bot.reply_to(message, "Мисти капризничает. Напиши еще раз через минуту!")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.reply_to(message, "Ой, у меня голова разболелась... Проверь ключи в настройках!")

if __name__ == "__main__":
    print("Бот запускается...")
    # Проверка наличия токенов перед стартом
    if not TG_TOKEN or not HF_TOKEN:
        print("ОШИБКА: Токены TG_TOKEN или HF_TOKEN не найдены в Environment!")
    else:
        bot.polling(none_stop=True)
