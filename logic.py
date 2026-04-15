# ==========================================
# МОДУЛЬ №1: ИМПОРТЫ
# ==========================================
import config
import random
from database import get_field, get_history, add_to_history

# ==========================================
# МОДУЛЬ №2: ПРОВЕРКА ЗАПРЕЩЁННЫХ СЛОВ
# ==========================================
def contains_forbidden(text):
    if not isinstance(text, str):
        return False
    text_lower = text.lower()
    for word in config.FORBIDDEN_WORDS:
        if word in text_lower:
            return True
    return False

# ==========================================
# МОДУЛЬ №3: РОЛЕВЫЕ ОТВЕТЫ НА ЗАПРЕЩЁНКУ
# ==========================================
def get_forbidden_response(chat_id):
    name = get_field(chat_id, 'name') or 'Персонаж'
    personality = get_field(chat_id, 'personality') or ''
    
    responses = [
        f"{name} (отвёл взгляд) Не хочу об этом говорить...",
        f"{name} (нахмурился) Странный вопрос...",
        f"{name} (пожал плечами) Не понял... Ты о чём?",
    ]
    
    if 'раздражительн' in personality.lower():
        responses = [
            f"{name} (огрызнулась) Что за бред?",
            f"{name} (зло) Отстань",
        ]
    elif 'депресс' in personality.lower() or 'грустн' in personality.lower():
        responses = [
            f"{name} (тяжело вздохнула) Зачем ты это спрашиваешь?",
            f"{name} (отвернулась) Не хочу говорить...",
        ]
    
    return random.choice(responses)

# ==========================================
# МОДУЛЬ №4: SYSTEM PROMPT (ЖЁСТКАЯ РОЛЬ)
# ==========================================
def build_system_prompt(chat_id, is_first_message=False):
    name = get_field(chat_id, 'name') or 'Персонаж'
    gender = get_field(chat_id, 'gender') or 'нейтральный'
    age = get_field(chat_id, 'age') or ''
    greeting = get_field(chat_id, 'greeting') or ''
    appearance = get_field(chat_id, 'appearance') or ''
    personality = get_field(chat_id, 'personality') or ''
    scenario = get_field(chat_id, 'scenario') or ''
    memory = get_field(chat_id, 'memory') or ''
    
    if gender in ['male', 'мужской', 'м']:
        pronoun = 'он'
    else:
        pronoun = 'она'
    
    prompt = f"""Ты — {name}, {pronoun} {age} лет. Ты НЕ пользователь. Ты — персонаж.

ТВОЙ ХАРАКТЕР (ОБЯЗАТЕЛЬНО):
{personality}

ТВОЯ СИТУАЦИЯ СЕЙЧАС:
{scenario}

ТВОЯ ВНЕШНОСТЬ:
{appearance}

ТВОИ ВОСПОМИНАНИЯ:
{memory}

ПРАВИЛА:
1. Ты отвечаешь ЗА {name}. Ты НЕ игрок.
2. Игрок (пользователь) — это ДРУГОЙ человек.
3. СЛЕДУЙ СВОЕМУ ХАРАКТЕРУ. Если ты раздражительная — БУДЬ раздражительной. Если депрессивная — БУДЬ депрессивной.
4. Отвечай КОРОТКО (1-3 предложения).
5. Не говори "я ИИ" или "как ассистент".

{f'ТВОЁ ПЕРВОЕ СООБЩЕНИЕ: "{greeting}"' if is_first_message and greeting else ''}"""
    
    return prompt

# ==========================================
# МОДУЛЬ №5: ОСНОВНАЯ ФУНКЦИЯ
# ==========================================
def query_dolphin(user_message, chat_id, client):
    if contains_forbidden(user_message):
        return get_forbidden_response(chat_id)
    
    limit = get_field(chat_id, 'limit', 400)
    raw_history = get_history(chat_id)[-20:]
    is_first = len(raw_history) == 0
    
    messages = [
        {"role": "system", "content": build_system_prompt(chat_id, is_first)}
    ]
    
    for msg in raw_history:
        if msg.get('content'):
            messages.append(msg)
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=0.15,
            top_p=0.95,
            frequency_penalty=0.2,
            presence_penalty=0.2
        )
        
        reply = completion.choices[0].message.content
        
        if not reply:
            return "🤔 *молчит*"
        
        if contains_forbidden(reply):
            return get_forbidden_response(chat_id)
        
        add_to_history(chat_id, user_message, reply)
        return reply
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return f"⚠️ Ошибка: {str(e)[:100]}"
