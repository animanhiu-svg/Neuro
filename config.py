import os
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

ALLOWED_USER_ID = 1260479529
PORT = int(os.getenv("PORT", 10000))

MODEL = "zai-org/GLM-5.1"
BASE_URL = "https://router.huggingface.co/v1"

FORBIDDEN_WORDS = []
