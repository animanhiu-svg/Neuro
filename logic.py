import config
import random
from database import get_field, get_history, add_to_history

def contains_forbidden(text):
    return False

def build_system_prompt(chat_id):
    name = get_field(chat_id, 'name')
    personality = get_field(chat_id, 'personality')
    scenario = get_field(chat_id, 'scenario')
    
    if not name:
        name = "Персонаж"
    if not personality:
        personality = "обычный человек"
    if not scenario:
        scenario = "обычный разговор"
    
    return f"""Ты — {name}. {personality} {scenario}

Правила:
- Отвечай от лица {name}
- Следуй своему характеру и ситуации
- Длина ответа: от 1 до 150 слов (коротко или чуть длиннее — по ситуации)
- Эмодзи используй изредка, не в каждом сообщении (1 эмодзи на 2-3 сообщения, если уместно)
- Не будь помощником, ты живой человек"""

def query_dolphin(prompt, chat_id, client):
    name = get_field(chat_id, 'name') or "Персонаж"
    
    # Напоминание имени
    prompt_with_name = f"{prompt}\n\n(Ты — {name}. Не забывай, кто ты.)"
    
    raw_history = get_history(chat_id)[-40:]
    messages = [{"role": "system", "content": build_system_prompt(chat_id)}]
    for msg in raw_history:
        if msg.get('content'):
            messages.append(msg)
    messages.append({"role": "user", "content": prompt_with_name})
    
    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=400,  # достаточно для 150 слов
            temperature=0.75,
            top_p=0.9
        )
        reply = completion.choices[0].message.content
        if not reply:
            return "..."
        add_to_history(chat_id, prompt, reply)
        return reply
    except Exception as e:
        print(f"Ошибка: {e}")
        return "Ошибка"
