import os
import io
import json
import logging
import time
import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.error import TelegramError, Conflict

# ---------- Production Logging ----------
def setup_logging():
    """Setup Production-Grade Logging"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Create Logs Directory If It Doesn't Exist
    log_dir = "/app/logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure Logging Format
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(process)d | %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f"{log_dir}/app.log", mode="a")
        ]
    )

    # Set Specific Loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
    
    return logging.getLogger("TeleIdentityBot")

log = setup_logging()

# ---------- Developer Signature ----------
SIGNATURE = os.getenv("BOT_SIGNATURE", "i8o8i Developer")

# ---------- Configuration And Validation ----------
def validate_environment():
    """Validate Required Environment Variables"""
    required_vars = ["TELEGRAM_BOT_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"Missing Required Environment Variables: {', '.join(missing_vars)}"
        log.error(error_msg)
        raise RuntimeError(error_msg)

    # Validate Bot Token Format
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token or len(bot_token.split(":")) != 2:
        raise RuntimeError("Invalid TELEGRAM_BOT_TOKEN Format")
    
    log.info("Environment Validation Passed")

# Validate Environment On Startup
validate_environment()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
APP_ENV = os.getenv("APP_ENV", "production")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# Sync With Docker/Coolify Defaults
PORT = int(os.getenv("PORT", "3000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# ---------- Global State ----------
application: Optional[Application] = None
shutdown_event = asyncio.Event()
polling_task: Optional[asyncio.Task] = None

# ---------- Graceful Shutdown Handler ----------
def signal_handler(signum, frame):
    """Handle Shutdown Signals Gracefully"""
    log.info(f"Received Signal {signum}, Initiating Graceful Shutdown...")
    
    try:
        shutdown_event.set()
    except Exception:
        pass

# Register Signal Handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# ---------- Error Handling Decorator ----------
def handle_errors(func):
    """Decorator For Error Handling In Commands"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            return await func(update, context)
        except TelegramError as e:
            log.error(f"Telegram Error In {func.__name__}: {e}")
            try:
                await update.effective_message.reply_text(
                    f"⚠️ <b>Telegram API Error</b>\n"
                    f"─────────────────────────\n\n"
                    f"🔧 <b>Issue:</b> API Communication Problem\n"
                    f"🔄 <b>Solution:</b> Please Try Again In A Moment\n"
                    f"📱 <b>Status:</b> Temporary Issue\n\n"
                    f"💡 <i>If This Persists, Telegram May Be Having Issues!</i>",
                    parse_mode="HTML"
                )
            except:
                pass
        except Exception as e:
            log.error(f"Unexpected Error In {func.__name__}: {e}")
            try:
                await update.effective_message.reply_text(
                    f"❌ <b>Unexpected Error</b>\n"
                    f"─────────────────────────\n\n"
                    f"🚫 <b>Issue:</b> Something Went Wrong\n"
                    f"🔄 <b>Solution:</b> Please Try Again\n"
                    f"🛠️ <b>Status:</b> Error Logged For Review\n\n"
                    f"💡 <i>Our Team Will Investigate This Issue!</i>",
                    parse_mode="HTML"
                )
            except:
                pass
    return wrapper

# ---------- Enhanced Command Handlers ----------
@handle_errors
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🆔 Your ID", callback_data="id"), 
         InlineKeyboardButton("💬 Chat/Group ID", callback_data="chatid")],
        [InlineKeyboardButton("👑 Admins", callback_data="admins"), 
         InlineKeyboardButton("👥 Member Count", callback_data="members")],
        [InlineKeyboardButton("🧵 Topic ID", callback_data="topicid"), 
         InlineKeyboardButton("ℹ️ User Info", callback_data="userinfo")],
        [InlineKeyboardButton("📦 Export JSON", callback_data="export"), 
         InlineKeyboardButton("🔍 Ping Test", callback_data="ping")],
        [InlineKeyboardButton("🆘 Help & Commands", callback_data="help")]
    ])
    
    user_name = update.effective_user.first_name if update.effective_user else "User"
    text = (
        f"🔍 <b>Telegram ID Bot</b>\n"
        f"─────────────────────────\n\n"
        f"👋 Hello <b>{user_name}</b>! I Can Help You Discover IDs and Chat Information.\n\n"
        f"✨ <b>Quick Actions:</b>\n"
        f"🆔 Get Your Telegram ID\n"
        f"💬 Find Chat/Group IDs\n"
        f"🧵 Discover Topic IDs\n"
        f"👑 List Administrators\n"
        f"📊 Export Chat Data\n\n"
        f"📱 <i>Choose An Option Below Or Use Commands Directly!</i>"
        f"\n\n— <i>{SIGNATURE}</i>"
    )
    await update.effective_message.reply_text(text, reply_markup=kb, parse_mode="HTML")

@handle_errors
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        f"📖 <b>Command Reference</b>\n"
        f"─────────────────────────\n\n"
        f"🏠 <code>/start</code> — Show Main Menu\n"
        f"🆘 <code>/help</code> — Display This Help\n\n"
        f"🔍 <b>ID Commands:</b>\n"
        f"🆔 <code>/id</code> — Your Telegram ID\n"
        f"💬 <code>/chatid</code> — Current Chat/Group ID\n"
        f"🧵 <code>/topicid</code> — Topic ID (In Threads)\n\n"
        f"👥 <b>Group Info:</b>\n"
        f"📊 <code>/members</code> — Member Count\n"
        f"👑 <code>/admins</code> — List Administrators\n\n"
        f"📱 <b>Utilities:</b>\n"
        f"ℹ️ <code>/userinfo</code> — Detailed User Info\n"
        f"📦 <code>/export</code> — Export Chat Data (JSON)\n"
        f"🔍 <code>/ping</code> — Test Bot Response Time\n"
        f"🗂️ <code>/fileid</code> — Get Media File ID\n\n"
        f"💡 <i>Tip: Use The Buttons Above For Quick Access!</i>"
    )
    # Append Signature To Help
    help_text = help_text + f"\n\n— <i>{SIGNATURE}</i>"
    await update.effective_message.reply_text(help_text, parse_mode="HTML")

@handle_errors
async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    await update.effective_message.reply_text(
        f"🆔 <b>Your Telegram ID</b>\n"
        f"─────────────────────────\n\n"
        f"👤 <b>User:</b> {u.full_name}\n"
        f"🔢 <b>ID:</b> <code>{u.id}</code>\n\n"
        f"💡 <i>Copy The ID by Tapping On It!</i>", 
        parse_mode="HTML"
    )

@handle_errors
async def cmd_chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = update.effective_chat
    
    # Get Chat Icon Based On Type
    chat_icons = {
        "private": "👤",
        "group": "👥", 
        "supergroup": "🏢",
        "channel": "📢"
    }
    icon = chat_icons.get(c.type, "💬")
    
    chat_name = c.title or c.first_name or "Unknown"
    
    await update.effective_message.reply_text(
        f"{icon} <b>Chat Information</b>\n"
        f"─────────────────────────\n\n"
        f"📝 <b>Name:</b> {chat_name}\n"
        f"🔢 <b>Chat ID:</b> <code>{c.id}</code>\n"
        f"📊 <b>Type:</b> {c.type.title()}\n\n"
        f"💡 <i>Tap The ID To Copy It!</i>", 
        parse_mode="HTML"
    )

@handle_errors
async def cmd_topicid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat

    if chat.type in ["supergroup", "group"]:
        if msg.is_topic_message: 
            thread_id = msg.message_thread_id
            await msg.reply_text(
                f"🧵 <b>Topic Information</b>\n"
                f"─────────────────────────\n\n"
                f"💬 <b>Chat:</b> {chat.title or 'Unknown'}\n"
                f"🔢 <b>Topic ID:</b> <code>{thread_id}</code>\n\n"
                f"✅ <i>This Message Is In A Topic Thread!</i>",
                parse_mode="HTML",
            )
        else:
            await msg.reply_text(
                f"🧵 <b>Topic Status</b>\n"
                f"─────────────────────────\n\n"
                f"⚠️ <b>No Topic Found</b>\n\n"
                f"🔍 This Chat Doesn't Have Topics Enabled\n"
                f"🔄 Or This Message Isn't In A Topic Thread\n\n"
                f"💡 <i>Topics Are Available In Supergroups Only!</i>",
                parse_mode="HTML"
            )
    else:
        await msg.reply_text(
            f"🧵 <b>Topic Feature</b>\n"
            f"─────────────────────────\n\n"
            f"❌ <b>Not Available</b>\n\n"
            f"📱 Topics Only Work In <b>Supergroups</b>\n"
            f"🔄 Convert Your Group To Supergroup First\n\n"
            f"💡 <i>Private Chats Don't Support Topics!</i>",
            parse_mode="HTML"
        )

@handle_errors
async def cmd_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    try:
        count = await context.bot.get_chat_member_count(chat.id)
        
        # Member Count Visualization
        if count < 10:
            status = "👥 Small Group"
        elif count < 100:
            status = "🏘️ Medium Group"
        elif count < 1000:
            status = "🏢 Large Group"
        else:
            status = "🌆 Huge Community"
            
        await update.effective_message.reply_text(
            f"👥 <b>Member Statistics</b>\n"
            f"─────────────────────────\n\n"
            f"📊 <b>Total Members:</b> <code>{count:,}</code>\n"
            f"🏷️ <b>Status:</b> {status}\n"
            f"💬 <b>Chat:</b> {chat.title or 'Unknown'}\n\n"
            f"📈 <i>Live Member Count Updated!</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        log.error(f"Error Getting Member Count: {e}")
        await update.effective_message.reply_text(
            f"👥 <b>Member Count</b>\n"
            f"─────────────────────────\n\n"
            f"❌ <b>Access Denied</b>\n\n"
            f"🔒 Cannot Fetch Member Count\n"
            f"📱 Bot Might Lack Permissions\n"
            f"🔄 Try In A Group Where I'm Admin\n\n"
            f"💡 <i>This Works Best In Public Groups!</i>",
            parse_mode="HTML"
        )

@handle_errors
async def cmd_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        
        if not admins:
            await update.effective_message.reply_text(
                f"👑 <b>Administrators</b>\n"
                f"─────────────────────────\n\n"
                f"❌ <b>No Admins Found</b>\n\n"
                f"🤔 This Is Unusual...\n"
                f"💬 <i>Every Group Should Have Admins!</i>",
                parse_mode="HTML"
            )
            return
            
        admin_list = []
        owner_count = 0
        admin_count = 0
        
        for admin in admins:
            user = admin.user
            if admin.status == "creator":
                admin_list.append(f"👑 {user.mention_html()} <i>(Owner)</i>")
                owner_count += 1
            else:
                admin_list.append(f"🛡️ {user.mention_html()}")
                admin_count += 1
        
        admin_text = "\n".join(admin_list)
        total_admins = len(admins)
        
        await update.effective_message.reply_text(
            f"👑 <b>Chat Administrators</b>\n"
            f"─────────────────────────\n\n"
            f"📊 <b>Total:</b> {total_admins} administrator{'s' if total_admins != 1 else ''}\n"
            f"👑 <b>Owners:</b> {owner_count}\n"
            f"🛡️ <b>Admins:</b> {admin_count}\n\n"
            f"<b>Admin List:</b>\n{admin_text}\n\n"
            f"💡 <i>Tap Names To View Profiles!</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        log.error(f"Error getting admins: {e}")
        await update.effective_message.reply_text(
            f"👑 <b>Administrators</b>\n"
            f"─────────────────────────\n\n"
            f"❌ <b>Access Denied</b>\n\n"
            f"🔒 Cannot Fetch Admin List\n"
            f"📱 Bot Might Lack Permissions\n"
            f"🔄 Make Me Admin to See Full List\n\n"
            f"💡 <i>Some Groups Restrict This Info!</i>",
            parse_mode="HTML"
        )

def _chat_snapshot(update: Update) -> Dict[str, Any]:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    return {
        "timestamp": time.time(),
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

@handle_errors
async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Show progress Message
        progress_msg = await update.effective_message.reply_text(
            f"📦 <b>Exporting Chat Data...</b>\n"
            f"─────────────────────────\n\n"
            f"⏳ <i>Gathering Chat Information...</i>",
            parse_mode="HTML"
        )
        
        payload = _chat_snapshot(update)
        
        # Enhanced Export With Metadata
        export_data = {
            "export_info": {
                "generated_by": f"Telegram ID Bot v2.0.0 — {SIGNATURE}",
                "export_date": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "export_timestamp": time.time(),
            },
            "data": payload
        }
        
        buf = io.BytesIO(json.dumps(export_data, indent=2, ensure_ascii=False).encode())
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        buf.name = f"Chat_Export_{timestamp}.json"
        
        await progress_msg.edit_text(
            f"📦 <b>Export Complete!</b>\n"
            f"─────────────────────────\n\n"
            f"✅ <b>Status:</b> Ready For Download\n"
            f"📄 <b>Format:</b> JSON\n"
            f"🕐 <b>Generated:</b> {time.strftime('%H:%M:%S')}\n\n"
            f"📥 <i>Sending File...</i>",
            parse_mode="HTML"
        )
        
        await update.effective_message.reply_document(
            InputFile(buf),
            caption=(
                f"📊 <b>Chat Data Export</b>\n\n"
                f"💾 Complete Chat Information In JSON Format\n"
                f"🔒 All Sensitive Data Included\n"
                f"⚡ Generated Instantly\n\n"
                f"💡 <i>Use This Data For Backups Or Analysis!</i>"
            ),
            parse_mode="HTML"
        )
        
        # Delete Progress Message
        await progress_msg.delete()
        
    except Exception as e:
        log.error(f"Error Exporting Data: {e}")
        await update.effective_message.reply_text(
            f"📦 <b>Export Failed</b>\n"
            f"─────────────────────────\n\n"
            f"❌ <b>Error:</b> Could Not Export Data\n"
            f"🔧 <b>Reason:</b> Technical Error\n"
            f"🔄 <b>Solution:</b> Try Again In A Moment\n\n"
            f"💡 <i>If Issue Persists, Contact Support!</i>",
            parse_mode="HTML"
        )

@handle_errors
async def cmd_userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user

    # User Status Indicators
    bot_status = "🤖 Bot" if u.is_bot else "👤 Human"
    username_display = f"@{u.username}" if u.username else "❌ No username"
    language_display = u.language_code.upper() if u.language_code else "🌍 Unknown"
    
    # Premium Status (if Available)
    premium_status = ""
    if hasattr(u, 'is_premium') and u.is_premium:
        premium_status = "⭐ Premium User\n"
    
    info = (
        f"ℹ️ <b>User Information</b>\n"
        f"─────────────────────────\n\n"
        f"👤 <b>Name:</b> {u.full_name}\n"
        f"🆔 <b>ID:</b> <code>{u.id}</code>\n"
        f"📛 <b>Username:</b> {username_display}\n"
        f"🌍 <b>Language:</b> {language_display}\n"
        f"📰 <b>Type:</b> {bot_status}\n"
        f"{premium_status}\n"
        f"🕐 <b>Checked:</b> {time.strftime('%H:%M:%S')}\n\n"
        f"💡 <i>All Your Telegram Details In One Place!</i>"
    )
    await update.effective_message.reply_text(info, parse_mode="HTML")

@handle_errors
async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = time.time()
    msg = await update.effective_message.reply_text(
        f"🔍 <b>Testing Connection...</b>\n"
        f"─────────────────────────\n\n"
        f"⏳ <i>Measuring Response Time...</i>"
    )
    latency = (time.time() - start) * 1000
    
    # Latency Status
    if latency < 100:
        status = "🟢 Excellent"
        emoji = "⚡"
    elif latency < 300:
        status = "🟡 Good" 
        emoji = "💚"
    elif latency < 500:
        status = "🟠 Fair"
        emoji = "⚠️"
    else:
        status = "🔴 Slow"
        emoji = "🌍"
    
    await msg.edit_text(
        f"🔍 <b>Ping Test Results</b>\n"
        f"─────────────────────────\n\n"
        f"{emoji} <b>Response Time:</b> <code>{latency:.2f} ms</code>\n"
        f"📊 <b>Status:</b> {status}\n"
        f"🕐 <b>Tested:</b> {time.strftime('%H:%M:%S')}\n\n"
        f"✅ <i>Bot Is Responding Normally!</i>", 
        parse_mode="HTML"
    )

@handle_errors
async def cmd_fileid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    file_id = None
    file_type = None
    file_size = None
    
    if msg.reply_to_message:
        replied_msg = msg.reply_to_message
        if replied_msg.sticker:
            file_id = replied_msg.sticker.file_id
            file_type = "🎭 Sticker"
            file_size = getattr(replied_msg.sticker, 'file_size', None)
        elif replied_msg.photo:
            file_id = replied_msg.photo[-1].file_id
            file_type = "🖼️ Photo"
            file_size = getattr(replied_msg.photo[-1], 'file_size', None)
        elif replied_msg.document:
            file_id = replied_msg.document.file_id
            file_type = f"📄 Document ({replied_msg.document.file_name or 'Unknown'})"
            file_size = getattr(replied_msg.document, 'file_size', None)
        elif replied_msg.video:
            file_id = replied_msg.video.file_id
            file_type = "🎥 Video"
            file_size = getattr(replied_msg.video, 'file_size', None)
        elif replied_msg.audio:
            file_id = replied_msg.audio.file_id
            file_type = "🎵 Audio"
            file_size = getattr(replied_msg.audio, 'file_size', None)
        elif replied_msg.voice:
            file_id = replied_msg.voice.file_id
            file_type = "🎤 Voice Message"
            file_size = getattr(replied_msg.voice, 'file_size', None)
    
    if file_id:
        size_text = f"\n📏 <b>Size:</b> {file_size:,} bytes" if file_size else ""
        
        await msg.reply_text(
            f"🗂️ <b>File Information</b>\n"
            f"─────────────────────────\n\n"
            f"📝 <b>Type:</b> {file_type}\n"
            f"🆔 <b>File ID:</b>\n<code>{file_id}</code>{size_text}\n\n"
            f"💡 <i>Tap The ID To Copy It!\n"
            f"Use This ID To Send The Same File.</i>", 
            parse_mode="HTML"
        )
    else:
        await msg.reply_text(
            f"🗂️ <b>File ID Extractor</b>\n"
            f"─────────────────────────\n\n"
            f"❌ <b>No Media Found</b>\n\n"
            f"📱 <b>How To Use:</b>\n"
            f"1️⃣ Find A Message With Media\n"
            f"2️⃣ Reply To It With <code>/fileid</code>\n"
            f"3️⃣ Get The Unique File ID!\n\n"
            f"🎯 <b>Supported Types:</b>\n"
            f"🖼️ Photos • 🎥 Videos • 📄 Documents\n"
            f"🎭 Stickers • 🎵 Audio • 🎤 Voice\n\n"
            f"💡 <i>File IDs Never Expire!</i>",
            parse_mode="HTML"
        )

@handle_errors
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    await update.callback_query.answer()
    
    if data == "id":
        await cmd_id(update, context)
    elif data == "chatid":
        await cmd_chatid(update, context)
    elif data == "admins":
        await cmd_admins(update, context)
    elif data == "members":
        await cmd_members(update, context)
    elif data == "export":
        await cmd_export(update, context)
    elif data == "userinfo":
        await cmd_userinfo(update, context)
    elif data == "help":
        await help_cmd(update, context)
    elif data == "topicid":
        await cmd_topicid(update, context)
    elif data == "ping":
        await cmd_ping(update, context)

# ---------- Handler Registration ----------
def register_handlers(app: Application):
    """Register all bot handlers"""
    handlers = [
        CommandHandler("start", start),
        CommandHandler("help", help_cmd),
        CommandHandler("id", cmd_id),
        CommandHandler("chatid", cmd_chatid),
        CommandHandler("topicid", cmd_topicid),
        CommandHandler("members", cmd_members),
        CommandHandler("admins", cmd_admins),
        CommandHandler("export", cmd_export),
        CommandHandler("userinfo", cmd_userinfo),
        CommandHandler("ping", cmd_ping),
        CommandHandler("fileid", cmd_fileid),
        CallbackQueryHandler(on_callback),
    ]
    
    for handler in handlers:
        app.add_handler(handler)
    
    log.info(f"✅ Registered {len(handlers)} Handlers")

# ---------- Async Polling Function With Conflict Handling ----------
async def run_polling():
    """Run Bot Polling with Proper Conflict Handling"""
    global application, polling_task
    max_retries = 5
    retry_delay = 5
    
    try:
        if application:
            log.info("🔄 Starting Bot Polling...")
            await application.initialize()
            await application.start()
            
            retry_count = 0
            while not shutdown_event.is_set() and retry_count < max_retries:
                try:
                    # Clear Any Pending Updates First to Prevent Conflicts
                    log.info("🧹 Clearing Pending Updates...")
                    await application.bot.get_updates(offset=-1, limit=1, timeout=1)

                    # Start Polling With Proper Parameters (FIXED)
                    await application.updater.start_polling(
                        drop_pending_updates=True,
                        allowed_updates=Update.ALL_TYPES
                    )
                    
                    log.info("✅ Bot polling started successfully!")
                    retry_count = 0  # Reset Retry Count On Successful Start
                    
                    # Keep Polling Until Shutdown
                    while not shutdown_event.is_set():
                        await asyncio.sleep(1)
                        
                except Conflict as e:
                    log.warning(f"⚠️ Bot Conflict Detected : {e}")
                    retry_count += 1
                    
                    if retry_count < max_retries:
                        log.info(f"🔄 Waiting {retry_delay} Seconds Before Retry {retry_count}/{max_retries}...")
                        
                        # Stop Current Updater If Running
                        try:
                            if application.updater.running:
                                await application.updater.stop()
                        except Exception as stop_error:
                            log.warning(f"Error Stopping Updater: {stop_error}")
                        
                        # Wait Before Retrying
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 60)  # Exponential Backoff, Max 60s
                    else:
                        log.error("❌ Max Retries Reached for Bot Conflicts")
                        break
                        
                except Exception as e:
                    log.error(f"❌ Unexpected Polling Error: {e}")
                    retry_count += 1
                    
                    if retry_count < max_retries:
                        log.info(f"🔄 Retrying After Error... {retry_count}/{max_retries}")
                        await asyncio.sleep(retry_delay)
                    else:
                        log.error("❌ Max Retries Reached for Polling Errors")
                        break
                        
    except Exception as e:
        log.error(f"❌ Fatal Polling Error: {e}")
        raise
    finally:
        if application:
            try:
                if application.updater.running:
                    await application.updater.stop()
                await application.stop()
                await application.shutdown()
                log.info("✅ Bot Polling Stopped Cleanly")
            except Exception as e:
                log.error(f"❌ Error Stopping Bot: {e}")

# ---------- Application Lifespan ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Application LifeSpan With Proper Startup and Shutdown"""
    global application, polling_task
    
    try:
        # Startup
        log.info("🚀 Starting Telegram ID Bot...")

        # Create the application with better configuration
        application = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .connect_timeout(REQUEST_TIMEOUT)
            .read_timeout(REQUEST_TIMEOUT)
            .write_timeout(REQUEST_TIMEOUT)
            .pool_timeout(REQUEST_TIMEOUT)
            .get_updates_connect_timeout(REQUEST_TIMEOUT)
            .get_updates_read_timeout(REQUEST_TIMEOUT)
            .concurrent_updates(True)
            .build()
        )

        # Register Handlers
        register_handlers(application)

        # Start Polling In Background Task
        polling_task = asyncio.create_task(run_polling())

        log.info(f"✅ Bot Started Successfully — Listening On Port {PORT}")

        yield
        
    except Exception as e:
        log.error(f"❌ Failed To Start Bot: {e}")
        raise
    finally:
        # Shutdown
        log.info("🛑 Shutting Down Bot...")
        
        # Signal shutdown
        shutdown_event.set()
        
        # Cancel Polling Task
        if polling_task and not polling_task.done():
            polling_task.cancel()
            try:
                await asyncio.wait_for(polling_task, timeout=10.0)
            except asyncio.TimeoutError:
                log.warning("⚠️ Polling Task Didn't Stop Within Timeout")
            except asyncio.CancelledError:
                log.info("✅ Polling Task Cancelled Successfully")
            except Exception as e:
                log.error(f"❌ Error Cancelling Polling Task: {e}")

        # Ensure application cleanup
        if application:
            try:
                if application.updater.running:
                    await application.updater.stop()
                await application.stop()
                await application.shutdown()
            except Exception as e:
                log.error(f"❌ Error during application shutdown: {e}")
        
        log.info("✅ Bot Shutdown Completed")

# ---------- FastAPI Application ----------
app = FastAPI(
    title="Telegram ID Bot",
    description="Production-Grade Telegram Bot For ID Information",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if APP_ENV == "development" else None,
    redoc_url="/redoc" if APP_ENV == "development" else None,
)

# Add CORS Middleware For Production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if APP_ENV == "development" else [],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ---------- Health Check And Status Routes ----------
@app.get("/", response_class=PlainTextResponse)
async def root():
    return f"✅ Telegram ID Bot Running In Production Mode — {SIGNATURE}"

@app.get("/healthz")
async def health():
    """Kubernetes/Coolify Health Check Endpoint"""
    global application
    
    if not application:
        raise HTTPException(status_code=503, detail="Bot Not Initialized")
    
    try:
        me = await application.bot.get_me()
        return {
            "status": "healthy",
            "bot_username": me.username,
            "timestamp": time.time(),
            "version": "2.0.0"
        }
    except Exception as e:
        log.error(f"Health Check Failed: {e}")
        raise HTTPException(status_code=503, detail="Bot Health Check Failed")

@app.get("/metrics")
async def metrics():
    """Basic Metrics Endpoint For Monitoring"""
    global application, polling_task
    
    if not application:
        return {"error": "Bot Not Initialized"}

    try:
        return {
            "uptime": time.time(),
            "bot_running": bool(application and not shutdown_event.is_set()),
            "polling_task_running": bool(polling_task and not polling_task.done()),
            "updater_running": bool(application.updater.running),
            "version": "2.0.0"
        }
    except Exception as e:
        log.error(f"Metrics Collection Failed: {e}")
        return {"error": "Failed To Collect Metrics"}

@app.get("/status")
async def status():
    """Detailed Status Endpoint"""
    global application
    
    if not application:
        return {"status": "not_initialized"}
    
    try:
        me = await application.bot.get_me()
        return {
            "status": "running",
            "bot_info": {
                "id": me.id,
                "username": me.username,
                "first_name": me.first_name,
                "can_join_groups": me.can_join_groups,
                "can_read_all_group_messages": me.can_read_all_group_messages,
                "supports_inline_queries": me.supports_inline_queries,
            },
            "app_info": {
                "version": "2.0.0",
                "environment": APP_ENV,
                "port": PORT,
                "maintainer": SIGNATURE,
            },
            "system_info": {
                "python_version": sys.version,
                "timestamp": time.time(),
                "shutdown_event_set": shutdown_event.is_set(),
                "polling_task_done": polling_task.done() if polling_task else None,
                "updater_running": application.updater.running if application else None,
            }
        }
    except Exception as e:
        log.error(f"Status Check Failed : {e}")
        return {"status": "error", "message": str(e)}

# ---------- Error Handlers ----------
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    log.error(f"Global Exception: {exc}")
    return {"error": "Internal Server Error", "timestamp": time.time()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "Main:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
        workers=1,
        log_level=LOG_LEVEL.lower()
    )
