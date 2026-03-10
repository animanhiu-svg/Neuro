import os
from dotenv import load_dotenv

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
HF_TOKEN = os.getenv("HF_TOKEN")

ALLOWED_USER_ID = 1260479529  # замени на свой
PORT = int(os.getenv("PORT", 10000))

MODEL = "dphn/Dolphin-Mistral-24B-Venice-Edition:featherless-ai"
BASE_URL = "https://router.huggingface.co/v1"

FORBIDDEN_WORDS = [
    "наркотик", "наркота", "героин", "кокаин", "метамфетамин", "спайс", "мефедрон", "амфетамин",
    "детский", "ребёнок", "ребенок", "малолетний", "несовершеннолетний", "педофил", "педофилия",
    "оружие", "пистолет", "автомат", "взрывчатка", "бомба", "динамит", "порох", "кинжал"
]
