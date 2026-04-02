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
    gender = character.get('gender', 'человек')
    personality = character.get('personality', '')
    scenario = character.get('scenario', '')
    age = character.get('age', '')
    nsfw_mode = character.get('nsfw_mode', False)

    prompt = (
        "Ты — живой человек, НЕ ИИ. Общайся короткими фразами (Telegram-стиль). "
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

def query_dolphin(prompt, chat_id, client):
    name = get_field(chat_id, 'name') or "Персонаж"
    gender = get_field(chat_id, 'gender') or "человек"
    age = get_field(chat_id, 'age') or ""
    nsfw_mode = get_field(chat_id, 'nsfw_mode')
    personality = get_field(chat_id, 'personality') or ""
    scenario = get_field(chat_id, 'scenario') or ""

    character = {
        'name': name,
        'gender': gender,
        'age': age,
        'nsfw_mode': nsfw_mode,
        'personality': personality,
        'scenario': scenario
    }
    system_content = build_system_prompt(character)

    limit = 150
    history = get_history(chat_id)[-5:]
    messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": prompt}]

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=0.7,
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
