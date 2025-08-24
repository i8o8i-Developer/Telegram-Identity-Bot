import os
import io
import json
import logging
import time
import asyncio
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ---------- Logging ----------
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("Tg-Id-Bot")

# ---------- Config ----------
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError(
        "❌ TELEGRAM_BOT_TOKEN is missing. Please set it in Cloud Run environment variables or Secret Manager."
    )

# ---------- FastAPI ----------
app = FastAPI(title="Telegram ID Bot (Polling Mode)")

# ---------- PTB Application ----------
application: Application = ApplicationBuilder().token(BOT_TOKEN).build()

# ---------- Commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("Your ID", callback_data="id")],
        [InlineKeyboardButton("This Chat/Group ID", callback_data="chatid")],
        [InlineKeyboardButton("Admins", callback_data="admins")],
        [InlineKeyboardButton("📦 Export JSON", callback_data="export")],
        [InlineKeyboardButton("ℹ️ User Info", callback_data="userinfo")],
        [InlineKeyboardButton("🆘 Help", callback_data="help")],
        [InlineKeyboardButton("🧵 Topic ID", callback_data="topicid")],
    ])
    text = (
        "Hi! I Can Show IDs And Chat Info.\n\n"
        "Commands :\n"
        "/id – Your ID\n"
        "/chatid – This Chat's/Group's ID\n"
        "/topicid – Get The Topic ID In This Thread\n"
        "/members – Member Count\n"
        "/admins – List Admins\n"
        "/export – Export Chat Info As JSON\n"
        "/userinfo – Show Your Info\n"
        "/ping – Bot Latency\n"
        "/fileid – Get File ID Of Media"
    )
    await update.effective_message.reply_text(text, reply_markup=kb)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "📖 Available Commands:\n\n"
        "/start – Show Menu\n"
        "/help – Show This Help\n"
        "/id – Your Telegram ID\n"
        "/chatid – This Chat's/Group's ID\n"
        "/topicid – Get The Topic ID In This Thread\n"
        "/members – Member Count\n"
        "/admins – List Chat/Group Admins\n"
        "/export – Export Chat Info As JSON\n"
        "/userinfo – Show Detailed User Info\n"
        "/ping – Test Bot Latency\n"
        "/fileid – Get File ID From Media"
    )

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.effective_message.reply_text(
        f"Your ID : <code>{u.id}</code>", parse_mode="HTML"
    )

async def cmd_chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = update.effective_chat
    await update.effective_message.reply_text(
        f"Chat ID : <code>{c.id}</code>\nType: {c.type}", parse_mode="HTML"
    )

async def cmd_topicid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat

    if chat.type in ["supergroup", "group"]:
        if msg.is_topic_message: 
            thread_id = msg.message_thread_id
            await msg.reply_text(
                f"🧵 This Topic's ID : <code>{thread_id}</code>",
                parse_mode="HTML",
            )
        else:
            await msg.reply_text("⚠️ This Chat Has No Topic ID (Not In A Thread).")
    else:
        await msg.reply_text("⚠️ This command Only Works In SuperGroups With Topics Enabled.")


async def cmd_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    try:
        count = await context.bot.get_chat_member_count(chat.id)
        await update.effective_message.reply_text(f"👥 Members : <b>{count}</b>", parse_mode="HTML")
    except Exception as e:
        await update.effective_message.reply_text(f"⚠️ Could Not Fetch Member Count\n{e}")

async def cmd_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        names = [a.user.mention_html() for a in admins]
        await update.effective_message.reply_text(
            "👑 Admins :\n" + "\n".join(names), parse_mode="HTML"
        )
    except Exception as e:
        await update.effective_message.reply_text(f"⚠️ Could Not Fetch Admins\n{e}")

def _chat_snapshot(update: Update) -> Dict[str, Any]:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    return {
        "chat": {
            "id": chat.id,
            "type": chat.type,
            "title": chat.title,
            "username": chat.username,
            "first_name": chat.first_name,
            "last_name": chat.last_name,
            "bio": getattr(chat, "bio", None),
            "description": getattr(chat, "description", None),
            "invite_link": getattr(chat, "invite_link", None),
        },
        "from_user": {
            "id": user.id if user else None,
            "is_bot": user.is_bot if user else None,
            "username": user.username if user else None,
            "first_name": user.first_name if user else None,
            "last_name": user.last_name if user else None,
            "full_name": user.full_name if user else None,
            "language_code": user.language_code if user else None,
        } if user else None,
        "message": {
            "message_id": msg.message_id if msg else None,
            "text": msg.text if msg else None,
            "caption": msg.caption if msg else None,
            "media_group_id": msg.media_group_id if msg else None,
            "has_protected_content": msg.has_protected_content if msg else None,
            "date": msg.date.isoformat() if msg and msg.date else None,
            "edit_date": msg.edit_date.isoformat() if msg and msg.edit_date else None,
            "entities": [e.to_dict() for e in msg.entities] if msg and msg.entities else None,
            "reply_to_message_id": msg.reply_to_message.message_id if msg and msg.reply_to_message else None,
        } if msg else None,
    }

async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payload = _chat_snapshot(update)
    buf = io.BytesIO(json.dumps(payload, indent=2, ensure_ascii=False).encode())
    buf.name = "Chat_Info.json"
    await update.effective_message.reply_document(InputFile(buf))

async def cmd_userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    info = (
        f"👤 <b>User Info</b>\n"
        f"ID : <code>{u.id}</code>\n"
        f"Username : @{u.username if u.username else 'N/A'}\n"
        f"Name: {u.full_name}\n"
        f"Language : {u.language_code or 'N/A'}\n"
        f"Bot : {'Yes' if u.is_bot else 'No'}"
    )
    await update.effective_message.reply_text(info, parse_mode="HTML")

async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.time()
    msg = await update.effective_message.reply_text("Pinging...")
    latency = (time.time() - start) * 1000
    await msg.edit_text(f"🏓 Pong ! : <b>{latency:.2f} ms</b>", parse_mode="HTML")

async def cmd_fileid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    file_id = None
    if msg.reply_to_message:
        if msg.reply_to_message.sticker:
            file_id = msg.reply_to_message.sticker.file_id
        elif msg.reply_to_message.photo:
            file_id = msg.reply_to_message.photo[-1].file_id
        elif msg.reply_to_message.document:
            file_id = msg.reply_to_message.document.file_id
        elif msg.reply_to_message.video:
            file_id = msg.reply_to_message.video.file_id
    if file_id:
        await msg.reply_text(f"🆔 File ID :\n<code>{file_id}</code>", parse_mode="HTML")
    else:
        await msg.reply_text("⚠️ Reply To A Sticker/Photo/Document/Video To Get Its File ID")

async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    await update.callback_query.answer()
    if data == "id":
        await cmd_id(update, context)
    elif data == "chatid":
        await cmd_chatid(update, context)
    elif data == "admins":
        await cmd_admins(update, context)
    elif data == "export":
        await cmd_export(update, context)
    elif data == "userinfo":
        await cmd_userinfo(update, context)
    elif data == "help":
        await help_cmd(update, context)
    elif data == "topicid":
        await cmd_topicid(update, context)


# ---------- FastAPI Routes ----------
@app.get("/", response_class=PlainTextResponse)
async def root():
    return "✅ Telegram ID Bot Running in Polling Mode"

@app.get("/healthz")
async def health():
    return {"status": "Healthy"}

# ---------- Startup / Shutdown ----------
@app.on_event("startup")
async def on_startup():
    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("id", cmd_id))
    application.add_handler(CommandHandler("chatid", cmd_chatid))
    application.add_handler(CommandHandler("topicid", cmd_topicid))
    application.add_handler(CommandHandler("members", cmd_members))
    application.add_handler(CommandHandler("admins", cmd_admins))
    application.add_handler(CommandHandler("export", cmd_export))
    application.add_handler(CommandHandler("userinfo", cmd_userinfo))
    application.add_handler(CommandHandler("ping", cmd_ping))
    application.add_handler(CommandHandler("fileid", cmd_fileid))
    application.add_handler(CallbackQueryHandler(on_callback))

    # Start Polling In Background
    await application.initialize()
    await application.start()
    asyncio.create_task(application.updater.start_polling())
    log.info("🚀 Bot Started in Polling Mode")

@app.on_event("shutdown")
async def on_shutdown():
    await application.updater.stop()
    await application.stop()
    await application.shutdown()
    log.info("🛑 Bot Stopped ...")
