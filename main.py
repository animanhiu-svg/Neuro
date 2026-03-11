import os
import json
import telebot
from openai import OpenAI
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

import config
import utils
from database import (
    init_user, update_field, get_field,
    clear_history, add_to_history
)
from logic import contains_forbidden, query_dolphin

# Запуск пингера (если нужно)
utils.start_pinger()

client = OpenAI(base_url=config.BASE_URL, api_key=config.HF_TOKEN)
bot = telebot.TeleBot(config.TG_TOKEN)

# -------------------- Утилита для URL WebApp --------------------
def get_webapp_url():
    if os.getenv('RENDER_EXTERNAL_HOSTNAME'):
        return f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/app"
    return f"http://localhost:{config.PORT}/app"

# -------------------- Команда /start --------------------
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ Только для владельца.")
        return

    cid = message.chat.id
    init_user(cid)  # создаём запись в БД

    # Кнопка для открытия мини-приложения
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(
        "🚀 Создать / Редактировать персонажа",
        web_app=WebAppInfo(url=get_webapp_url())
    ))

    bot.send_message(
        cid,
        "👋 Привет! Это твой конструктор персонажей с искусственным интеллектом.\n"
        "Нажми кнопку ниже, чтобы открыть мини‑приложение и настроить героя.\n\n"
        "После сохранения просто пиши сообщения – я буду отвечать от лица персонажа.",
        reply_markup=markup
    )

# -------------------- Получение данных из мини-приложения --------------------
@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    cid = message.chat.id
    if cid != config.ALLOWED_USER_ID:
        return

    try:
        data = json.loads(message.web_app_data.data)
        # Ожидаем словарь с полями персонажа
        for key, value in data.items():
            if value:  # сохраняем только непустые поля
                update_field(cid, key, value)
        bot.send_message(cid, "✅ Персонаж сохранён! Теперь можно общаться.")
    except Exception as e:
        bot.send_message(cid, f"❌ Ошибка при сохранении: {e}")

# -------------------- Общение с AI --------------------
@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
def handle_chat(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        return

    cid = message.chat.id
    text = message.text

    # Проверка на запрещённые темы
    if contains_forbidden(text):
        bot.reply_to(message, "⛔ Запрещённая тема.")
        return

    # Инициализация на всякий случай
    init_user(cid)

    # Показываем индикатор "печатает"
    bot.send_chat_action(cid, 'typing')

    # Получаем ответ от AI
    reply = query_dolphin(text, cid, client)
    bot.send_message(cid, reply)

# -------------------- Запуск --------------------
if __name__ == "__main__":
    print("🚀 Бот запущен (чистая версия с Mini App)")
    bot.polling(none_stop=True)
