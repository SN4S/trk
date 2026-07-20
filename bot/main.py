import os

from dotenv import load_dotenv
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, BotCommand
)
from telegram.ext import (
    Application, CommandHandler, ContextTypes, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)
from telegram.error import BadRequest

from database.models import init_engine, create_tables
from database import service

THEME, MESSAGE, CONFIRM, ADDINFO, ADDINFO_PICK, ADDINFO_CONFIRM = range(6)

def _status_ua(status) -> str:
    val = status.value if hasattr(status, "value") else status
    if val == "open":
        return "Відкритий"
    elif val == "pending":
        return "В очікуванні"
    elif val == "closed":
        return "Закритий"
    return str(val)

# Cached at startup — avoids a Telegram API call on every ticket send
_bot_username: str = ""

# Persistent main keyboard — shown only in private chats
MY_TICKETS_BTN = "📋 Мої тікети"
MAIN_KB = ReplyKeyboardMarkup(
    [[KeyboardButton(MY_TICKETS_BTN)]],
    resize_keyboard=True,
    is_persistent=True,
)
MY_TICKETS_FILTER = filters.TEXT & filters.Regex(f"^{MY_TICKETS_BTN}$") & filters.ChatType.PRIVATE

# Keyboard shown while waiting for text input in private chats
CANCEL_BTN = "❌ Скасувати"
CANCEL_KB = ReplyKeyboardMarkup(
    [[KeyboardButton(CANCEL_BTN)]],
    resize_keyboard=True,
    one_time_keyboard=False,
)


async def _remove_keyboard(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    try:
        ghost = await context.bot.send_message(chat_id, "\u200b", reply_markup=ReplyKeyboardRemove())
        await ghost.delete()
    except BadRequest:
        pass

async def _restore_main_kb(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> None:
    await context.bot.send_message(chat_id, text, reply_markup=MAIN_KB)

async def _finish(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str) -> None:
    prompt_msg_id = context.user_data.get("prompt_msg_id")
    if prompt_msg_id:
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=prompt_msg_id)
        except BadRequest:
            pass

    bot_msg_id = context.user_data.get("bot_msg_id")
    chat = await context.bot.get_chat(chat_id)
    if chat.type != "private":
        if bot_msg_id:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=bot_msg_id)
            except BadRequest:
                pass
        if text:
            await context.bot.send_message(chat_id, text)
        return

    if bot_msg_id:
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=bot_msg_id, text=text)
        except BadRequest:
            pass
        await _restore_main_kb(context, chat_id, "Головне меню")
    else:
        await _restore_main_kb(context, chat_id, text)


async def step(update, context, text, markup=None):
    chat_id = update.effective_chat.id
    prev_id = context.user_data.get("bot_msg_id")
    if prev_id:
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=prev_id, text=text, reply_markup=markup)
            return
        except BadRequest:
            pass
    msg = await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=markup)
    context.user_data["bot_msg_id"] = msg.message_id

async def delete_user_msg(update):
    try:
        if update.message:
            await update.message.delete()
    except BadRequest:
        pass

async def post_support_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎫 Звернутись у підтримку", callback_data="create_ticket")]
    ])
    await context.bot.send_message(
        chat.id, 
        "Натисніть кнопку нижче, щоб звернутись у підтримку:", 
        reply_markup=kb
    )


async def support_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if update.message:
        await delete_user_msg(update)
    if chat.type == "private":
        if update.message:
            await update.message.reply_text("Ця команда працює лише в групах. В приватних повідомленнях використовуйте /start.")
        elif update.callback_query:
            await update.callback_query.answer("Ця кнопка працює лише в групах.", show_alert=True)
        return ConversationHandler.END

    group_chat_id = chat.id
    context.user_data.clear()
    context.user_data["group_chat_id"] = group_chat_id
    context.user_data["group_title"] = chat.title

    themes = await service.get_themes()
    if not themes:
        if update.message:
            await update.message.reply_text("Теми звернень не налаштовані.")
        elif update.callback_query:
            await update.callback_query.answer("Теми звернень не налаштовані.", show_alert=True)
        return ConversationHandler.END

    kb = [[InlineKeyboardButton(t.name, callback_data=f"theme_{t.id}")] for t in themes]
    kb.append([InlineKeyboardButton("❌ Скасувати", callback_data="cancel_cmd")])
    
    text = f"@{update.effective_user.username or update.effective_user.first_name}, оберіть тему звернення:"
    if update.callback_query:
        await update.callback_query.answer()
        msg = await context.bot.send_message(chat.id, text, reply_markup=InlineKeyboardMarkup(kb))
        context.user_data["bot_msg_id"] = msg.message_id
    else:
        await step(update, context, text, InlineKeyboardMarkup(kb))
    return THEME

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    is_private = update.effective_chat.type == "private"

    if not args:
        if is_private:
            await update.message.reply_text(
                "Вітаємо! Використайте команду /support у вашій групі, "
                "або перегляньте свої тікети нижче.",
                reply_markup=MAIN_KB,
            )
        else:
            await update.message.reply_text(
                "Вітаємо! Використайте команду /support, щоб звернутись у підтримку в цій групі."
            )
        return ConversationHandler.END

    if args[0].startswith("addinfo_"):
        ticket_num = args[0].split("_", 1)[1]
        ticket = await service.get_ticket_by_num(ticket_num)
        if not ticket:
            await update.message.reply_text("Тікет не знайдено.", reply_markup=MAIN_KB if is_private else None)
            return ConversationHandler.END
        context.user_data.clear()
        context.user_data["addinfo_id"] = ticket.id
        context.user_data["addinfo_num"] = ticket.ticket_num
        msg = await update.message.reply_text(
            f"Введіть додаткову інформацію по тікету {ticket.ticket_num}:",
            reply_markup=CANCEL_KB,
        )
        context.user_data["prompt_msg_id"] = msg.message_id
        return ADDINFO

    if not args[0].startswith("support_"):
        await update.message.reply_text(
            "Використайте команду /support у вашій групі.",
            reply_markup=MAIN_KB if is_private else None,
        )
        return ConversationHandler.END

    group_chat_id = int(args[0].split("_", 1)[1])
    context.user_data.clear()
    context.user_data["group_chat_id"] = group_chat_id
    try:
        chat = await context.bot.get_chat(group_chat_id)
        context.user_data["group_title"] = chat.title
    except BadRequest:
        context.user_data["group_title"] = str(group_chat_id)

    themes = await service.get_themes()
    if not themes:
        await update.message.reply_text("Теми звернень не налаштовані.")
        return ConversationHandler.END

    kb = [[InlineKeyboardButton(t.name, callback_data=f"theme_{t.id}")] for t in themes]
    await step(update, context, "Оберіть тему звернення:", InlineKeyboardMarkup(kb))
    return THEME

async def get_addinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == CANCEL_BTN:
        return await cancel_cmd(update, context)

    ticket_id = context.user_data["addinfo_id"]
    ticket_num = context.user_data["addinfo_num"]
    reply_to_tg_msg_id = context.user_data.get("reply_to_tg_msg_id")

    reply_text = update.message.text
    context.user_data["reply_message"] = reply_text
    
    await delete_user_msg(update)

    reply_to_reply_id = context.user_data.get("reply_to_reply_id")
    if reply_to_tg_msg_id and not reply_to_reply_id:
        reply = await service.get_reply_by_tg_message_id(reply_to_tg_msg_id, ticket_id)
        if reply:
            reply_to_reply_id = reply.id
            
    if not reply_to_reply_id and update.message.reply_to_message:
        reply = await service.get_reply_by_tg_message_id(update.message.reply_to_message.message_id, ticket_id)
        if reply:
            reply_to_reply_id = reply.id
            reply_to_tg_msg_id = update.message.reply_to_message.message_id
            
    context.user_data["reply_to_reply_id"] = reply_to_reply_id
    context.user_data["reply_to_tg_msg_id"] = reply_to_tg_msg_id

    prompt_msg_id = context.user_data.get("prompt_msg_id")
    if prompt_msg_id:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_msg_id)
        except BadRequest:
            pass
        context.user_data["prompt_msg_id"] = None

    if update.effective_chat.type == "private":
        await _remove_keyboard(context, update.effective_chat.id)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Відправити", callback_data="send_reply")],
        [InlineKeyboardButton("Редагувати", callback_data="edit_reply")],
        [InlineKeyboardButton("Скасувати", callback_data="cancel_cmd")],
    ])

    text = (
        f"Додаткова інформація до тікету #{ticket_num}\n\n"
        f"Повідомлення: {reply_text}\n\n"
        f"Відправити?"
    )
    if update.effective_chat.type != "private":
        text = f"@{update.effective_user.username or update.effective_user.first_name}, {text}"

    await step(update, context, text, kb)
    return ADDINFO_CONFIRM

async def edit_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    text = "Введіть новий текст додаткової інформації:"
    if q.message.chat.type != "private":
        text = f"@{update.effective_user.username or update.effective_user.first_name}, {text}"
        cancel_inline = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Скасувати", callback_data="cancel_cmd")]])
        msg = await context.bot.send_message(q.message.chat_id, text, reply_markup=cancel_inline)
    else:
        msg = await context.bot.send_message(q.message.chat_id, text, reply_markup=CANCEL_KB)
    
    context.user_data["prompt_msg_id"] = msg.message_id
    try:
        await q.message.delete()
    except BadRequest:
        pass
    
    return ADDINFO

async def confirm_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "cancel_cmd":
        return await cancel_cmd(update, context)

    ticket_id = context.user_data["addinfo_id"]
    ticket_num = context.user_data["addinfo_num"]
    reply_to_tg_msg_id = context.user_data.get("reply_to_tg_msg_id")
    reply_to_reply_id = context.user_data.get("reply_to_reply_id")
    reply_text = context.user_data["reply_message"]

    chat_type = update.effective_chat.type
    user_name = update.effective_user.username or update.effective_user.first_name

    if chat_type != "private":
        confirm_text = (
            f"✅ @{user_name}, інформацію додано до тікету #{ticket_num}\n"
            f"Повідомлення: {reply_text}"
        )
    else:
        confirm_text = (
            f"Додаткова інформація по тікету {ticket_num} додана ✅\n"
            f"Повідомлення: {reply_text}"
        )

    bot_msg_id = context.user_data.get("bot_msg_id")
    if bot_msg_id:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=bot_msg_id)
        except BadRequest:
            pass

    confirm_msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=confirm_text,
        reply_to_message_id=reply_to_tg_msg_id if reply_to_tg_msg_id else None
    )

    if chat_type == "private":
        await _restore_main_kb(context, update.effective_chat.id, "Головне меню")

    await service.add_reply(
        ticket_id, 
        reply_text, 
        is_support=False, 
        tg_message_id=confirm_msg.message_id,
        reply_to_reply_id=reply_to_reply_id
    )

    ticket = await service.get_ticket_by_num(ticket_num)
    if ticket and ticket.group and ticket.group.tg_group_id:
        if chat_type == "private":
            await context.bot.send_message(
                ticket.group.tg_group_id,
                f"💬 Додаткова інформація по тікету #{ticket_num}:\n{reply_text}"
            )

    context.user_data.clear()
    return ConversationHandler.END

async def choose_theme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    context.user_data["theme_id"] = int(q.data.split("_", 1)[1])
    context.user_data["bot_msg_id"] = q.message.message_id

    user = update.effective_user
    ticket = await service.reserve_ticket(
        group_chat_id=context.user_data["group_chat_id"],
        group_title=context.user_data["group_title"],
        theme_id=context.user_data["theme_id"],
        soc_user_id=user.id,
        soc_user_name=user.username or user.first_name,
    )
    context.user_data["ticket_id"] = ticket.id
    context.user_data["ticket_num"] = ticket.ticket_num
    context.user_data["ticket_theme"] = await service.get_theme_name(theme_id=context.user_data["theme_id"])

    chat_type = q.message.chat.type
    if chat_type != "private":
        cancel_inline = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Скасувати", callback_data="cancel_cmd")]])
        await q.edit_message_text(f"Заявка №{ticket.ticket_num}\nТема: {context.user_data['ticket_theme']}\n")
        msg = await context.bot.send_message(
            q.message.chat_id,
            f"@{user.username or user.first_name}, введіть текст звернення:",
            reply_markup=cancel_inline,
        )
    else:
        await q.edit_message_text(f"Заявка №{ticket.ticket_num}\nТема: {context.user_data['ticket_theme']}\n")
        msg = await context.bot.send_message(
            q.message.chat_id,
            "Введіть текст звернення:",
            reply_markup=CANCEL_KB,
        )
    context.user_data["prompt_msg_id"] = msg.message_id
    return MESSAGE


async def get_message(update, context):
    if update.message.text == CANCEL_BTN:
        return await cancel_cmd(update, context)

    context.user_data["message"] = update.message.text
    await delete_user_msg(update)


    prompt_msg_id = context.user_data.get("prompt_msg_id")
    if prompt_msg_id:
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=prompt_msg_id)
        except BadRequest:
            pass
        context.user_data["prompt_msg_id"] = None

    if update.effective_chat.type == "private":
        await _remove_keyboard(context, update.effective_chat.id)

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Відправити", callback_data="send")],
        [InlineKeyboardButton("Редагувати", callback_data="edit_msg")],
        [InlineKeyboardButton("Скасувати", callback_data="cancel_cmd")],
    ])
    text = (
        f"Номер заявки: {context.user_data['ticket_num']}\n\n"
        f"Тема: {context.user_data['ticket_theme']}\n"
        f"Повідомлення: {context.user_data['message']}\n\n"
        f"Відправити?"
    )
    if update.effective_chat.type != "private":
        text = f"@{update.effective_user.username or update.effective_user.first_name}, {text}"
        
    await step(update, context, text, kb)
    return CONFIRM

async def edit_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    text = "Введіть новий текст звернення:"
    if q.message.chat.type != "private":
        text = f"@{update.effective_user.username or update.effective_user.first_name}, {text}"
        cancel_inline = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Скасувати", callback_data="cancel_cmd")]])
        msg = await context.bot.send_message(q.message.chat_id, text, reply_markup=cancel_inline)
    else:
        msg = await context.bot.send_message(q.message.chat_id, text, reply_markup=CANCEL_KB)
    
    context.user_data["prompt_msg_id"] = msg.message_id
    try:
        await q.message.delete()
    except BadRequest:
        pass
    
    return MESSAGE

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "cancel_cmd":
        return await cancel_cmd(update, context)

    user = update.effective_user
    ticket = await service.finalize_ticket(
        context.user_data["ticket_id"],
        context.user_data["message"],
    )

    if q.message.chat.type == "private":
        await q.edit_message_text(f"Тікет {ticket.ticket_num} відправлено")
    else:
        try:
            await q.message.delete()
        except BadRequest:
            pass

    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Відповісти", callback_data=f"pick_{ticket.id}")]])
    message_text = ticket.message or "(без тексту)"
    
    status_ua = _status_ua(ticket.status)
    
    # In groups, we just drop the finalized ticket to the group
    msg = await context.bot.send_message(
        context.user_data["group_chat_id"],
        f"🎫 Тікет #{ticket.ticket_num}\n\n"
        f"Тема: {context.user_data['ticket_theme']}\n"
        f"Статус: {status_ua}\n"
        f"Від: @{user.username or user.first_name}\n"
        f"Повідомлення: {message_text}",
        reply_markup=kb
    )
    await service.set_ticket_tg_message_id(ticket.id, msg.message_id)
    
    context.user_data.clear()
    if q.message.chat.type == "private":
        await _restore_main_kb(context, q.message.chat_id, "Головне меню")
    return ConversationHandler.END

async def cancel_cmd(update, context):
    if "ticket_id" in context.user_data:
        await service.delete_ticket(context.user_data["ticket_id"])
        reply_text = "Заявку скасовано"
    else:
        reply_text = "Скасовано"

    chat_id = update.effective_chat.id
    if update.message:
        await delete_user_msg(update)
    
    if update.callback_query:
        await update.callback_query.answer()
        chat_id = update.callback_query.message.chat_id

    await _finish(context, chat_id, reply_text if chat_id == update.effective_chat.id else None)
    context.user_data.clear()
    return ConversationHandler.END

async def timeout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "ticket_id" in context.user_data:
        await service.delete_ticket(context.user_data["ticket_id"])

    chat_id = update.effective_chat.id if update and update.effective_chat else None
    if chat_id:
        await _finish(context, chat_id, "Час очікування вийшов. Заявку скасовано.")

    context.user_data.clear()


async def my_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        try:
            msg = await update.message.reply_text("Ця команда доступна лише в приватних повідомленнях з ботом.")
            # Optionally delete the warning msg after a while, or just leave it.
        except BadRequest:
            pass
        return ConversationHandler.END

    if "ticket_id" in context.user_data:
        await service.delete_ticket(context.user_data["ticket_id"])

    tickets = await service.get_open_tickets_for_user(update.effective_user.id)
    if not tickets:
        await update.message.reply_text("У вас немає активних тікетів.", reply_markup=MAIN_KB)
        return ConversationHandler.END
    context.user_data.clear()
    context.user_data["ticket_list"] = [t.id for t in tickets]
    context.user_data["ticket_idx"] = 0
    await show_ticket_page(update.message, context)
    return ADDINFO_PICK


async def show_ticket_page(message_or_query, context):
    idx = context.user_data["ticket_idx"]
    ticket_ids = context.user_data["ticket_list"]
    ticket_id = ticket_ids[idx]
    ticket = await service.get_ticket_by_id(ticket_id)
    theme = await service.get_theme_name(theme_id=ticket.theme_id)
    status_ua = _status_ua(ticket.status)

    text = (
        f"Тікет {idx+1}/{len(ticket_ids)}: {ticket.ticket_num}"
        f"\nТема: {theme}"
        f"\nСтатус: {status_ua}"
        f"\nПовідомлення: {ticket.message or '(без тексту)'}"
    )

    buttons = []
    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data="nav_prev"))
    if idx < len(ticket_ids) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data="nav_next"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("Додати інформацію", callback_data=f"pick_{ticket_id}")])
    buttons.append([InlineKeyboardButton("Вийти", callback_data="close_tickets")])

    kb = InlineKeyboardMarkup(buttons)

    if hasattr(message_or_query, "edit_message_text"):
        await message_or_query.edit_message_text(text, reply_markup=kb)
    else:
        msg = await message_or_query.reply_text(text, reply_markup=kb)
        context.user_data["bot_msg_id"] = msg.message_id


async def nav_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "nav_next":
        context.user_data["ticket_idx"] += 1
    else:
        context.user_data["ticket_idx"] -= 1
    await show_ticket_page(q, context)
    return ADDINFO_PICK


async def close_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("Вихід ✅")
    context.user_data.clear()
    return ConversationHandler.END


async def pick_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ticket_id = int(q.data.split("_", 1)[1])
    ticket = await service.get_ticket_by_id(ticket_id)
    if not ticket:
        if q.message.chat.type == "private":
            await q.edit_message_text("Тікет не знайдено.")
        else:
            await context.bot.send_message(q.message.chat_id, "Тікет не знайдено.")
        return ConversationHandler.END

    status_val = ticket.status.value if hasattr(ticket.status, "value") else ticket.status
    if status_val == "closed":
        if q.message.chat.type == "private":
            await q.edit_message_text(f"Тікет #{ticket.ticket_num} закритий. Додавати відповіді заборонено.")
            await _restore_main_kb(context, q.message.chat_id, "Головне меню")
        else:
            await context.bot.send_message(q.message.chat_id, f"@{update.effective_user.username or update.effective_user.first_name}, тікет #{ticket.ticket_num} закритий. Додавати відповіді заборонено.")
        return ConversationHandler.END

    context.user_data["addinfo_id"] = ticket.id
    context.user_data["addinfo_num"] = ticket.ticket_num
    context.user_data["reply_to_tg_msg_id"] = q.message.message_id
    
    chat_type = q.message.chat.type
    if chat_type != "private":
        cancel_inline = InlineKeyboardMarkup([[InlineKeyboardButton("❌ Скасувати", callback_data="cancel_cmd")]])
        msg = await context.bot.send_message(
            q.message.chat_id,
            f"@{update.effective_user.username or update.effective_user.first_name}, введіть відповідь для тікету #{ticket.ticket_num}:",
            reply_markup=cancel_inline,
            reply_to_message_id=q.message.message_id
        )
        context.user_data["prompt_msg_id"] = msg.message_id
    else:
        context.user_data["bot_msg_id"] = q.message.message_id
        await q.edit_message_text(f"Тікет: {ticket.ticket_num}")
        msg = await context.bot.send_message(
            q.message.chat_id,
            "Введіть додаткову інформацію:",
            reply_markup=CANCEL_KB,
        )
        context.user_data["prompt_msg_id"] = msg.message_id
    return ADDINFO

conv = ConversationHandler(
    entry_points=[
        CommandHandler("start", start),
        CommandHandler("support", support_cmd),
        CallbackQueryHandler(support_cmd, pattern=r"^create_ticket$"),
        CommandHandler("mytickets", my_tickets),
        MessageHandler(MY_TICKETS_FILTER, my_tickets),
        CallbackQueryHandler(pick_ticket, pattern=r"^pick_"),
    ],
    states={
        THEME: [
            CallbackQueryHandler(choose_theme, pattern=r"^theme_"),
            CallbackQueryHandler(cancel_cmd, pattern=r"^cancel_cmd$")
        ],
        MESSAGE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_message),
            CallbackQueryHandler(cancel_cmd, pattern=r"^cancel_cmd$")
        ],
        CONFIRM: [
            CallbackQueryHandler(confirm, pattern=r"^(send|cancel_cmd)$"),
            CallbackQueryHandler(edit_msg, pattern=r"^edit_msg$")
        ],
        ADDINFO_PICK: [
            CallbackQueryHandler(nav_ticket, pattern=r"^nav_"),
            CallbackQueryHandler(pick_ticket, pattern=r"^pick_"),
            CallbackQueryHandler(close_tickets, pattern=r"^close_tickets$"),
        ],
        ADDINFO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, get_addinfo),
            CallbackQueryHandler(cancel_cmd, pattern=r"^cancel_cmd$")
        ],
        ADDINFO_CONFIRM: [
            CallbackQueryHandler(confirm_reply, pattern=r"^(send_reply|cancel_cmd)$"),
            CallbackQueryHandler(edit_reply, pattern=r"^edit_reply$")
        ],
        ConversationHandler.TIMEOUT: [
            MessageHandler(filters.ALL, timeout_handler),
            CallbackQueryHandler(timeout_handler),
        ],
    },
    fallbacks=[
        CommandHandler("cancel", cancel_cmd),
        MessageHandler(MY_TICKETS_FILTER, my_tickets),
    ],
    allow_reentry=True,
    conversation_timeout=600,
)


async def post_init(application: Application) -> None:
    global _bot_username
    me = await application.bot.get_me()
    _bot_username = me.username

    commands = [
        BotCommand("support", "Звернутись у підтримку (лише в групах)"),
        BotCommand("mytickets", "Мої тікети (лише в приватних повідомленнях)"),
        BotCommand("cancel", "Скасувати поточну дію")
    ]
    await application.bot.set_my_commands(commands)


def main():
    load_dotenv()
    token = os.getenv("TG_BOT_TOKEN", "")
    if not token:
        print("no token — set TG_BOT_TOKEN in .env")
        exit(0)

    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        print("no DATABASE_URL — set DATABASE_URL in .env")
        exit(0)

    init_engine(db_url)

    application = (
        Application.builder()
        .token(token)
        .post_init(post_init)
        .build()
    )
    application.add_handler(conv)
    application.add_handler(CommandHandler("setup", post_support_button))
    application.run_polling()

if __name__ == '__main__':
    main()