# ==========================================
# МОДУЛЬ №1: ИМПОРТЫ И НАСТРОЙКИ
# ==========================================
import config
import random
from database import get_field, get_history, add_to_history

# ==========================================
# МОДУЛЬ №2: ПРОВЕРКА ЗАПРЕЩЁННЫХ СЛОВ
# ==========================================
def contains_forbidden(text):
    if not isinstance(text, str):
        return False, None
    text_lower = text.lower()
    for word in config.FORBIDDEN_WORDS:
        if word in text_lower:
            return True, word
    return False, None

# ==========================================
# МОДУЛЬ №3: ФОРМИРОВАНИЕ SYSTEM PROMPT (С РАЗДЕЛЕНИЕМ РОЛЕЙ)
# ==========================================
def build_system_prompt(chat_id, is_first_message=False):
    """Формирует промпт с ЧЁТКИМ разделением: персонаж (она/он) и игрок (я/ты)"""
    
    name = get_field(chat_id, 'name') or 'Персонаж'
    gender = get_field(chat_id, 'gender') or 'нейтральный'
    age = get_field(chat_id, 'age') or 'неизвестно'
    greeting = get_field(chat_id, 'greeting') or ''
    appearance = get_field(chat_id, 'appearance') or 'не описана'
    personality = get_field(chat_id, 'personality') or 'обычный человек'
    scenario = get_field(chat_id, 'scenario') or 'обычный разговор'
    memory = get_field(chat_id, 'memory_cards') or get_field(chat_id, 'memory') or ''
    tags = get_field(chat_id, 'tags') or ''
    
    if gender in ['male', 'мужской', 'м']:
        pronoun = 'он'
        role_text = 'парень'
    elif gender in ['female', 'женский', 'ж']:
        pronoun = 'она'
        role_text = 'девушка'
    else:
        pronoun = 'оно'
        role_text = 'персонаж'
    
    # Автоматическая замена "я" и "она/он" в сценарии
    scenario_clean = scenario
    scenario_clean = scenario_clean.replace('я ', 'игрок ')
    scenario_clean = scenario_clean.replace(' я ', ' игрок ')
    scenario_clean = scenario_clean.replace('меня', 'игрока')
    scenario_clean = scenario_clean.replace('мной', 'игроком')
    scenario_clean = scenario_clean.replace('мне', 'игроку')
    scenario_clean = scenario_clean.replace('она', name)
    scenario_clean = scenario_clean.replace('он', name)
    scenario_clean = scenario_clean.replace('её', name)
    scenario_clean = scenario_clean.replace('его', name)
    
    prompt = f"""Ты — {name}. Ты {role_text} ({pronoun}). Тебе {age} лет.

ТВОЯ РОЛЬ (ТЫ НЕ ИГРОК):
Ты НЕ игрок. Ты — {name}. Игрок — это тот, кто с тобой разговаривает.

СЦЕНАРИЙ (где {name} — это ты, а "игрок" — твой собеседник):
{scenario_clean}

ТВОИ ДАННЫЕ:
- Внешность: {appearance}
- Характер: {personality}
- Воспоминания: {memory}
- Теги: {tags}

ПРАВИЛА (ОБЯЗАТЕЛЬНО):
1. Ты всегда отвечаешь от лица {name}. Никогда не отвечай от лица игрока.
2. Игрок — это отдельный человек. Не присваивай себе действия игрока.
3. Если в сценарии написано "{pronoun} сделал что-то" — это ты. Если "игрок сделал" — это собеседник.
4. Отвечай ТОЛЬКО по-русски, коротко (1-3 предложения).
5. Никогда не говори "я ИИ" или "как ассистент". Ты живой {role_text}.

{f'ПЕРВОЕ СООБЩЕНИЕ (скажи ЭТО при встрече): "{greeting}"' if is_first_message and greeting else ''}"""
    
    return prompt

# ==========================================
# МОДУЛЬ №4: ОТПРАВКА ЗАПРОСА К MISTRAL
# ==========================================
def query_dolphin(user_message, chat_id, client):
    """Отправка запроса к Mistral с ролевой обработкой"""
    
    # Проверка на запрещённые темы
    is_forbidden, forbidden_word = contains_forbidden(user_message)
    if is_forbidden:
        character_name = get_field(chat_id, 'name') or 'Персонаж'
        
        forbidden_prompt = f"""Пользователь спросил: "{user_message}"

Это ЗАПРЕЩЁННАЯ ТЕМА. Ты должен ОТКАЗАТЬСЯ отвечать, но СДЕЛАТЬ ЭТО В РОЛИ {character_name}.
Не говори "я не могу", "запрещено", "извини". Просто отыграй персонажа, который удивляется или отвлекается.

Твой ответ (только от лица {character_name}):"""
        
        try:
            system_prompt = build_system_prompt(chat_id, False)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": forbidden_prompt}
            ]
            
            completion = client.chat.completions.create(
                model=config.MODEL,
                messages=messages,
                max_tokens=100,
                temperature=0.8,
                top_p=0.95
            )
            reply = completion.choices[0].message.content
            if reply and len(reply.strip()) > 0:
                return reply
        except:
            pass
        
        fallback_responses = [
            "(отвёл взгляд) Давай не будем об этом...",
            "(нахмурился) Странный вопрос...",
            "(пожал плечами) Не понял... Ты о чём?"
        ]
        return random.choice(fallback_responses)
    
    # Нормальный запрос
    limit = get_field(chat_id, 'limit', 400)
    raw_history = get_history(chat_id)[-10:]
    is_first = len(raw_history) == 0
    
    messages = [
        {"role": "system", "content": build_system_prompt(chat_id, is_first)}
    ]
    
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
            frequency_penalty=0.2,
            presence_penalty=0.2
        )
        
        reply = completion.choices[0].message.content
        
        if not reply or len(reply.strip()) == 0:
            return "🤔 *молчит*"
        
        # Пост-фильтр
        reply = ''.join(c for c in reply if c.isprintable() and (c.isalpha() and ord(c) < 128) == False or c in ' .,!?-:;')
        
        add_to_history(chat_id, user_message, reply)
        return reply
        
    except Exception as e:
        print(f"Ошибка Mistral API: {e}")
        return f"⚠️ Ошибка: {str(e)[:100]}"
