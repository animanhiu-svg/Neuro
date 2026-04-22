import os
from openai import OpenAI

# Вставь сюда свой ключ временно (потом удали)
OPENROUTER_API_KEY = "sk-or-v1-твой_ключ_сюда"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    timeout=60
)

try:
    completion = client.chat.completions.create(
        model="google/gemma-3-27b-it:free",
        messages=[{"role": "user", "content": "Привет! Ответь одним словом."}],
        max_tokens=10,
        temperature=0.7
    )
    print("✅ ОТВЕТ ПОЛУЧЕН:", completion.choices[0].message.content)
except Exception as e:
    print("❌ ОШИБКА:", e)
