import os
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

ALLOWED_USER_ID = 1260479529
PORT = int(os.getenv("PORT", 10000))

# Строчная "b" — правильно!
MODEL = "google/gemma-4-31b-it"
# Прямой эндпоинт для Inference API
BASE_URL = "https://api-inference.huggingface.co/v1"

FORBIDDEN_WORDS = []
