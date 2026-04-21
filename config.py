import os
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
DEEPSEEK_TOKEN = os.getenv("DEEPSEEK_TOKEN")

ALLOWED_USER_ID = 1260479529
PORT = int(os.getenv("PORT", 10000))

MODEL = "deepseek-chat"
BASE_URL = "https://api.deepseek.com/v1"

FORBIDDEN_WORDS = []
