import os
import telebot
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
from openai import OpenAI  # импортируем OpenAI

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

# --- ТОКЕНЫ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
TG_TOKEN = os.getenv("TG_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

if not TG_TOKEN or not HF_TOKEN:
    raise ValueError("❌ Ошибка: TG_TOKEN и HF_TOKEN должны быть установлены в переменных окружения!")

bot = telebot.TeleBot(TG_TOKEN)

# --- НАСТРОЙКИ МОДЕЛИ (OpenAI-совместимый режим) ---
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

MODEL_NAME = "dphn/Dolphin-Mistral-24B-Venice-Edition:featherless-ai"  # именно так!

def query_dolphin(prompt):
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )
        # Извлекаем текст ответа
        return completion.choices[0].message.content
    except Exception as e:
        return f"❌ Ошибка API: {str(e)}"

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        reply = query_dolphin(message.text)
        bot.reply_to(message, reply)
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.reply_to(message, "Техническая ошибка, уже чиним.")

if __name__ == "__main__":
    print("🚀 Бот с Dolphin-Mistral запущен!")
    bot.polling(none_stop=True)
