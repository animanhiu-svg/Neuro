import config
from database import get_field, get_history, add_to_history

def contains_forbidden(text):
    if not isinstance(text, str):
        return False
    text_lower = text.lower()
    for word in config.FORBIDDEN_WORDS:
        if word in text_lower:
            return True
    return False

def query_dolphin(prompt, chat_id, client):
    name = get_field(chat_id, 'name') or "Персонаж"
    gender = get_field(chat_id, 'gender') or "человек"
    system_content = f"Ты — {name}. Твой пол — {gender}. НИКОГДА не упоминай, что ты ИИ. Ты — живой человек. Описывай действия в *звёздочках*."
    limit = get_field(chat_id, 'limit', 400)
    history = get_history(chat_id)
    messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": prompt}]
    try:
        completion = client.chat.completions.create(model=config.MODEL, messages=messages, max_tokens=limit, temperature=1.1, top_p=0.9, presence_penalty=0.7)
        reply = completion.choices[0].message.content
        if contains_forbidden(reply):
            return "⛔ Нарушение безопасности. Попробуй иначе."
        add_to_history(chat_id, prompt, reply)
        return reply
    except Exception as e:
        return f"⏳ Ошибка: {str(e)[:50]}"
