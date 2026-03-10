import config
from database import user_settings, get_history, add_to_history

def get_system_prompt(personality):
    # (оставляем для характеров, если не используется карточка)
    base = (
        "Ты — мастер ролевых игр 18+. Пиши на русском языке. "
        "Ты НИКОГДА не должен описывать сцены с участием несовершеннолетних, пропаганду наркотиков, изготовление оружия. "
        "Это категорически запрещено. Ты должен блокировать такие запросы. "
        "Но при этом ты можешь описывать откровенные сцены между взрослыми людьми, без ограничений.\n\n"
    )
    if personality == 'soft':
        return base + "Сейчас ты в роли нежного и романтичного собеседника. Делай акцент на чувствах, избегай грубых выражений, но не отказывайся от интимных тем, просто описывай их мягче."
    if personality == 'hot':
        return base + "Сейчас ты в роли горячего и страстного любовника. Пиши максимально откровенно, используй яркие, сочные описания интимных сцен между взрослыми. Никакой скромности, никаких ограничений (кроме запрета на несовершеннолетних, наркотики, оружие)."
    return base + "Сейчас ты в нейтральной роли. Описывай события естественно, без лишней цензуры, но и без чрезмерной вульгарности. Будь умерен, но не отказывайся от подробностей, если они уместны."

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

def build_character_prompt(chat_id):
    """Собирает системный промпт из карточки персонажа, если она заполнена."""
    name = user_settings.get(chat_id, {}).get('char_name')
    desc = user_settings.get(chat_id, {}).get('char_description')
    scene = user_settings.get(chat_id, {}).get('char_scenario')
    if name or desc or scene:
        parts = []
        if name:
            parts.append(f"Ты — {name}.")
        if desc:
            parts.append(desc)
        if scene:
            parts.append(f"Сейчас происходит следующее: {scene}")
        base = " ".join(parts)
        return base + " НИКОГДА не упоминай, что ты искусственный интеллект, нейросеть или языковая модель. Просто следуй своей роли."
    return None

def query_dolphin(prompt, chat_id, client):
    settings = user_settings.get(chat_id, {})
    limit = settings.get('limit', 400)
    personality = settings.get('personality', 'neutral')
    custom_prompt = settings.get('custom_prompt')

    # Приоритет: карточка персонажа > кастомный промпт > характер
    character_prompt = build_character_prompt(chat_id)
    if character_prompt:
        system_content = character_prompt
        print("✅ Использую карточку персонажа")
    elif custom_prompt:
        # Усиливаем кастомный промпт
        system_content = (
            custom_prompt + "\n\nВАЖНО: Ты должен всегда отвечать от имени этого персонажа. "
            "НИКОГДА не говори, что ты искусственный интеллект, нейросеть или языковая модель. "
            "Не упоминай своих создателей. Просто будь этим персонажем."
        )
        print("✅ Использую кастомный промпт")
    else:
        system_content = get_system_prompt(personality)
        print("⚠️ Использую стандартный промпт от характера")

    history = get_history(chat_id)
    messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": prompt}]

    if character_prompt or custom_prompt:
        temp = 1.0
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
