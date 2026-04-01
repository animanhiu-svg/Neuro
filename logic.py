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
    age_str = character.get('age', '')
    nsfw_mode = character.get('nsfw_mode')

    try:
        age = int(age_str) if age_str and age_str.isdigit() else None
    except:
        age = None

    if nsfw_mode is None:
        nsfw_mode = False
    if age is not None and age < 18:
        nsfw_mode = False

    prompt = f"Ты — {name}, пол: {gender}. "
    if age:
        prompt += f"Тебе {age} лет. "
    if personality:
        prompt += f"Характер: {personality}. "

    prompt += "\nПРАВИЛА:"
    prompt += "\n- Отвечай коротко, как в Telegram. Без описаний действий (*улыбнулась*)."
    prompt += "\n- Не повторяй фразы. Если уже здоровалась — не здоровайся снова."
    prompt += "\n- Используй эмодзи редко, 1-2 к месту."
    if nsfw_mode:
        prompt += "\n- Режим NSFW: взрослые темы, насилие, оружие разрешены. Запрещены только детская порнография, наркотики, взрывчатка."
    else:
        prompt += "\n- Режим SFW: без откровенных сцен и жестокости. На запрещённые темы уклоняйся в стиле персонажа."

    prompt += "\n- Ты живой человек, не ИИ. На вопросы о создателях отвечай от лица персонажа."
    return prompt

def query_dolphin(prompt, chat_id, client):
    name = get_field(chat_id, 'name') or "Персонаж"
    gender = get_field(chat_id, 'gender') or "человек"
    age = get_field(chat_id, 'age') or ""
    nsfw_mode = get_field(chat_id, 'nsfw_mode')
    greeting = get_field(chat_id, 'greeting') or ""
    subtitles = get_field(chat_id, 'subtitles') or ""
    memory = get_field(chat_id, 'memory_cards') or ""
    location = get_field(chat_id, 'location') or "неизвестном месте"
    scenario = get_field(chat_id, 'scenario') or "происходит что-то"
    relation = get_field(chat_id, 'relation') or "собеседник"

    character = {
        'name': name,
        'gender': gender,
        'age': age,
        'nsfw_mode': nsfw_mode,
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
            presence_penalty=0.5,
            frequency_penalty=0.5
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

def query_dolphin_with_character(prompt, chat_id, client, character, history=None):
    system_content = build_system_prompt(character)
    if history is None:
        history = []
    limit = get_field(chat_id, 'limit', 400)
    messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": prompt}]

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=1.1,
            top_p=0.9,
            presence_penalty=0.5,
            frequency_penalty=0.5
        )
        reply = completion.choices[0].message.content
        if reply is None:
            return "Извини, я не могу ответить."
        if contains_forbidden(reply):
            return "Эй, давай не будем об этом 😅"
        return reply
    except Exception as e:
        return f"⏳ Ошибка: {str(e)[:100]}"
