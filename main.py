import os
import telebot
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. Твоя "пищалка" для Render (чтобы он не выключал бота)
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    # Render сам подставит порт, если нет - возьмет 10000
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"✅ Сервер-заглушка запущен на порту {port}")
    server.serve_forever()

# Запускаем сервер в фоне
Thread(target=run_server, daemon=True).start()

# 2. Настройка бота с твоим токеном
TOKEN = '8579809463:AAFr-8tqceB1E0FfUQnbDJKUjvYWpKybdGs' # Твой токен тут
bot = telebot.TeleBot(TOKEN)

# Твои функции (добавь свои, если нужно)
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Бро, всё чётко! Я работаю и Render меня не трогает. 🚀")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Ты написал: {message.text}")

# 3. Запуск бесконечного цикла бота
if __name__ == "__main__":
    print("🚀 Бот погнал...")
    bot.polling(none_stop=True)
