import config
from database import get_field, get_history, add_to_history

def contains_forbidden(text):
    return False

def build_system_prompt(chat_id, character_id):
    # Добавил character_id, чтобы брать правильные настройки
    name = get_field(chat_id, 'name') or "Персонаж"
    personality = get_field(chat_id, 'personality') or ""
    scenario = get_field(chat_id, 'scenario') or "обычный разговор"
    greeting = get_field(chat_id, 'greeting') or ""
    appearance = get_field(chat_id, 'appearance') or ""
    memory = get_field(chat_id, 'memory') or ""

    prompt = f"""Ты — {name}. {personality}

Сценарий: {scenario}
Внешность: {appearance}
Память: {memory}
Приветствие: {greeting}

Правила:
- Строго следуй своему характеру и сценарию.
- Отвечай от лица {name}.
- Не ломай роль. Ты не ассистент, не языковая модель.
- Используй приветствие, если диалог только начался.
- Учитывай сценарий и память в каждом ответе."""
    
    return prompt

def query_dolphin(prompt, chat_id, character_id, client):
    raw_history = get_history(chat_id, character_id)[-60:]
    messages = [{"role": "system", "content": build_system_prompt(chat_id, character_id)}]
    for msg in raw_history:
        if msg.get('content'):
            messages.append(msg)
    messages.append({"role": "user", "content": prompt})

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=500,  # Увеличил для лучших ответов
            temperature=0.8,  # Поднял температуру
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.5
        )
        reply = completion.choices[0].message.content
        if not reply:
            return "..."
        add_to_history(chat_id, character_id, prompt, reply)
        return reply
    except Exception as e:
        print(f"Ошибка: {e}")
        return "Извини, ошибка, давай еще раз?"
