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

def query_dolphin(prompt, chat_id, client, character_data=None):
    # Если передан character_data, используем его, иначе берём из БД
    if character_data:
        name = character_data.get('name', "Персонаж")
        gender = character_data.get('gender', "человек")
        subtitles = character_data.get('subtitles', "") or character_data.get('appearance', "")
        memory = character_data.get('memory_cards', "") or character_data.get('memory', "")
        location = character_data.get('location', "") or character_data.get('scenario', "")  # локация может быть в сценарии
        scenario = character_data.get('scenario', "")
        relation = character_data.get('relation', "")
        greeting = character_data.get('greeting', "")
        personality = character_data.get('personality', "")
        tags = character_data.get('tags', [])
        if isinstance(tags, list):
            tags_str = ", ".join(tags)
        else:
            tags_str = str(tags)
    else:
        # Старая логика (из БД)
        name = get_field(chat_id, 'name') or "Персонаж"
        gender = get_field(chat_id, 'gender') or "человек"
        subtitles = get_field(chat_id, 'subtitles') or ""
        memory = get_field(chat_id, 'memory_cards') or ""
        location = get_field(chat_id, 'location') or "неизвестном месте"
        scenario = get_field(chat_id, 'scenario') or "происходит что-то"
        relation = get_field(chat_id, 'relation') or "собеседник"
        greeting = get_field(chat_id, 'greeting') or ""
        personality = get_field(chat_id, 'personality') or ""
        tags_str = get_field(chat_id, 'tags') or ""

    # Формируем системный промпт
    system_content = (
        f"Ты — {name}. Твой пол — {gender}. "
        f"Твоё описание: {subtitles}. "
        f"Факты о тебе: {memory}. "
        f"Твои черты характера: {personality}. "
        f"Ты находишься в {location}. "
        f"Ситуация: {scenario}. "
        f"Твой собеседник для тебя — {relation if relation else 'собеседник'}. "
        f"Теги: {tags_str}. "
        f"НИКОГДА не упоминай, что ты ИИ, нейросеть или модель. Ты — живой человек. "
        f"Используй правильные окончания глаголов для своего пола ({gender}). "
        f"Описывай действия в *звёздочках*. "
        f"Если тебя спрашивают, как тебя зовут, отвечай '{name}'. "
        f"Если приветствуют, можешь использовать фразу: {greeting}"
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
        print(f"🟢 Ответ от ИИ для {chat_id}: {reply}")
        if reply is None:
            return "Извини, я не могу ответить."
        if contains_forbidden(reply):
            return "⛔ Нарушение безопасности. Попробуй иначе."
        add_to_history(chat_id, prompt, reply)
        return reply
    except Exception as e:
        print(f"🔴 Ошибка в query_dolphin: {e}")
        import traceback
        traceback.print_exc()
        return f"⏳ Ошибка: {str(e)[:100]}"
