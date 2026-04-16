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
    personality = character.get('personality', '')
    scenario = character.get('scenario', '')
    
    if not scenario.strip():
        scenario = "обычный разговор"
    
    return f"Ты — {name}. {personality} {scenario}. Отвечай от лица {name}, следуя своему характеру. Коротко. Используй действия в скобках."

def query_dolphin(prompt, chat_id, client):
    name = get_field(chat_id, 'name')
    personality = get_field(chat_id, 'personality')
    scenario = get_field(chat_id, 'scenario')

    if not name:
        name = "Персонаж"
    if not personality:
        personality = ""
    if not scenario:
        scenario = "обычный разговор"

    character = {'name': name, 'personality': personality, 'scenario': scenario}
    system_content = build_system_prompt(character)

    raw_history = get_history(chat_id)[-20:]

    messages = [{"role": "system", "content": system_content}]
    for msg in raw_history:
        if msg.get('content'):
            messages.append(msg)
    messages.append({"role": "user", "content": prompt})

    try:
        completion = client.chat.completions.create(
            model=config.MODEL,
            messages=messages,
            max_tokens=250,
            temperature=0.8,
            top_p=0.9,
            presence_penalty=0.5,
            frequency_penalty=0.5
        )
        reply = completion.choices[0].message.content
        if not reply:
            return "🤔"
        if contains_forbidden(reply):
            return "😅 Давай не будем об этом."
        add_to_history(chat_id, prompt, reply)
        return reply
    except Exception as e:
        print(f"Ошибка: {e}")
        return "🌫️ Ошибка связи"
