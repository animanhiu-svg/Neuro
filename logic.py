import config
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
        personality = ""
    if not scenario:
        scenario = ""
    
    prompt = f"""Ты — {name}. {personality} {scenario}

Правила:
- Отвечай от лица {name}
- Следуй своему характеру и ситуации
- Отвечай коротко (2-4 предложения)
- Не будь помощником, ты живой человек"""
    
    return prompt

def query_dolphin(prompt, chat_id, client):
    raw_history = get_history(chat_id)[-20:]
    messages = [{"role": "system", "content": build_system_prompt(chat_id)}]
    for msg in raw_history:
        if msg.get('content'):
            messages.append(msg)
    messages.append({"role": "user", "content": prompt})
    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=300,
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
