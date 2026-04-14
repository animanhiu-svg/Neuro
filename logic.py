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

def build_system_prompt(chat_id, is_first_message=False):
    name = get_field(chat_id, 'name') or 'Персонаж'
    gender = get_field(chat_id, 'gender') or 'нейтральный'
    age = get_field(chat_id, 'age') or ''
    greeting = get_field(chat_id, 'greeting') or ''
    personality = get_field(chat_id, 'personality') or ''
    scenario = get_field(chat_id, 'scenario') or ''
    
    if gender in ['male', 'мужской', 'м']:
        pronoun = 'он'
    elif gender in ['female', 'женский', 'ж']:
        pronoun = 'она'
    else:
        pronoun = 'оно'
    
    prompt = f"{name} - {pronoun}, {age} лет.\n"
    if personality:
        prompt += f"Характер: {personality}\n"
    if scenario:
        prompt += f"Сейчас: {scenario}\n"
    prompt += "Отвечай кратко, по-русски, без цифр и символов. Ты живой персонаж."
    
    if is_first_message and greeting:
        prompt += f" Первая фраза: '{greeting}'"
    
    return prompt

def query_dolphin(user_message, chat_id, client):
    if contains_forbidden(user_message):
        return "😅 Давай не будем об этом."
    
    limit = get_field(chat_id, 'limit', 400)
    raw_history = get_history(chat_id)[-10:]
    is_first = len(raw_history) == 0
    
    messages = [{"role": "system", "content": build_system_prompt(chat_id, is_first)}]
    
    for msg in raw_history[-6:]:
        if msg.get('content') and str(msg['content']).strip():
            messages.append(msg)
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=0.15,
            top_p=0.95,
            presence_penalty=0.2,
            frequency_penalty=0.2
        )
        
        reply = completion.choices[0].message.content
        
        if not reply or len(reply.strip()) == 0:
            return "🤔 *молчит*"
        
        if contains_forbidden(reply):
            return "😅 Давай сменим тему."
        
        add_to_history(chat_id, user_message, reply)
        return reply
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return f"⚠️ Ошибка: {str(e)[:100]}"
