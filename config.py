import os
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

ALLOWED_USER_ID = 1260479529
PORT = int(os.getenv("PORT", 10000))

MODEL = "google/gemma-4-31b-it"
BASE_URL = "https://router.huggingface.co/v1"

FORBIDDEN_WORDS = []
