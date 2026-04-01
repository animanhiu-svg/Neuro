import config
from database import add_to_history

def contains_forbidden(text):
    if not isinstance(text, str):
        return False
    text_lower = text.lower()
    for word in config.FORBIDDEN_WORDS:
        if word in text_lower:
            return True
    return False

def query_dolphin(prompt, chat_id, client):
    """Для бота – использует данные из БД (старый способ, но можно оставить)"""
    from database import get_field, get_history
    name = get_field(chat_id, 'name') or "Персонаж"
    gender = get_field(chat_id, 'gender') or "человек"
    personality = get_field(chat_id, 'personality') or ""
    scenario = get_field(chat_id, 'scenario') or ""
    age = get_field(chat_id, 'age') or ""
    nsfw_mode = get_field(chat_id, 'nsfw_mode')

    system_content = build_system_prompt({
        'name': name,
        'gender': gender,
        'age': age,
        'personality': personality,
        'scenario': scenario,
        'nsfw_mode': nsfw_mode
    })

    limit = 150
    history = get_history(chat_id)[-5:]
    messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": prompt}]

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=1.1,
            top_p=0.9,
            presence_penalty=0.7,
            frequency_penalty=0.7
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

def build_system_prompt(character):
    """Собирает системный промпт из данных, переданных из мини-аппа"""
    name = character.get('name', 'Персонаж')
    gender = character.get('gender', 'человек')
    personality = character.get('personality', '')
    scenario = character.get('scenario', '')
    age = character.get('age', '')
    nsfw_mode = character.get('nsfw_mode', False)

    prompt = (
        "ДИРЕКТИВА: Ты — живой человек, НЕ ИИ. Общайся короткими фразами (Telegram-стиль). "
        "Лимит — 300 символов, всегда завершай мысль. НИКОГДА не веди себя как ассистент.\n"
    )
    prompt += f"Имя: {name}. Пол: {gender}. "
    if age:
        prompt += f"Возраст: {age}. "
    if personality:
        prompt += f"Характер: {personality}. "
    if scenario:
        prompt += f"Сейчас происходит: {scenario}. "

    if nsfw_mode:
        prompt += "Режим NSFW: взрослые темы, насилие, оружие разрешены. "
    else:
        prompt += "Режим SFW: без откровенных сцен и жестокости. "

    prompt += (
        "Отвечай как в Telegram: кратко, без описаний действий (*улыбнулась*), используй эмодзи редко (1-2). "
        "Не повторяй фразы. Если уже здоровалась — не здоровайся снова. "
        "На вопросы о создателях отвечай от лица персонажа."
    )
    return prompt

def query_dolphin_with_character(prompt, chat_id, client, character, history=None):
    """Для мини-аппа – использует переданные данные персонажа напрямую"""
    system_content = build_system_prompt(character)
    if history is None:
        history = []
    history = history[-5:] if history else []
    limit = 150
    messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": prompt}]

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=1.1,
            top_p=0.9,
            presence_penalty=0.7,
            frequency_penalty=0.7
        )
        reply = completion.choices[0].message.content
        if reply is None:
            return "Извини, я не могу ответить."
        if contains_forbidden(reply):
            return "Эй, давай не будем об этом 😅"
        # Сохраняем историю в БД для бота (опционально)
        add_to_history(chat_id, prompt, reply)
        return reply
    except Exception as e:
        return f"⏳ Ошибка: {str(e)[:100]}"
