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
# МОДУЛЬ №3: РОЛЕВОЙ ОТВЕТ НА ЗАПРЕЩЁНКУ
# ==========================================
def get_forbidden_response(chat_id):
    """Возвращает ответ в стиле персонажа, без тупого 'запрещено'"""
    name = get_field(chat_id, 'name') or 'Персонаж'
    personality = get_field(chat_id, 'personality') or ''
    
    # Базовые ролевые ответы
    responses = [
        f"{name} (отвёл взгляд) Не хочу об этом говорить...",
        f"{name} (нахмурился) Странный вопрос... Давай о другом",
        f"{name} (пожал плечами) Не понял... Ты о чём?",
        f"{name} (задумался) Ммм... Неинтересно мне это",
    ]
    
    # Если персонаж раздражительный
    if 'раздражительн' in personality.lower():
        responses = [
            f"{name} (огрызнулась) Что за бред? Не беси",
            f"{name} (зло) Отстань с такими вопросами",
        ]
    
    # Если персонаж грустный
    elif 'депресс' in personality.lower() or 'грустн' in personality.lower():
        responses = [
            f"{name} (тяжело вздохнула) Зачем ты спрашиваешь? Мне и так плохо...",
            f"{name} (отвернулась) Не хочу это обсуждать",
        ]
    
    return random.choice(responses)

# ==========================================
# МОДУЛЬ №4: SYSTEM PROMPT
# ==========================================
def build_system_prompt(chat_id, is_first_message=False):
    name = get_field(chat_id, 'name') or 'Персонаж'
    age = get_field(chat_id, 'age') or ''
    personality = get_field(chat_id, 'personality') or ''
    scenario = get_field(chat_id, 'scenario') or ''
    greeting = get_field(chat_id, 'greeting') or ''
    
    prompt = f"Ты — {name}, {age} лет. {personality}. {scenario}."
    
    if is_first_message and greeting:
        prompt += f" Начни с: \"{greeting}\""
    
    return prompt

# ==========================================
# МОДУЛЬ №5: ОСНОВНАЯ ФУНКЦИЯ
# ==========================================
def query_dolphin(user_message, chat_id, client):
    # Проверка на запрещёнку → ролевой ответ
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
        
        # Проверка ответа ИИ
        if contains_forbidden(reply):
            return get_forbidden_response(chat_id)
        
        add_to_history(chat_id, user_message, reply)
        return reply
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return f"⚠️ Ошибка: {str(e)[:100]}"
