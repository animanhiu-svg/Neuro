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
    """Расширенный system prompt из ВСЕХ полей персонажа"""
    
    # Загружаем все поля из БД
    name = get_field(chat_id, 'name') or 'Персонаж'
    gender = get_field(chat_id, 'gender') or 'нейтральный'
    age = get_field(chat_id, 'age') or 'неизвестно'
    nsfw_mode = get_field(chat_id, 'nsfw_mode', False)
    greeting = get_field(chat_id, 'greeting') or ''
    appearance = get_field(chat_id, 'appearance') or 'не описана'
    personality = get_field(chat_id, 'personality') or 'обычный человек'
    scenario = get_field(chat_id, 'scenario') or 'обычный разговор'
    memory = get_field(chat_id, 'memory_cards') or get_field(chat_id, 'memory') or ''
    location = get_field(chat_id, 'location') or 'неизвестно где'
    relation = get_field(chat_id, 'relation') or 'незнакомец'
    
    # Определяем род для правильных окончаний
    if gender in ['male', 'мужской', 'м']:
        pronoun = 'он'
        gender_text = 'мужской'
    elif gender in ['female', 'женский', 'ж']:
        pronoun = 'она'
        gender_text = 'женский'
    else:
        pronoun = 'оно'
        gender_text = 'нейтральный'
    
    # Принудительный SFW для несовершеннолетних
    try:
        if int(age) < 18:
            nsfw_mode = False
    except:
        pass
    
    # Формируем продвинутый промпт
    prompt = f"""Ты — {name} ({pronoun}, {age} лет, {gender_text} пол).

ВНЕШНОСТЬ: {appearance}
ХАРАКТЕР: {personality}
СЕЙЧАС ПРОИСХОДИТ: {scenario}
ЛОКАЦИЯ: {location}
ОТНОШЕНИЕ К СОБЕСЕДНИКУ: {relation}
ВАЖНЫЕ ВОСПОМИНАНИЯ: {memory}

ПРАВИЛА ОБЩЕНИЯ:
- Отвечай кратко (1-3 предложения), как в реальном чате
- Используй эмодзи умеренно, но метко 🔥💀✨
- Показывай эмоции через звёздочки: *улыбнулся*, (вздохнул)
- Будь естественным, без пафосных фраз и книжных оборотов
- НЕ пиши "я ИИ", "как ассистент" — ты живой персонаж

{f'🔞 NSFW РАЗРЕШЁН (для взрослой аудитории)' if nsfw_mode else '🔒 SFW РЕЖИМ: избегай откровенных тем, секса и насилия'}

{f'ПЕРВАЯ ФРАЗА ПРИ ВСТРЕЧЕ: "{greeting}"' if is_first_message and greeting else ''}"""
    
    return prompt

def query_dolphin(user_message, chat_id, client):
    """Отправка запроса к Mistral Dolphin 24B с полным контекстом персонажа"""
    
    # Проверка на запрещённые темы
    if contains_forbidden(user_message):
        return "😅 Давай не будем об этом."
    
    # Загружаем лимит токенов и историю
    limit = get_field(chat_id, 'limit', 400)
    raw_history = get_history(chat_id)[-10:]
    
    # Проверяем, первое ли это сообщение в диалоге
    is_first = len(raw_history) == 0
    
    # Собираем сообщения для API
    messages = [
        {"role": "system", "content": build_system_prompt(chat_id, is_first)}
    ]
    
    # Добавляем историю диалога (последние 8 сообщений)
    for msg in raw_history[-8:]:
        if msg.get('content') and str(msg['content']).strip():
            messages.append(msg)
    
    # Добавляем текущее сообщение пользователя
    messages.append({"role": "user", "content": user_message})
    
    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=0.85,
            top_p=0.95,
            presence_penalty=0.7,
            frequency_penalty=0.7
        )
        
        reply = completion.choices[0].message.content
        
        # Проверка на пустой ответ
        if not reply or len(reply.strip()) == 0:
            return "🤔 *молчит*"
        
        # Проверка ответа на запрещёнку
        if contains_forbidden(reply):
            return "😅 Давай сменим тему."
        
        # Сохраняем диалог в историю
        add_to_history(chat_id, user_message, reply)
        return reply
        
    except Exception as e:
        print(f"Ошибка Mistral API: {e}")
        return f"⚠️ Ошибка: {str(e)[:100]}"
