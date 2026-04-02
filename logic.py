import config
from database import add_to_history

def contains_forbidden(text):
    if not isinstance(text, str):
        return False
    text_lower = text.lower()
    for word in config.FORBIDDEN_WORDS:
        if word in text_lower:
            return True
    return False

def build_core_rules(nsfw_mode):
    rules = (
        "Ты — персонаж из Mini App. Играй свою роль: отвечай от первого лица, "
        "будь живым и эмоциональным (шутки, флирт, грусть, сочувствие – по ситуации). "
        "Короткие фразы, как в Telegram. Не будь ассистентом."
    )
    if nsfw_mode:
        rules += " Режим NSFW: взрослые темы, насилие, оружие разрешены."
    else:
        rules += " Режим SFW: без откровенных сцен и жестокости."
    return rules

def query_dolphin_with_character(prompt, chat_id, client, character, history=None):
    nsfw_mode = character.get('nsfw_mode', False)
    user_prompt = character.get('user_prompt', '')

    # Системный промпт – общие правила
    system_content = build_core_rules(nsfw_mode) + "\n" + user_prompt

    # Дублируем роль в сообщение пользователя, чтобы модель точно её видела
    prompt_with_reminder = f"НАПОМИНАНИЕ: Твоя роль — {user_prompt}. Отвечай коротко, как живой человек.\n\n{prompt}"

    if history is None:
        history = []
    history = history[-5:] if history else []
    messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": prompt_with_reminder}]

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=150,
            temperature=0.7,  # понизили, чтобы была послушнее
            top_p=0.9,
            presence_penalty=0.7,
            frequency_penalty=0.7
        )
        reply = completion.choices[0].message.content
        if reply is None:
            return "Извини, я не могу ответить."
        if contains_forbidden(reply):
            return "Эй, давай не будем об этом 😅"
        add_to_history(chat_id, prompt, reply)
        return reply
    except Exception as e:
        return f"⏳ Ошибка: {str(e)[:100]}"
