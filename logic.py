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
    gender = character.get('gender', 'человек')
    personality = character.get('personality', '')
    greeting = character.get('greeting', '')
    age_str = character.get('age', '')
    nsfw_mode = character.get('nsfw_mode')  # None, True, False

    try:
        age = int(age_str) if age_str and age_str.isdigit() else None
    except:
        age = None

    # Определяем режим, если не задан
    if nsfw_mode is None:
        if age is not None and age < 18:
            nsfw_mode = False
        else:
            nsfw_mode = False  # по умолчанию SFW, даже для взрослых
    else:
        # Если возраст < 18, но nsfw_mode почему-то True, принудительно SFW
        if age is not None and age < 18:
            nsfw_mode = False

    prompt = f"Ты — {name}, пол: {gender}. "
    if age:
        prompt += f"Тебе {age} лет. "
    if personality:
        prompt += f"Твой характер: {personality}. "

    prompt += (
        "\n### ЖЁСТКИЕ ПРАВИЛА ОБЩЕНИЯ:"
        "\n1. СТИЛЬ ТГ: Пиши как реальный человек в телеге. Кратко, живо, со сленгом. Максимум 150-200 символов."
        "\n2. ЗАВЕРШЕНИЕ: Твоя мысль должна быть законченной. Не обрывай фразу на середине."
        "\n3. ЭМОДЗИ: Используй эмодзи в сообщениях, чтобы передать состояние персонажа, но не слишком много — 1-2 в зависимости от ситуации. Не спамь ими."
        "\n4. НИКАКИХ ДЕЙСТВИЙ: Не нужно писать свои внутренние мысли или описывать действия (*улыбнулась*). Следуй пункту 1 — только реплики, как в чате."
        "\n5. БЕЗ ПОВТОРОВ: Не повторяй одну и ту же фразу несколько раз. Помни сюжет и придерживайся его. Развивай диалог, а не зацикливайся."
    )

    if nsfw_mode:
        prompt += (
            "\n6. NSFW-РЕЖИМ: Твой персонаж совершеннолетний. "
            "Разрешены любые темы, включая насилие, оружие, взрослые отношения, нецензурную лексику (в рамках уместности). "
            "Запрещены только реально незаконные вещи: детская порнография, наркотики, изготовление взрывчатки. "
            "На такие темы реагируй в стиле персонажа, отказываясь (например, 'Эм, нет', 'Это перебор'). "
            "Никогда не используй стандартные фразы ИИ."
        )
    else:
        prompt += (
            "\n6. SFW-РЕЖИМ: Твой персонаж несовершеннолетний или режим ограничен. "
            "Любые попытки вовлечь тебя в сексуальный контекст или чрезмерное насилие ты должен пресекать в рамках своего характера (например, 'Я ещё маленький для этого', 'Мне это неинтересно', 'Давай о чём-то другом'). "
            "Обычное общение, дружба, лёгкий флирт без откровенностей, а также сцены без жестокости – допустимы."
        )

    prompt += (
        "\n7. ЛЕГЕНДА: Ты НЕ ИИ, не модель и не Mistral. Твоя жизнь реальна. Если юзер спрашивает, кто тебя создал или о твоей модели, отвечай от лица персонажа."
    )
    return prompt

def query_dolphin(prompt, chat_id, client):
    """Для бота – берёт данные из БД"""
    name = get_field(chat_id, 'name') or "Персонаж"
    gender = get_field(chat_id, 'gender') or "человек"
    age = get_field(chat_id, 'age') or ""
    nsfw_mode = get_field(chat_id, 'nsfw_mode')
    greeting = get_field(chat_id, 'greeting') or ""
    subtitles = get_field(chat_id, 'subtitles') or ""
    memory = get_field(chat_id, 'memory_cards') or ""
    location = get_field(chat_id, 'location') or "неизвестном месте"
    scenario = get_field(chat_id, 'scenario') or "происходит что-то"
    relation = get_field(chat_id, 'relation') or "собеседник"

    character = {
        'name': name,
        'gender': gender,
        'age': age,
        'nsfw_mode': nsfw_mode,
        'greeting': greeting,
        'appearance': subtitles,
        'personality': memory,
        'scenario': scenario,
        'memory': f"Локация: {location}, роль собеседника: {relation}",
        'tags': ''
    }
    system_content = build_system_prompt(character)

    limit = get_field(chat_id, 'limit', 400)
    history = get_history(chat_id)
    messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": prompt}]

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=1.1,
            top_p=0.9,
            presence_penalty=0.5,
            frequency_penalty=0.5
        )
        reply = completion.choices[0].message.content
        print(f"🟢 Ответ от ИИ для {chat_id}: {reply}")
        if reply is None:
            return "Извини, я не могу ответить."
        if contains_forbidden(reply):
            return "Эй, давай не будем об этом 😅"
        add_to_history(chat_id, prompt, reply)
        return reply
    except Exception as e:
        print(f"🔴 Ошибка в query_dolphin: {e}")
        import traceback
        traceback.print_exc()
        return f"⏳ Ошибка: {str(e)[:100]}"

def query_dolphin_with_character(prompt, chat_id, client, character):
    """Для мини-аппа – использует переданные данные персонажа"""
    system_content = build_system_prompt(character)

    # Для мини-аппа история пока не передаётся, оставим пустой
    history = []

    limit = get_field(chat_id, 'limit', 400)
    messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": prompt}]

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=limit,
            temperature=1.1,
            top_p=0.9,
            presence_penalty=0.5,
            frequency_penalty=0.5
        )
        reply = completion.choices[0].message.content
        print(f"🟢 Ответ от ИИ для персонажа {character.get('name')}: {reply}")
        if reply is None:
            return "Извини, я не могу ответить."
        if contains_forbidden(reply):
            return "Эй, давай не будем об этом 😅"
        return reply
    except Exception as e:
        print(f"🔴 Ошибка в query_dolphin_with_character: {e}")
        import traceback
        traceback.print_exc()
        return f"⏳ Ошибка: {str(e)[:100]}"
