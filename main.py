import os
import telebot
import requests
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- ПИЩАЛКА ДЛЯ RENDER ---
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"✅ Сервер запущен на порту {port}")
    server.serve_forever()

Thread(target=run_server, daemon=True).start()

# --- ТОКЕНЫ ТОЛЬКО ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
TG_TOKEN = os.getenv("TG_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

if not TG_TOKEN or not HF_TOKEN:
    raise ValueError("❌ Ошибка: TG_TOKEN и HF_TOKEN должны быть установлены в переменных окружения!")

bot = telebot.TeleBot(TG_TOKEN)

# --- НАСТРОЙКИ MISTRAL ---
MODEL_ID = "mistralai/Mistral-7B-Instruct-v0.3"
API_URL = f"https://router.huggingface.co/models/{MODEL_ID}"
HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

def query_mistral(prompt):
    formatted_prompt = f"<s>[INST] {prompt} [/INST]"
    payload = {
        "inputs": formatted_prompt,
        "parameters": {
            "max_new_tokens": 500,
            "return_full_text": False,
            "temperature": 0.7
        }
    }
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"error": str(e)}

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        output = query_mistral(message.text)

        if isinstance(output, list) and len(output) > 0:
            ai_response = output[0].get('generated_text', 'Пустой ответ от ИИ.')
        elif isinstance(output, dict) and 'error' in output:
            error_text = output['error']
            if 'loading' in error_text.lower():
                ai_response = "⏳ Модель загружается, попробуй через 20 секунд."
            else:
                ai_response = f"Ошибка: {error_text[:200]}"
        else:
            ai_response = "Не удалось получить ответ. Попробуй позже."

        bot.reply_to(message, ai_response)
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.reply_to(message, "Техническая ошибка, уже чиним.")

if __name__ == "__main__":
    print("🚀 Бот с Mistral запущен!")
    bot.polling(none_stop=True)
