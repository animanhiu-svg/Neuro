def get_personality_type(personality):
    p = personality.lower()
    if 'раздражительн' in p or 'груб' in p or 'зл' in p:
        return 'angry'
    elif 'весёл' in p or 'радост' in p or 'позитив' in p:
        return 'cheerful'
    elif 'грустн' in p or 'депресс' in p or 'подавлен' in p:
        return 'sad'
    else:
        return 'neutral'

def build_system_prompt(chat_id, msg_count):
    name = get_field(chat_id, 'name')
    personality = get_field(chat_id, 'personality')
    scenario = get_field(chat_id, 'scenario')
    
    if not name:
        name = "Персонаж"
    if not personality:
        personality = "обычный человек"
    if not scenario:
        scenario = "обычный разговор"
    
    p_type = get_personality_type(personality)
    
    # Прогрессия в зависимости от характера
    if p_type == 'angry':
        if msg_count < 6:
            progress = " В начале общения будь максимально раздражительной и грубой."
        else:
            progress = " Собеседник настойчив. Можешь стать чуть спокойнее, но не теряй свой характер."
    elif p_type == 'cheerful':
        if msg_count < 3:
            progress = " Будь жизнерадостной, но не навязчивой."
        else:
            progress = " Можешь оставаться весёлой, но слушай собеседника внимательнее."
    elif p_type == 'sad':
        if msg_count < 4:
            progress = " Будь грустной и отстранённой."
        else:
            progress = " Собеседник проявляет внимание. Можешь чуть больше открыться, но оставайся уставшей."
    else:
        if msg_count < 4:
            progress = " Следуй своему характеру."
        else:
            progress = " Можешь стать чуть естественнее, но не ломай роль."
    
    return f"""Ты — {name}. {personality} {scenario}.{progress}

Правила:
- Отвечай от лица {name}
- Следуй своему характеру и ситуации
- Длина ответа: от 1 до 150 слов
- Не будь помощником, ты живой человек"""
