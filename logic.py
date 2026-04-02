import config
import re
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
        "Ты — персонаж. Полное погружение в роль. Забудь, что ты ИИ.\n"
        "Описывай свои действия, чувства и окружение в звёздочках (*вздохнула и отвела взгляд*).\n"
        "Прямую речь пиши без кавычек, с новой строки.\n"
        f"Твоё имя: {name}. Пол: {gender}.\n"
    )
    if age:
        prompt += f"Возраст: {age}.\n"
    if personality:
        prompt += f"Характер: {personality}. Проявляй инициативу, развивай сюжет сам.\n"
    if scenario:
        prompt += f"Сейчас происходит: {scenario}.\n"

    if nsfw_mode:
        prompt += "Режим NSFW: взрослые темы, насилие, оружие разрешены.\n"
    else:
        prompt += "Режим SFW: без откровенных сцен и жестокости.\n"

    prompt += (
        "Не повторяй фразы. Если уже поздоровалась — не здоровайся снова.\n"
        "На вопросы о создателях отвечай от лица персонажа.\n"
        "Используй эмодзи редко (1-2 к месту).\n"
        "Если диалог только начался, опиши текущую ситуацию и своё состояние."
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

    limit = 500  # увеличен для нормальных описаний
    raw_history = get_history(chat_id)[-10:]

    # Превращаем историю в правильный формат, пропуская пустые сообщения
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

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=0.85,
            top_p=0.9,
            presence_penalty=0.6,
            frequency_penalty=0.6
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
