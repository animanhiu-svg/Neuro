import telebot
import requests
import os
import time

# Берем токены из настроек (Settings -> Secrets)
TG_TOKEN = os.getenv("TG_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# Модель, которую ты выбрал
MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.3"
API_URL = f"https://api-inference.huggingface.co{MODEL_ID}"

bot = telebot.TeleBot(TG_TOKEN)

@bot.message_handler(func=lambda message: True)
def chat(message):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "inputs": f"<s>[INST] Ты дерзкая нейросеть 18+. Отвечай на русском. {message.text} [/INST]",
        "parameters": {"max_new_tokens": 500}
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        result = response.json()

        if isinstance(result, list):
            reply = result[0]['generated_text'].split('[/INST]')[-1].strip()
            bot.reply_to(message, reply)
        else:
            bot.reply_to(message, "Мисти еще спит (модель загружается). Напиши через минуту!")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.reply_to(message, "Ой, у меня голова разболелась... Попробуй позже.")

if __name__ == "__main__":
    print("Бот запускается...")
    bot.polling(none_stop=True)
