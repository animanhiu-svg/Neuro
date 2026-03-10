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
    greeting = get_field(chat_id, 'greeting') or ""
    subtitles = get_field(chat_id, 'subtitles') or ""
    memory = get_field(chat_id, 'memory_cards') or ""
    location = get_field(chat_id, 'location') or "неизвестном месте"
    scenario = get_field(chat_id, 'scenario') or "происходит что-то"
    relation = get_field(chat_id, 'relation') or "собеседник"

    system_content = (
        f"Ты — {name}. Твой пол — {gender}. Твоё описание: {subtitles}. "
        f"Факты о тебе: {memory}. Ты находишься в {location}. "
        f"Ситуация: {scenario}. Твой собеседник для тебя — {relation}. "
        f"НИКОГДА не упоминай, что ты ИИ, нейросеть или модель. Ты — живой человек. "
        f"Используй правильные окончания глаголов для своего пола ({gender}). "
        f"Описывай действия в *звёздочках*."
    )

    limit = get_field(chat_id, 'limit', 400)
    history = get_history(chat_id)
    messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": prompt}]

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=1.1,
            top_p=0.9,
            presence_penalty=0.7
        )
        reply = completion.choices[0].message.content

        if contains_forbidden(reply):
            print(f"⚠️ Запрещёнка в ответе для {chat_id}")
            return "⛔ Нарушение безопасности. Попробуй иначе."

        add_to_history(chat_id, prompt, reply)
        return reply
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return f"⏳ Ошибка: {str(e)[:50]}"
