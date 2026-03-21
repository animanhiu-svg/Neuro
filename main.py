import os
import json
import telebot
from openai import OpenAI
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo,
    ReplyKeyboardMarkup, KeyboardButton
)

import config
import utils
from database import (
    init_user, update_field, get_field,
    clear_history, add_to_history
)
from logic import contains_forbidden, query_dolphin

utils.start_pinger()

client = OpenAI(base_url=config.BASE_URL, api_key=config.HF_TOKEN)
bot = telebot.TeleBot(config.TG_TOKEN)

def get_webapp_url():
    if os.getenv('RENDER_EXTERNAL_HOSTNAME'):
        return f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/app"
    return f"http://localhost:{config.PORT}/app"

@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        bot.reply_to(message, "⛔ Только для владельца.")
        return

    cid = message.chat.id
    init_user(cid)

    # Создаём reply-клавиатуру (гарантированно работает)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    webapp_button = KeyboardButton(
        text="🚀 Погрузиться",
        web_app=WebAppInfo(url=get_webapp_url())
    )
    markup.add(webapp_button)

    bot.send_message(
        cid,
        "👋 Привет, друг!\n\n"
        "Я помогу тебе создать уникального персонажа с помощью нейросети.\n"
        "Нажимай кнопку **«Погрузиться»** — там ты сможешь задать имя, внешность, характер и даже загрузить фото.\n\n"
        "После сохранения просто пиши мне, и я буду отвечать от лица твоего героя 😊",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(content_types=['web_app_data'])
def handle_web_app_data(message):
    cid = message.chat.id
    if cid != config.ALLOWED_USER_ID:
        return
    try:
        data = json.loads(message.web_app_data.data)
        for key, value in data.items():
            if value:
                update_field(cid, key, value)
        bot.send_message(cid, "✅ Персонаж сохранён! Теперь можно общаться.")
    except Exception as e:
        bot.send_message(cid, f"❌ Ошибка при сохранении: {e}")

@bot.message_handler(func=lambda m: m.text and not m.text.startswith('/'))
def handle_chat(message):
    if message.chat.id != config.ALLOWED_USER_ID:
        return
    cid = message.chat.id
    text = message.text
    if contains_forbidden(text):
        bot.reply_to(message, "⛔ Запрещённая тема.")
        return
    init_user(cid)
    bot.send_chat_action(cid, 'typing')
    reply = query_dolphin(text, cid, client)
    bot.send_message(cid, reply)

if __name__ == "__main__":
    print("🚀 Бот с Mini App и кнопкой запущен!")
    bot.polling(none_stop=True)
