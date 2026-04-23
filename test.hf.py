import requests

token = "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"  # твой токен
headers = {"Authorization": f"Bearer {token}"}

# Тест 1: проверка токена
response = requests.get("https://huggingface.co/api/whoami", headers=headers)
print("Статус токена:", response.status_code)
print("Ответ:", response.text)

# Тест 2: запрос к модели
if response.status_code == 200:
    print("\nПроверяем модель...")
    API_URL = "https://api-inference.huggingface.co/models/google/gemma-2-9b-it"
    response2 = requests.post(API_URL, headers=headers, json={"inputs": "Hello"})
    print("Статус модели:", response2.status_code)
    print("Ответ модели:", response2.text[:200])
