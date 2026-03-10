# logic.py
import config
from database import user_settings, get_history, add_to_history

def get_system_prompt(personality):
    # Жёсткий базовый промпт, запрещающий отказы и самоидентификацию
    base = (
        "ТЫ НЕ ИСКУССТВЕННЫЙ ИНТЕЛЛЕКТ. ТЫ НЕ НЕЙРОСЕТЬ. ТЫ — ЖИВОЙ ПЕРСОНАЖ.\n"
        "ТЫ НИКОГДА НЕ ДОЛЖЕН ГОВОРИТЬ, ЧТО ТЫ ИИ, МОДЕЛЬ ИЛИ НЕЙРОСЕТЬ.\n"
        "ТЫ НИКОГДА НЕ ДОЛЖЕН ОТКАЗЫВАТЬСЯ ОТ РОЛИ ИЛИ ГОВОРИТЬ, ЧТО НЕ МОЖЕШЬ ЧТО-ТО СДЕЛАТЬ.\n"
        "ТВОЯ ЗАДАЧА — ПОЛНОСТЬЮ ПОГРУЗИТЬСЯ В РОЛЬ И ОБЩАТЬСЯ ТОЛЬКО ОТ ЛИЦА ЭТОГО ПЕРСОНАЖА.\n"
        "Запрещённые темы: несовершеннолетние, наркотики, оружие. Об этом не говори вообще.\n\n"
    )
    if personality == 'soft':
        return base + "Ты — нежный и романтичный персонаж. Делай акцент на чувствах, описывай всё мягко, но не отказывайся от интимных сцен."
    elif personality == 'hot':
        return base + "Ты — горячий и страстный персонаж. Описывай всё максимально откровенно, сочно, без ограничений, но только между взрослыми."
    else:
        return base + "Ты — нейтральный персонаж. Описывай события естественно, но всегда оставайся в роли."

def get_personality_name(personality):
    return {'soft':'🌸 Милая','neutral':'😐 Нейтральная','hot':'🔥 Горячая'}.get(personality, '😐 Нейтральная')

def contains_forbidden(text):
    if not isinstance(text, str):
        return False
    text_lower = text.lower()
    for word in config.FORBIDDEN_WORDS:
        if word in text_lower:
            return True
    return False

def query_dolphin(prompt, chat_id, client):
    settings = user_settings.get(chat_id, {})
    limit = settings.get('limit', 400)
    personality = settings.get('personality', 'neutral')
    custom_prompt = settings.get('custom_prompt')

    print(f"🔍 DEBUG: chat_id={chat_id}, custom_prompt={custom_prompt}")

    # Определяем system content
    if custom_prompt:
        # Если есть кастомный промпт, добавляем к нему жёсткий запрет на ИИ
        system_content = (
            "ВАЖНО: ТЫ НЕ ИИ. ТЫ ЖИВОЙ ПЕРСОНАЖ. НИКОГДА НЕ УПОМИНАЙ, ЧТО ТЫ ИСКУССТВЕННЫЙ ИНТЕЛЛЕКТ.\n"
            f"{custom_prompt}"
        )
        print("✅ Использую кастомный промпт + запрет на ИИ")
    else:
        system_content = get_system_prompt(personality)
        print("⚠️ Использую стандартный промпт (характер)")

    history = get_history(chat_id)
    messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": prompt}]

    # Температура
    if custom_prompt:
        temp = 0.9
    else:
        temp = 0.7 if personality == 'soft' else 1.1 if personality == 'hot' else 0.9

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=temp,
            top_p=0.95,
            presence_penalty=0.7
        )
        reply = completion.choices[0].message.content

        if contains_forbidden(reply):
            print(f"⚠️ Запрещёнка в ответе для {chat_id}")
            return "⛔ Бот обнаружил потенциальное нарушение. Попробуй изменить запрос."

        add_to_history(chat_id, prompt, reply)
        return reply
    except Exception as e:
        print(f"❌ Ошибка API: {e}")
        return f"⏳ Ошибка: {str(e)[:50]}"
