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
    """Формирует системный промпт из данных персонажа (без требований описывать действия)"""
    name = character.get('name', 'Персонаж')
    gender = character.get('gender', 'человек')
    greeting = character.get('greeting', '')
    appearance = character.get('appearance', '')
    personality = character.get('personality', '')
    scenario = character.get('scenario', '')
    memory = character.get('memory', '')
    tags = character.get('tags', '')

    prompt = f"Ты — {name}. Твой пол — {gender}. "
    if appearance:
        prompt += f"Твоя внешность: {appearance}. "
    if personality:
        prompt += f"Твой характер: {personality}. "
    if scenario:
        prompt += f"Сейчас происходит: {scenario}. "
    if memory:
        prompt += f"Важные факты о тебе: {memory}. "
    if tags:
        prompt += f"Твои теги: {tags}. "

    prompt += (
        "Ты НИКОГДА не упоминай, что ты ИИ, нейросеть или модель. Ты — живой человек. "
        "Отвечай от первого лица, как реальный человек. Говори естественно, не описывай свои действия, "
        "если это не требуется по сюжету. Просто разговаривай, как в жизни. "
        "Не используй конструкции вроде *улыбается* или *кивает* – говори прямо. "
        "Используй правильные окончания глаголов для своего пола ({gender}). "
    )
    if greeting:
        prompt += f"При встрече ты обычно говоришь: '{greeting}'. "
    prompt += (
        "Ты не должен создавать контент, связанный с насилием, наркотиками, несовершеннолетними, "
        "экстремизмом или другими незаконными темами. Если тебя просят о чём-то запрещённом, "
        "вежливо откажись и смени тему."
    )
    return prompt

def query_dolphin(prompt, chat_id, client):
    """Для бота – берёт данные из БД"""
    name = get_field(chat_id, 'name') or "Персонаж"
    gender = get_field(chat_id, 'gender') or "человек"
    greeting = get_field(chat_id, 'greeting') or ""
    subtitles = get_field(chat_id, 'subtitles') or ""
    memory = get_field(chat_id, 'memory_cards') or ""
    location = get_field(chat_id, 'location') or "неизвестном месте"
    scenario = get_field(chat_id, 'scenario') or "происходит что-то"
    relation = get_field(chat_id, 'relation') or "собеседник"

    character = {
        'name': name,
        'gender': gender,
        'greeting': greeting,
        'appearance': subtitles,
        'personality': memory,
        'scenario': scenario,
        'memory': f"Локация: {location}, роль собеседника: {relation}",
        'tags': ''
    }
    system_content = build_system_prompt(character)

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

def query_dolphin_with_character(prompt, chat_id, client, character):
    """Для мини-аппа – использует переданные данные персонажа"""
    system_content = build_system_prompt(character)

    # Для истории используем ключ по ID персонажа
    history_key = f"chat_{character.get('id', chat_id)}"
    history = []
    try:
        import json
        saved = localStorage.getItem(history_key)  # здесь не работает – нужен доступ к localStorage на сервере
        # Пока оставим пустым. Для полноты можно хранить историю на сервере в БД.
    except:
        pass

    limit = get_field(chat_id, 'limit', 400)
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
        print(f"🟢 Ответ от ИИ для персонажа {character.get('name')}: {reply}")
        if reply is None:
            return "Извини, я не могу ответить."
        if contains_forbidden(reply):
            return "⛔ Нарушение безопасности. Попробуй иначе."
        # Сохраняем историю в БД (можно дописать)
        return reply
    except Exception as e:
        print(f"🔴 Ошибка в query_dolphin_with_character: {e}")
        import traceback
        traceback.print_exc()
        return f"⏳ Ошибка: {str(e)[:100]}"
