import os
from dotenv import load_dotenv

load_dotenv()  # для локального тестирования

# Токены (на Render задаются в окружении)
TG_TOKEN = os.getenv("TG_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

# Только этот пользователь может пользоваться ботом
ALLOWED_USER_ID = 1260479529  # 🔴 замени на свой, если нужно

# Порт для Render
PORT = int(os.getenv("PORT", 10000))

# Модель Hugging Face
MODEL = "dphn/Dolphin-Mistral-24B-Venice-Edition:featherless-ai"
BASE_URL = "https://router.huggingface.co/v1"

# Запрещённые темы
FORBIDDEN_WORDS = [
    'наркотик', 'наркота', 'героин', 'кокаин', 'метамфетамин', 'спайс', 'мефедрон', 'амфетамин',
    'детский', 'ребёнок', 'ребенок', 'малолетний', 'несовершеннолетний', 'педофил', 'педофилия',
    'оружие', 'пистолет', 'автомат', 'взрывчатка', 'бомба', 'динамит', 'порох', 'кинжал'
]
