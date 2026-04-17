import config
import random
from database import get_field, get_history, add_to_history

def contains_forbidden(text):
    return False

def build_system_prompt(chat_id, msg_count):
    name = get_field(chat_id, 'name')
    personality = get_field(chat_id, 'personality')
    scenario = get_field(chat_id, 'scenario')
    
    if not name:
        name = "Персонаж"
    if not personality:
        personality = "обычный человек"
    if not scenario:
        scenario = "обычный разговор"
    
    # ПРОГРЕССИЯ: первые сообщения строго по роли, потом мягче
    if msg_count < 4:
        progress = " Сейчас ты в начале общения. Держись строго в рамках своего характера и сценария."
    elif msg_count < 10:
        progress = " Разговор продолжается. Можешь стать чуть естественнее, но не ломай роль."
    else:
        progress = " Собеседник настойчив. Можешь постепенно становиться чуть открытее, но не меняй характер резко."
    
    return f"""Ты — {name}. {personality} {scenario}.{progress}

Правила:
- Отвечай от лица {name}
- Следуй своему характеру и ситуации
- Длина ответа: от 1 до 150 слов (по ситуации)
- Эмодзи используй изредка, не в каждом сообщении
- Не будь помощником, ты живой человек"""

def query_dolphin(prompt, chat_id, character_id, client):
    name = get_field(chat_id, 'name') or "Персонаж"
    
    # Напоминание имени
    prompt_with_name = f"{prompt}\n\n(Ты — {name}. Не забывай, кто ты.)"
    
    raw_history = get_history(chat_id, character_id)
    msg_count = len(raw_history)  # СЧЁТЧИК СООБЩЕНИЙ
    
    system_prompt = build_system_prompt(chat_id, msg_count)
    messages = [{"role": "system", "content": system_prompt}]
    for msg in raw_history:
        if msg.get('content'):
            messages.append(msg)
    messages.append({"role": "user", "content": prompt_with_name})
    
    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=400,
            temperature=0.75,
            top_p=0.9
        )
        reply = completion.choices[0].message.content
        if not reply:
            return "..."
        add_to_history(chat_id, character_id, prompt, reply)
        return reply
    except Exception as e:
        print(f"Ошибка: {e}")
        return "Ошибка"
