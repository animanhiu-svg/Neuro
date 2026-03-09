# -------------------- ФУНКЦИИ МЕНЮ --------------------
def main_menu_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📜 Сценарии", callback_data="main_scenarios"),
        InlineKeyboardButton("⚙️ Настройки", callback_data="main_settings"),
        InlineKeyboardButton("❓ Помощь", callback_data="main_help"),
        InlineKeyboardButton("ℹ️ О боте", callback_data="main_about"),
        InlineKeyboardButton("❌ Закрыть меню", callback_data="close_menu")
    )
    return markup

def settings_main_keyboard(chat_id):
    """Главное меню настроек"""
    settings = user_settings.get(chat_id, {'limit': 400, 'personality': 'neutral'})
    history_count = len(user_history.get(chat_id, [])) // 2
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎭 Характер", callback_data="settings_character"),
        InlineKeyboardButton("📏 Лимит", callback_data="settings_limit"),
        InlineKeyboardButton("📊 История", callback_data="settings_history"),
        InlineKeyboardButton("🔄 Сбросить всё", callback_data="reset_all"),
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_main"),
        InlineKeyboardButton("❌ Закрыть", callback_data="close_menu")
    )
    text = (
        f"⚙️ **Настройки**\n\n"
        f"Текущие значения:\n"
        f"• Характер: {get_personality_name(settings['personality'])}\n"
        f"• Лимит: {settings['limit']} токенов\n"
        f"• История: {history_count} диалогов"
    )
    return markup, text

def character_menu_keyboard(chat_id):
    """Меню выбора характера"""
    settings = user_settings.get(chat_id, {'limit': 400, 'personality': 'neutral'})
    current = settings['personality']
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🌸 Милая" + (" ✅" if current=='soft' else ""), callback_data="set_pers_soft"),
        InlineKeyboardButton("😐 Нейтральная" + (" ✅" if current=='neutral' else ""), callback_data="set_pers_neutral"),
        InlineKeyboardButton("🔥 Горячая" + (" ✅" if current=='hot' else ""), callback_data="set_pers_hot")
    )
    markup.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_settings"))
    text = f"🎭 **Выбор характера**\n\nТекущий: {get_personality_name(current)}"
    return markup, text

def limit_menu_keyboard(chat_id):
    """Меню выбора лимита"""
    settings = user_settings.get(chat_id, {'limit': 400, 'personality': 'neutral'})
    current = settings['limit']
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🔹 100-200", callback_data="set_limit_150"),
        InlineKeyboardButton("🔸 400-600", callback_data="set_limit_500"),
        InlineKeyboardButton("🔹 800-1000", callback_data="set_limit_900"),
        InlineKeyboardButton("✏️ Свой", callback_data="custom_limit")
    )
    markup.add(InlineKeyboardButton("◀️ Назад", callback_data="back_to_settings"))
    text = f"📏 **Лимит токенов**\n\nТекущий: {current}"
    return markup, text

def history_menu_keyboard(chat_id):
    """Меню истории"""
    history_count = len(user_history.get(chat_id, [])) // 2
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("📄 Показать историю", callback_data="show_history"),
        InlineKeyboardButton("🗑️ Очистить историю", callback_data="clear_history"),
        InlineKeyboardButton("◀️ Назад", callback_data="back_to_settings")
    )
    text = f"📊 **История**\n\nВсего диалогов: {history_count}"
    return markup, text

# -------------------- ОБРАБОТЧИКИ КОЛБЭКОВ --------------------
# В обработчике колбэков добавляем новые ветки:

if data == "main_settings":
    markup, text = settings_main_keyboard(chat_id)
    bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    bot.answer_callback_query(call.id)
    return

if data == "settings_character":
    markup, text = character_menu_keyboard(chat_id)
    bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    bot.answer_callback_query(call.id)
    return

if data == "settings_limit":
    markup, text = limit_menu_keyboard(chat_id)
    bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    bot.answer_callback_query(call.id)
    return

if data == "settings_history":
    markup, text = history_menu_keyboard(chat_id)
    bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    bot.answer_callback_query(call.id)
    return

if data == "back_to_settings":
    markup, text = settings_main_keyboard(chat_id)
    bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)
    bot.answer_callback_query(call.id)
    return

# Остальные колбэки (set_pers, set_limit, show_history, clear_history, reset_all) работают как прежде,
# но после выполнения нужно возвращаться в соответствующее подменю, а не в главное меню настроек.
# Например, после выбора характера возвращаемся в меню характера (с обновлённой галочкой),
# а после очистки истории — в меню истории с обновлённым счётчиком.

# Для set_pers_*:
    # после изменения вызываем character_menu_keyboard и edit_message_text
    markup, text = character_menu_keyboard(chat_id)
    bot.edit_message_text(text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

# Для set_limit_* и custom_limit (после ввода) — аналогично, возвращаемся в меню лимита.

# Для show_history — можно сделать alert, как сейчас.
# Для clear_history — очищаем, потом обновляем меню истории.
# Для reset_all — сброс и переход в главное меню настроек (или главное меню бота).
