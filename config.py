import os
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")   # <--- ЭТОТ КЛЮЧ

ALLOWED_USER_ID = 1260479529
PORT = int(os.getenv("PORT", 8080))

MODEL = "meta-llama/llama-3.3-70b-instruct"
BASE_URL = "https://openrouter.ai/api/v1"

FORBIDDEN_WORDS = []
