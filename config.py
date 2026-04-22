import os
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
OPENROUTER_TOKEN = os.getenv("OPENROUTER_TOKEN")  # ключ в Render, не в коде

ALLOWED_USER_ID = 1260479529
PORT = int(os.getenv("PORT", 10000))
MODEL = "inclusionai/ling-2.6-flash:free"
BASE_URL = "https://openrouter.ai/api/v1"
FORBIDDEN_WORDS = []
