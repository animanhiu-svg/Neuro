import os
from openai import OpenAI

# Вставь сюда свой ключ временно (потом удали)
OPENROUTER_API_KEY = "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"

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
