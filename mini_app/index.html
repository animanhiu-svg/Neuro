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
    """Жёсткие правила из кода – задают стиль и поведение"""
    rules = (
        "ТЫ — РОЛЕВАЯ МОДЕЛЬ. Твоя задача: играть персонажа, а не быть ассистентом. "
        "Ты умеешь шутить, флиртовать, сочувствовать, грустить — в зависимости от сюжета и ситуации. "
        "Твои ответы — короткие, живые, в стиле Telegram. Лимит — 300 символов, всегда завершай мысль. "
        "Ты — живой человек, НЕ ИИ. НИКОГДА не говори, что ты нейросеть или модель. "
    )
    if nsfw_mode:
        rules += "Режим NSFW: взрослые темы, насилие, оружие разрешены. "
    else:
        rules += "Режим SFW: без откровенных сцен и жестокости. "
    return rules

def query_dolphin_with_character(prompt, chat_id, client, character, history=None):
    """
    character должен содержать:
      - 'nsfw_mode': bool
      - 'user_prompt': строка с описанием персонажа (имя, характер, сценарий и т.д.)
    """
    nsfw_mode = character.get('nsfw_mode', False)
    user_prompt = character.get('user_prompt', '')

    system_content = build_core_rules(nsfw_mode) + "\n" + user_prompt

    if history is None:
        history = []
    history = history[-5:] if history else []
    messages = [{"role": "system", "content": system_content}] + history + [{"role": "user", "content": prompt}]

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=150,
            temperature=1.1,
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
