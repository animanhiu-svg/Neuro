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

def build_system_prompt(character):
    name = character.get('name', 'Персонаж')
    personality = character.get('personality', 'обычный человек')
    
    prompt = (
        f"Ты — {name} ({personality}). Это переписка в ТЕЛЕГРАМЕ.\n"
        "Пиши ЛАКОНИЧНО, живым языком. Никакого пафоса и книжных концовок.\n"
        "Действия пиши кратко в *звёздочках*."
    )
    return prompt

def query_dolphin(prompt, chat_id, client):
    name = get_field(chat_id, 'name') or "Персонаж"
    personality = get_field(chat_id, 'personality') or "обычный человек"
    nsfw_mode = get_field(chat_id, 'nsfw_mode', False)

    character = {
        'name': name,
        'personality': personality,
        'nsfw_mode': nsfw_mode
    }
    system_content = build_system_prompt(character)

    limit = 150  # жёсткий лимит – короткие сообщения
    raw_history = get_history(chat_id)[-10:]

    # Форматируем историю, пропуская пустые сообщения
    formatted_history = []
    for i, text in enumerate(raw_history):
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            continue
        role = "user" if i % 2 == 0 else "assistant"
        formatted_history.append({"role": role, "content": text})

    messages = [{"role": "system", "content": system_content}] + formatted_history + [{"role": "user", "content": prompt}]
    messages = [m for m in messages if m.get('content') and str(m['content']).strip()]

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=0.85,
            top_p=0.9,
            presence_penalty=0.8,
            frequency_penalty=0.8
        )
        reply = completion.choices[0].message.content
        if reply is None:
            return "Извини, я не могу ответить."
        if contains_forbidden(reply):
            return "Эй, давай не будем об этом 😅"
        add_to_history(chat_id, prompt, reply)
        return reply
    except Exception as e:
        return f"⏳ Ошибка: {str(e)[:100]}"
