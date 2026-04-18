from database import get_field

def build_system_prompt(chat_id: int, character_id: int) -> str:
    name = get_field(chat_id, character_id, 'name') or "Персонаж"
    personality = get_field(chat_id, character_id, 'personality') or ""
    scenario = get_field(chat_id, character_id, 'scenario') or "обычный разговор"
    greeting = get_field(chat_id, character_id, 'greeting') or ""
    appearance = get_field(chat_id, character_id, 'appearance') or ""
    memory = get_field(chat_id, character_id, 'memory') or ""

    prompt = f"""Ты — {name}. {personality}
Сейчас происходит: {scenario}
Внешность: {appearance}
Память: {memory}
Приветствие: {greeting}

Правила:
- Строго следуй своему характеру и сценарию.
- Отвечай от лица {name}.
- Не ломай роль. Ты не ассистент, не языковая модель.
- Используй приветствие, если это начало диалога.
- Учитывай обстоятельства из сценария и память."""
    return prompt

def query_dolphin(prompt, chat_id, character_id, client):
    history = get_history(chat_id, character_id, limit=60)  # последние 60 сообщений
    system = build_system_prompt(chat_id, character_id)
    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    # ... вызов LLM (остаётся без изменений)
    # После получения ответа:
    add_to_history(chat_id, character_id, prompt, reply)
    return reply
