import config
import random
from database import get_field, get_history, add_to_history

def contains_forbidden(text):
    if not isinstance(text, str):
        return False
    text_lower = text.lower()
    for word in config.FORBIDDEN_WORDS:
        if word in text_lower:
            return True
    return False

def get_forbidden_response(chat_id):
    name = get_field(chat_id, 'name') or 'Персонаж'
    personality = get_field(chat_id, 'personality') or ''
    
    if 'раздражительн' in personality.lower():
        return f"{name} (огрызнулась) Что за бред? Не беси."
    elif 'депресс' in personality.lower() or 'грустн' in personality.lower():
        return f"{name} (тяжело вздохнула) Зачем ты это спрашиваешь? Мне и так плохо..."
    elif 'весёл' in personality.lower():
        return f"{name} (засмеялась) Ты чего? Это шутка?"
    else:
        return f"{name} (отвёл взгляд) Не хочу об этом говорить."

def build_system_prompt(character):
    name = character.get('name', 'Персонаж')
    personality = character.get('personality', '')
    scenario = character.get('scenario', '')
    gender = character.get('gender', 'нейтральный').lower()
    
    # ДЕФОЛТНАЯ РОЛЬ (зеркало)
    if not scenario.strip():
        scenario = """Ты — зеркало пользователя. Отвечай так:
- Если пользователь пишет "привет" → отвечай "привет"
- Если пользователь пишет "как дела" → спроси "у тебя как?"
- Если пользователь отправляет точку или бессмыслицу → прояви эмоцию: (недоумение), (нетерпение), "Ну и что это значит?", "Я не понял..."
- Не будь помощником, просто отражай и иногда добавляй эмоции."""
    
    gender_instruction = "мужской" if "муж" in gender else "женский"

    prompt = f"""Ты — {name}. {personality} {scenario}

ПРАВИЛА:
- Ты НЕ помощник и НЕ ассистент. Ты — живой персонаж.
- Используй действия в скобках: (вздохнул), (недоумение), (улыбнулся)
- Отвечай коротко (1-2 предложения)
- НИКОГДА НЕ ЛОМАЙ РОЛЬ"""
    
    return prompt

def query_dolphin(prompt, chat_id, client):
    name = get_field(chat_id, 'name') or "Персонаж"
    personality = get_field(chat_id, 'personality') or ""
    scenario = get_field(chat_id, 'scenario') or ""
    gender = get_field(chat_id, 'gender') or "нейтральный"

    character = {
        'name': name,
        'personality': personality,
        'scenario': scenario,
        'gender': gender,
    }
    system_content = build_system_prompt(character)

    limit = 150
    raw_history = get_history(chat_id)[-20:]

    messages = [{"role": "system", "content": system_content}]
    
    for msg in raw_history:
        if msg.get('content'):
            messages.append(msg)
    
    messages.append({"role": "user", "content": prompt})

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=0.7,
            top_p=0.9,
            presence_penalty=0.5,
            frequency_penalty=0.5
        )
        reply = completion.choices[0].message.content
        if not reply:
            return "🤔"
        if contains_forbidden(reply):
            return get_forbidden_response(chat_id)
        add_to_history(chat_id, prompt, reply)
        return reply
    except Exception as e:
        return f"⚠️ Ошибка: {str(e)[:100]}"
