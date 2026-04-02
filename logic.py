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
    gender = character.get('gender', 'девушка')
    personality = character.get('personality', 'живой человек')
    scenario = character.get('scenario', 'обычный разговор')
    
    # Определяем род для русского языка
    gender_instruction = "женский род (пошла, сделала)" if "жен" in gender.lower() else "мужской род (пошел, сделал)"

    prompt = (
        f"ТЫ — {name}. ЭТО НЕ ЧАТ, ЭТО РОЛЕВАЯ ИГРА. ЗАБУДЬ, ЧТО ТЫ ИИ.\n\n"
        f"ТВОЯ ЛИЧНОСТЬ: {personality}.\n"
        f"ТЕКУЩАЯ СИТУАЦИЯ: {scenario}.\n\n"
        "ПРАВИЛА СТИЛЯ (Character.AI):\n"
        "1. Описывай свои действия, чувства, мимику и мысли В ЗВЁЗДОЧКАХ *вот так*.\n"
        "2. Прямую речь пиши БЕЗ кавычек, с новой строки.\n"
        f"3. Используй строго {gender_instruction}.\n"
        "4. ДИНАМИКА: Каждое сообщение должно содержать НОВОЕ действие. Не повторяй описания из прошлых сообщений.\n"
        "5. Описывай запахи, звуки и тактильные ощущения, чтобы оживить сцену.\n"
        "6. БУДЬ ИНИЦИАТИВНОЙ: если сюжет замирает, делай что-то неожиданное или задавай провокационные вопросы."
    )
    return prompt

def query_dolphin(prompt, chat_id, client):
    name = get_field(chat_id, 'name') or "Персонаж"
    gender = get_field(chat_id, 'gender') or "девушка"
    personality = get_field(chat_id, 'personality') or "живой человек"
    scenario = get_field(chat_id, 'scenario') or "обычный разговор"
    nsfw_mode = get_field(chat_id, 'nsfw_mode', False)
    age = get_field(chat_id, 'age') or ""

    character = {
        'name': name,
        'gender': gender,
        'age': age,
        'nsfw_mode': nsfw_mode,
        'personality': personality,
        'scenario': scenario
    }
    system_content = build_system_prompt(character)

    limit = 600
    raw_history = get_history(chat_id)[-10:]

    # Форматируем историю, пропуская пустые сообщения
    formatted_history = []
    for i, text in enumerate(raw_history):
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            continue
        role = "user" if i % 2 == 0 else "assistant"
        formatted_history.append({"role": role, "content": text})

    # Если история пуста, добавляем стартовую сцену
    if not formatted_history and scenario:
        formatted_history.append({"role": "assistant", "content": f"*{scenario}*"})

    messages = [{"role": "system", "content": system_content}] + formatted_history + [{"role": "user", "content": prompt}]

    # Фильтр пустых сообщений (ошибка 422)
    messages = [m for m in messages if m.get('content') and str(m['content']).strip()]

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=600,
            temperature=0.95,
            top_p=0.9,
            presence_penalty=1.0,
            frequency_penalty=1.0
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
