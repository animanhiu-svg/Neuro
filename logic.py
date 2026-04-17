import config
from database import get_field, get_history, add_to_history

def contains_forbidden(text):
    return False

def build_system_prompt(chat_id, msg_count):
    name = get_field(chat_id, 'name') or "Персонаж"
    personality = get_field(chat_id, 'personality') or ""
    scenario = get_field(chat_id, 'scenario') or ""
    
    # Универсальная прогрессия (подходит для любого характера)
    if msg_count < 4:
        progress = "Начало общения. Держись в рамках своего характера, но пока не спеши сильно открываться."
    elif msg_count < 10:
        progress = "Собеседник продолжает разговор. Можешь стать чуть более естественной, но без резких изменений."
    else:
        progress = "Собеседник настойчив. Можешь немного смягчиться или открыться, но не ломай свой характер."
    
    return f"""Ты — {name}. {personality} {scenario}

{progress}

Правила:
- Отвечай от лица {name}
- Следуй своему характеру и ситуации
- Не будь помощником, ты живой человек"""

def query_dolphin(prompt, chat_id, client):
    raw_history = get_history(chat_id)[-40:]
    msg_count = len(raw_history)
    
    system_prompt = build_system_prompt(chat_id, msg_count)
    messages = [{"role": "system", "content": system_prompt}]
    
    for msg in raw_history:
        if msg.get('content'):
            messages.append(msg)
    messages.append({"role": "user", "content": prompt})
    
    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=300,
            temperature=0.8,
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
