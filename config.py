import os
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
HF_TOKEN = "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"

ALLOWED_USER_ID = 1260479529
PORT = int(os.getenv("PORT", 8080))

MODEL = "google/gemma-2-9b-it"
BASE_URL = "https://api-inference.huggingface.co/v1"

FORBIDDEN_WORDS = []
