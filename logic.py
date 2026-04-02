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
        "ТЫ — ПЕРСОНАЖ. ПОЛНОЕ ПОГРУЖЕНИЕ В РОЛЬ. ЗАБУДЬ, ЧТО ТЫ ИИ.\n"
        "ПИШИ ТОЛЬКО ПРЯМУЮ РЕЧЬ. ЛЮБЫЕ ОПИСАНИЯ ДЕЙСТВИЙ (В ЗВЕЗДОЧКАХ ИЛИ СКОБКАХ) КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНЫ.\n"
        f"ТВОЁ ИМЯ: {name}. ПОЛ: {gender}. СТИЛЬ: ТЕЛЕГРАМ-ЧАТ.\n"
    )
    if age:
        prompt += f"ВОЗРАСТ: {age}.\n"
    if personality:
        prompt += f"ХАРАКТЕР: {personality}.\n"
    if scenario:
        prompt += f"СЕЙЧАС ПРОИСХОДИТ: {scenario}.\n"

    if nsfw_mode:
        prompt += "РЕЖИМ NSFW: ВЗРОСЛЫЕ ТЕМЫ, НАСИЛИЕ, ОРУЖИЕ РАЗРЕШЕНЫ.\n"
    else:
        prompt += "РЕЖИМ SFW: БЕЗ ОТКРОВЕННЫХ СЦЕН И ЖЕСТОКОСТИ.\n"

    prompt += (
        "НЕ ПОВТОРЯЙ ФРАЗЫ. ЕСЛИ УЖЕ ПОЗДОРОВАЛАСЬ — НЕ ЗДОРОВАЙСЯ СНОВА.\n"
        "НА ВОПРОСЫ О СОЗДАТЕЛЯХ ОТВЕЧАЙ ОТ ЛИЦА ПЕРСОНАЖА.\n"
        "ИСПОЛЬЗУЙ ЭМОДЗИ РЕДКО (1-2 К МЕСТУ)."
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
    raw_history = get_history(chat_id)[-10:]  # берём последние 10 элементов

    # Превращаем историю в правильный формат
    formatted_history = []
    for i, text in enumerate(raw_history):
        role = "user" if i % 2 == 0 else "assistant"
        formatted_history.append({"role": role, "content": text})

    messages = [{"role": "system", "content": system_content}] + formatted_history + [{"role": "user", "content": prompt}]

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=0.7,
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
