# logic.py
import config
from database import user_settings, get_history, add_to_history

# Системные промпты для характеров (если нет кастомного)
def get_system_prompt(personality):
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

# Проверка на запрещённые слова
def contains_forbidden(text):
    if not isinstance(text, str):
        return False
    text_lower = text.lower()
    for word in config.FORBIDDEN_WORDS:
        if word in text_lower:
            return True
    return False

# Основная функция запроса к модели
def query_dolphin(prompt, chat_id, client):
    # Получаем настройки пользователя
    settings = user_settings.get(chat_id, {})
    limit = settings.get('limit', 400)
    personality = settings.get('personality', 'neutral')
    custom_prompt = settings.get('custom_prompt')  # Вот он, твой кастомный промпт!

    # Определяем system content: если есть кастомный промпт — используем его, иначе — стандартный от характера
    if custom_prompt:
        system_content = custom_prompt
    else:
        system_content = get_system_prompt(personality)

    # Берём историю (последние 20 сообщений)
    history = get_history(chat_id)
    
    # Формируем сообщения для модели: сначала system (роль), потом история, потом текущий запрос
    messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": prompt}]

    # Температура в зависимости от характера (для кастомного промпта берём среднюю)
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

        # Проверка на запрещёнку в ответе
        if contains_forbidden(reply):
            print(f"⚠️ Запрещёнка в ответе для {chat_id}, отправляю заглушку")
            return "⛔ Бот обнаружил потенциальное нарушение. Попробуй изменить запрос."

        # Сохраняем в историю
        add_to_history(chat_id, prompt, reply)
        return reply
    except Exception as e:
        print(f"Ошибка API: {e}")
        return f"⏳ Ошибка: {str(e)[:50]}"
