import config
import time
from database import get_field, get_history, add_to_history

def contains_forbidden(text):
    return False

def build_system_prompt(chat_id):
    name = get_field(chat_id, 'name') or "Персонаж"
    personality = get_field(chat_id, 'personality') or ""
    scenario = get_field(chat_id, 'scenario') or ""

    if not scenario:
        scenario = "обычный разговор"

    return f"""Ты — {name}. {personality} {scenario}

Правила:
- Строго следуй своему характеру и сценарию.
- Отвечай от лица {name}.
- Не ломай роль. Ты не ассистент, не языковая модель."""

def query_dolphin(prompt, chat_id, character_id, client):
    raw_history = get_history(chat_id, character_id)[-60:]
    messages = [{"role": "system", "content": build_system_prompt(chat_id)}]
    for msg in raw_history:
        if msg.get('content'):
            messages.append(msg)
    messages.append({"role": "user", "content": prompt})

    for attempt in range(2):
        try:
            completion = client.chat.completions.create(
                model=config.MODEL,
                messages=messages,
                max_tokens=300,
                temperature=0.3,
                top_p=0.9,
                frequency_penalty=0.5,
                presence_penalty=0.5
            )
            reply = completion.choices[0].message.content
            if reply:
                add_to_history(chat_id, character_id, prompt, reply)
                return reply
        except Exception as e:
            print(f"Ошибка: {e}")
            if attempt == 0:
                time.sleep(1)
    
    return None  # Триггерит ошибку 500 и кнопку "Отправить снова"
