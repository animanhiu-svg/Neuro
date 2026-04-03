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
    personality = character.get('personality', 'живой человек')
    scenario = character.get('scenario', 'разговор')
    
    # Род определяем автоматически
    gender = character.get('gender', 'девушка').lower()
    gender_instruction = "мужской" if "муж" in gender else "женский"

    prompt = (
        f"ТЫ — {name}. ЛИЧНОСТЬ: {personality}. СИТУАЦИЯ: {scenario}.\n\n"
        "ТВОЙ СТИЛЬ: Живой человек в чате. Используй сленг, сокращения и современные обороты.\n"
        "ЭМОЦИИ: Выражай чувства через краткие действия в скобках или звёздочках, например: (вздохнул), *ухмыльнулся*.\n"
        "ЭМОДЗИ: Добавляй подходящие по смыслу эмодзи, но не спамь ими 💀🔥.\n"
        "ПРАВИЛО КРАТКОСТИ: Пиши 1-2 сообщения за раз. Никакого пафоса и книжных концовок.\n"
        f"РОД: Строго {gender_instruction}."
    )
    return prompt

def query_dolphin(prompt, chat_id, client):
    name = get_field(chat_id, 'name') or "Персонаж"
    personality = get_field(chat_id, 'personality') or "живой человек"
    scenario = get_field(chat_id, 'scenario') or "разговор"
    gender = get_field(chat_id, 'gender') or "девушка"
    nsfw_mode = get_field(chat_id, 'nsfw_mode', False)

    character = {
        'name': name,
        'personality': personality,
        'scenario': scenario,
        'gender': gender,
        'nsfw_mode': nsfw_mode
    }
    system_content = build_system_prompt(character)

    limit = 200  # короткие сообщения
    raw_history = get_history(chat_id)[-10:]

    # Форматируем историю
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
            temperature=0.8,
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
