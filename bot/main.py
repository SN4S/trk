import os
import asyncio
import sys

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, CallbackQueryHandler,
    MessageHandler, filters, ConversationHandler
)
from telegram.error import BadRequest

from database.models import init_engine, create_tables
from database import service

THEME, MESSAGE, CONFIRM, ADDINFO, ADDINFO_PICK = range(5)

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
        await update.message.delete()
    except BadRequest:
        pass

async def post_support_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    bot_username = (await context.bot.get_me()).username
    url = f"https://t.me/{bot_username}?start=support_{chat.id}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Звернутись у підтримку", url=url)]])
    await context.bot.send_message(chat.id, "Потрібна допомога? Натисніть кнопку нижче:", reply_markup=kb)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if not args:
        await update.message.reply_text("Напишіть /start у груповому чаті через кнопку звернення.")
        return ConversationHandler.END

    if args[0].startswith("addinfo_"):
        ticket_num = args[0].split("_", 1)[1]
        ticket = await service.get_ticket_by_num(ticket_num)
        if not ticket:
            await update.message.reply_text("Тікет не знайдено.")
            return ConversationHandler.END
        context.user_data.clear()
        context.user_data["addinfo_id"] = ticket.id
        context.user_data["addinfo_num"] = ticket.ticket_num
        await update.message.reply_text(f"Введіть додаткову інформацію по тікету {ticket.ticket_num}:")
        return ADDINFO

    if not args[0].startswith("support_"):
        await update.message.reply_text("Напишіть /start у груповому чаті через кнопку звернення.")
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
    ticket_id = context.user_data["addinfo_id"]
    ticket_num = context.user_data["addinfo_num"]
    await service.add_reply(ticket_id, update.message.text, is_support=False)

    ticket = await service.get_ticket_by_num(ticket_num)
    if ticket and ticket.group and ticket.group.tg_group_id:
        await context.bot.send_message(
            ticket.group.tg_group_id,
            f"💬 Додаткова інформація по тікету #{ticket_num}:\n{update.message.text}"
        )
    await update.message.reply_text("Додано ✅")
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

    await q.edit_message_text(f"Заявка №{ticket.ticket_num} створена\n\nТема: {context.user_data['ticket_theme']}\n\nВведіть текст звернення:")

    return MESSAGE


async def get_message(update, context):
    context.user_data["message"] = update.message.text
    await delete_user_msg(update)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Відправити", callback_data="send")],
        [InlineKeyboardButton("Скасувати", callback_data="cancel")],
    ])
    text = f"Номер заявки: {context.user_data['ticket_num']}\n\nТема звернення:{context.user_data['ticket_theme']}\nПовідомлення: {context.user_data['message']}\n\nВідправити?"
    await step(update, context, text, kb)
    return CONFIRM

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "cancel":
        await service.delete_ticket(context.user_data["ticket_id"])
        await q.edit_message_text("Заявку скасовано")
        context.user_data.clear()
        return ConversationHandler.END

    user = update.effective_user
    ticket = await service.finalize_ticket(
        context.user_data["ticket_id"],
        context.user_data["message"],
    )

    await q.edit_message_text(f"Тікет {ticket.ticket_num} відправлено")

    bot_username = (await context.bot.get_me()).username
    url = f"https://t.me/{bot_username}?start=addinfo_{ticket.ticket_num}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("Надіслати додаткову інформацію", url=url)]])

    await context.bot.send_message(
        context.user_data["group_chat_id"],
        f"🎫 Тікет #{ticket.ticket_num}\n\nТема:{context.user_data['ticket_theme']}\nВід: @{user.username or user.first_name}\n"
        f"Повідомлення: {ticket.message}", reply_markup=kb
    )
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_cmd(update, context):
    if "ticket_id" in context.user_data:
        await service.delete_ticket(context.user_data["ticket_id"])
    if update.callback_query:
        await update.callback_query.edit_message_text("Заявку скасовано")
    else:
        await update.message.reply_text("Заявку скасовано")
    context.user_data.clear()
    return ConversationHandler.END

async def my_tickets(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tickets = await service.get_open_tickets_for_user(update.effective_user.id)
    if not tickets:
        await update.message.reply_text("У вас немає активних тікетів.")
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

    text = (f"Тікет {idx+1}/{len(ticket_ids)}: {ticket.ticket_num}"
            f"\nТема: {theme}"
            f"\nПовідомлення: {ticket.message}")

    buttons = []
    nav = []
    if idx > 0:
        nav.append(InlineKeyboardButton("◀️", callback_data="nav_prev"))
    if idx < len(ticket_ids) - 1:
        nav.append(InlineKeyboardButton("▶️", callback_data="nav_next"))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton("Додати інформацію", callback_data=f"pick_{ticket_id}")])

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


async def pick_ticket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    ticket_id = int(q.data.split("_", 1)[1])
    ticket = await service.get_ticket_by_id(ticket_id)
    if not ticket:
        await q.edit_message_text("Тікет не знайдено.")
        return ConversationHandler.END
    context.user_data["addinfo_id"] = ticket.id
    context.user_data["addinfo_num"] = ticket.ticket_num
    await q.edit_message_text(f"Введіть додаткову інформацію по тікету {ticket.ticket_num}:")
    return ADDINFO

conv = ConversationHandler(
    entry_points=[CommandHandler("start", start), CommandHandler("mytickets",my_tickets),CallbackQueryHandler(pick_ticket, pattern=r"^pick_"),],
    states={
        THEME: [CallbackQueryHandler(choose_theme, pattern=r"^theme_")],
        MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_message)],
        CONFIRM: [CallbackQueryHandler(confirm, pattern=r"^(send|cancel)$")],
        ADDINFO_PICK: [CallbackQueryHandler(nav_ticket, pattern=r"^nav_"),CallbackQueryHandler(pick_ticket, pattern=r"^pick_")],
        ADDINFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_addinfo)],
    },
    fallbacks=[CommandHandler("cancel", cancel_cmd)],
)


async def setup_group_button(update, context):
    await post_support_button(update, context)

async def post_init(application) -> None:
    await create_tables()

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
        .build()
    )
    application.add_handler(conv)
    application.add_handler(CommandHandler("setup", setup_group_button))
    application.run_polling()

if __name__ == '__main__':
    main()