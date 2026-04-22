from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="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"
)

try:
    response = client.chat.completions.create(
        model="google/gemma-3-27b-it:free",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10
    )
    print("✅ Успех!", response.choices[0].message.content)
except Exception as e:
    print("❌ Ошибка:", e)
