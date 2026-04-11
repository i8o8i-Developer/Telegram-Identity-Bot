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
from urllib.parse import urlsplit

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse, PlainTextResponse
    from fastapi.middleware.cors import CORSMiddleware
    FASTAPI_AVAILABLE = True
except Exception:
    # Minimal Safe Stubs For FastAPI Types Used Elsewhere In This Module.
    FASTAPI_AVAILABLE = False

    class HTTPException(Exception):
        def __init__(self, status_code=500, detail=None):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    class PlainTextResponse(str):
        pass

    class JSONResponse(dict):
        def __init__(self, content=None, status_code=200):
            super().__init__(content or {})
            self.status_code = status_code

    class CORSMiddleware:
        def __init__(self, *args, **kwargs):
            pass

    class FastAPI:
        def __init__(self, *args, **kwargs):
            # Store Simple Route Lists; Decorators Will Be No-Ops
            self._routes = {}

        def get(self, path, **kwargs):
            def _decorator(fn):
                self._routes[path] = fn
                return fn
            return _decorator

        def post(self, path, **kwargs):
            def _decorator(fn):
                self._routes[path] = fn
                return fn
            return _decorator

        def exception_handler(self, exc_type):
            def _decorator(fn):
                return fn
            return _decorator

        def add_middleware(self, *args, **kwargs):
            return None

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
    from telegram.ext import (
        Application,
        ApplicationBuilder,
        CommandHandler,
        CallbackQueryHandler,
        ContextTypes,
    )
    from telegram.error import TelegramError, Conflict, NetworkError
    TELEGRAM_AVAILABLE = True
except Exception:
    TELEGRAM_AVAILABLE = False

    # Minimal Safe Stubs For Telegram Types Used In This Module.
    class TelegramError(Exception):
        pass

    class Conflict(TelegramError):
        pass

    class NetworkError(TelegramError):
        pass

    class Update:
        pass

    class InlineKeyboardButton:
        def __init__(self, text, callback_data=None):
            self.text = text
            self.callback_data = callback_data

    class InlineKeyboardMarkup:
        def __init__(self, keyboard):
            self.inline_keyboard = keyboard

    class InputFile:
        def __init__(self, fileobj):
            self.file = fileobj

    class ContextTypes:
        DEFAULT_TYPE = object

    class CommandHandler:
        def __init__(self, *args, **kwargs):
            pass

    class CallbackQueryHandler:
        def __init__(self, *args, **kwargs):
            pass

    class _DummyBot:
        async def get_updates(self, *a, **k):
            raise RuntimeError("Telegram Package Not Installed")

        async def get_me(self):
            raise RuntimeError("Telegram Package Not Installed")

    class _DummyUpdater:
        def __init__(self):
            self.running = False

        async def start_polling(self, *a, **k):
            self.running = True

        async def stop(self):
            self.running = False

    class Application:
        def __init__(self):
            self.bot = _DummyBot()
            self.updater = _DummyUpdater()

        async def initialize(self):
            return None

        async def start(self):
            return None

        async def stop(self):
            return None

        async def shutdown(self):
            return None

        def add_handler(self, handler):
            return None

    class ApplicationBuilder:
        def __init__(self):
            pass

        def token(self, *a, **k):
            return self

        def connect_timeout(self, *a, **k):
            return self

        def read_timeout(self, *a, **k):
            return self

        def write_timeout(self, *a, **k):
            return self

        def pool_timeout(self, *a, **k):
            return self

        def get_updates_connect_timeout(self, *a, **k):
            return self

        def get_updates_read_timeout(self, *a, **k):
            return self

        def concurrent_updates(self, *a, **k):
            return self

        def build(self):
            return Application()

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
APP_VERSION = "2.1.0"
WEBHOOK_ENDPOINT = "/webhook"


def build_webhook_url() -> str:
    """Build A Stable Webhook URL From WEBHOOK_URL Environment Variable."""
    base_url = WEBHOOK_BASE_URL.rstrip("/")
    if not base_url:
        return ""
    if base_url.endswith(WEBHOOK_ENDPOINT):
        return base_url
    return f"{base_url}{WEBHOOK_ENDPOINT}"

# ---------- Configuration And Validation ----------
def validate_environment():
    """Validate Required Environment Variables"""
    required_vars = ["TELEGRAM_BOT_TOKEN", "WEBHOOK_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        error_msg = f"Missing Required Environment Variables: {', '.join(missing_vars)}"
        log.error(error_msg)
        raise RuntimeError(error_msg)

    # Validate Bot Token Format
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token or len(bot_token.split(":")) != 2:
        raise RuntimeError("Invalid TELEGRAM_BOT_TOKEN Format")

    webhook_url = build_webhook_url()
    parsed_webhook_url = urlsplit(webhook_url)
    if parsed_webhook_url.scheme not in ("http", "https") or not parsed_webhook_url.netloc:
        raise RuntimeError("WEBHOOK_URL Must Be A Valid Absolute HTTP/HTTPS URL")
    
    log.info("Environment Validation Passed")

BOT_TOKEN = None
APP_ENV = os.getenv("APP_ENV", "production")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))

# Separate Timeouts For Different Operations
# Regular API Calls (get_me, send_message, etc.) - Should Be Reasonably Short
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))

# If Set To A Truthy Value ("1", "true", "yes"), The Health Endpoint Will Skip
# Calling The Telegram API. This Is Useful In Network-Restricted Environments Where
# Outbound Access To Telegram May Be Blocked But You Still Want The Service To Be
# Considered "Healthy" By The Orchestration Platform
SKIP_TELEGRAM_HEALTH_CHECK = os.getenv("SKIP_TELEGRAM_HEALTH_CHECK", "false").lower() in ("1", "true", "yes")

# Sync With Docker/Coolify Defaults
PORT = int(os.getenv("PORT", "5860"))
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_URL", "").strip()
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# ---------- Global State ----------
application: Optional[Application] = None
shutdown_event = asyncio.Event()

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
         InlineKeyboardButton("↩️ Reply ID", callback_data="replyid")],
        [InlineKeyboardButton("💬 Chat/Group ID", callback_data="chatid"),
         InlineKeyboardButton("🏷️ Chat Details", callback_data="chatinfo")],
        [InlineKeyboardButton("👑 Admins", callback_data="admins"),
         InlineKeyboardButton("👥 Member Count", callback_data="members")],
        [InlineKeyboardButton("🧵 Topic ID", callback_data="topicid"),
         InlineKeyboardButton("🧾 Message Info", callback_data="messageinfo")],
        [InlineKeyboardButton("ℹ️ User Info", callback_data="userinfo"),
         InlineKeyboardButton("🗂️ File ID", callback_data="fileid")],
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
        f"↩️ Extract IDs From Replied Messages\n"
        f"💬 Find Chat/Group IDs\n"
        f"🏷️ Inspect Detailed Chat Metadata\n"
        f"🧵 Discover Topic IDs\n"
        f"🧾 Capture Message IDs Instantly\n"
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
        f"↩️ <code>/replyid</code> — ID Of Replied User / Sender Chat\n"
        f"💬 <code>/chatid</code> — Current Chat/Group ID\n"
        f"🏷️ <code>/chatinfo</code> — Detailed Chat Metadata\n"
        f"🧵 <code>/topicid</code> — Topic ID (In Threads)\n\n"
        f"👥 <b>Group Info:</b>\n"
        f"📊 <code>/members</code> — Member Count\n"
        f"👑 <code>/admins</code> — List Administrators\n\n"
        f"📱 <b>Utilities:</b>\n"
        f"🧾 <code>/messageid</code> — Message / Reply / Topic IDs\n"
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
async def cmd_replyid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    replied_msg = msg.reply_to_message

    if not replied_msg:
        await msg.reply_text(
            f"↩️ <b>Reply ID Finder</b>\n"
            f"─────────────────────────\n\n"
            f"❌ <b>No Reply Found</b>\n\n"
            f"📱 Reply To Any User, Bot, Or Anonymous Admin Message\n"
            f"🔄 Then Send <code>/replyid</code> Again\n\n"
            f"💡 <i>This Is The Fastest Way To Capture Someone Else's ID!</i>",
            parse_mode="HTML"
        )
        return

    sender = replied_msg.from_user
    sender_chat = replied_msg.sender_chat
    reply_to_message_id = replied_msg.reply_to_message.message_id if replied_msg.reply_to_message else None
    topic_id = replied_msg.message_thread_id if replied_msg.is_topic_message else None

    if sender:
        username = f"@{sender.username}" if sender.username else "❌ No username"
        await msg.reply_text(
            f"↩️ <b>Reply Target Information</b>\n"
            f"─────────────────────────\n\n"
            f"👤 <b>Name:</b> {sender.full_name}\n"
            f"🆔 <b>User ID:</b> <code>{sender.id}</code>\n"
            f"📛 <b>Username:</b> {username}\n"
            f"🤖 <b>Bot:</b> {'Yes' if sender.is_bot else 'No'}\n"
            f"✉️ <b>Message ID:</b> <code>{replied_msg.message_id}</code>\n"
            f"↩️ <b>Replying To:</b> <code>{reply_to_message_id}</code>\n"
            f"🧵 <b>Topic ID:</b> <code>{topic_id}</code>\n\n"
            f"💡 <i>Tap The Numeric IDs To Copy Them.</i>",
            parse_mode="HTML"
        )
        return

    if sender_chat:
        sender_chat_name = sender_chat.title or sender_chat.username or "Unknown"
        await msg.reply_text(
            f"↩️ <b>Sender Chat Information</b>\n"
            f"─────────────────────────\n\n"
            f"📢 <b>Name:</b> {sender_chat_name}\n"
            f"🆔 <b>Chat ID:</b> <code>{sender_chat.id}</code>\n"
            f"🏷️ <b>Type:</b> {sender_chat.type.title()}\n"
            f"✉️ <b>Message ID:</b> <code>{replied_msg.message_id}</code>\n"
            f"🧵 <b>Topic ID:</b> <code>{topic_id}</code>\n\n"
            f"💡 <i>Useful For Anonymous Admin Or Channel-Linked Messages.</i>",
            parse_mode="HTML"
        )
        return

    await msg.reply_text(
        f"↩️ <b>Reply Target Information</b>\n"
        f"─────────────────────────\n\n"
        f"⚠️ <b>Sender Data Unavailable</b>\n\n"
        f"Telegram Did Not Include User Or Sender Chat Details For That Message.\n"
        f"✉️ <b>Message ID:</b> <code>{replied_msg.message_id}</code>\n\n"
        f"💡 <i>Try Again With A Regular User Or Channel Message.</i>",
        parse_mode="HTML"
    )


@handle_errors
async def cmd_chatinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    try:
        full_chat = await context.bot.get_chat(chat.id)
    except Exception:
        full_chat = chat

    try:
        member_count = await context.bot.get_chat_member_count(chat.id)
    except Exception:
        member_count = None

    chat_name = full_chat.title or full_chat.first_name or "Unknown"
    username = f"@{full_chat.username}" if getattr(full_chat, "username", None) else "❌ No public username"
    description = getattr(full_chat, "description", None) or getattr(full_chat, "bio", None) or "Not available"
    invite_link = getattr(full_chat, "invite_link", None) or "Not available"
    linked_chat_id = getattr(full_chat, "linked_chat_id", None)
    member_line = f"👥 <b>Members:</b> <code>{member_count:,}</code>\n" if member_count is not None else ""
    linked_chat_line = f"🔗 <b>Linked Chat ID:</b> <code>{linked_chat_id}</code>\n" if linked_chat_id else ""

    await update.effective_message.reply_text(
        f"🏷️ <b>Detailed Chat Info</b>\n"
        f"─────────────────────────\n\n"
        f"📝 <b>Name:</b> {chat_name}\n"
        f"🆔 <b>Chat ID:</b> <code>{full_chat.id}</code>\n"
        f"📊 <b>Type:</b> {full_chat.type.title()}\n"
        f"📛 <b>Username:</b> {username}\n"
        f"{member_line}"
        f"{linked_chat_line}"
        f"🧾 <b>Description:</b> {description}\n"
        f"🔗 <b>Invite Link:</b> <code>{invite_link}</code>\n\n"
        f"💡 <i>Handy For Group Setup, Migration, And Support Work.</i>",
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
    
    # Private Chats Don't Have Administrators
    if chat.type == "private":
        await update.effective_message.reply_text(
            f"👑 <b>Administrators</b>\n"
            f"─────────────────────────\n\n"
            f"❌ <b>Not Applicable</b>\n\n"
            f"🔒 Private Chats Don't Have Administrators\n"
            f"📱 Only Groups And Channels Have Admins\n"
            f"🔄 Try In A Group Chat Instead\n\n"
            f"💡 <i>Use /chatid To Get Chat Info!</i>",
            parse_mode="HTML"
        )
        return
    
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
async def cmd_messageid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    reply_to_message_id = msg.reply_to_message.message_id if msg.reply_to_message else "Not a reply"
    topic_id = msg.message_thread_id if msg.is_topic_message else "Not in a topic"
    sender_chat_id = msg.sender_chat.id if msg.sender_chat else "Not sent as chat"

    await msg.reply_text(
        f"🧾 <b>Message Information</b>\n"
        f"─────────────────────────\n\n"
        f"✉️ <b>Message ID:</b> <code>{msg.message_id}</code>\n"
        f"💬 <b>Chat ID:</b> <code>{chat.id}</code>\n"
        f"↩️ <b>Reply To ID:</b> <code>{reply_to_message_id}</code>\n"
        f"🧵 <b>Topic ID:</b> <code>{topic_id}</code>\n"
        f"📢 <b>Sender Chat ID:</b> <code>{sender_chat_id}</code>\n\n"
        f"💡 <i>Useful For Topic Routing, Logging, And Bot Automations.</i>",
        parse_mode="HTML"
    )

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
        elif replied_msg.animation:
            file_id = replied_msg.animation.file_id
            file_type = "🎞️ Animation"
            file_size = getattr(replied_msg.animation, 'file_size', None)
        elif replied_msg.document:
            file_id = replied_msg.document.file_id
            file_type = f"📄 Document ({replied_msg.document.file_name or 'Unknown'})"
            file_size = getattr(replied_msg.document, 'file_size', None)
        elif replied_msg.video:
            file_id = replied_msg.video.file_id
            file_type = "🎥 Video"
            file_size = getattr(replied_msg.video, 'file_size', None)
        elif replied_msg.video_note:
            file_id = replied_msg.video_note.file_id
            file_type = "📹 Video Note"
            file_size = getattr(replied_msg.video_note, 'file_size', None)
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
            f"🎭 Stickers • 🎵 Audio • 🎤 Voice\n"
            f"🎞️ Animations • 📹 Video Notes\n\n"
            f"💡 <i>File IDs Never Expire!</i>",
            parse_mode="HTML"
        )

@handle_errors
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data
    await update.callback_query.answer()
    
    if data == "id":
        await cmd_id(update, context)
    elif data == "replyid":
        await cmd_replyid(update, context)
    elif data == "chatid":
        await cmd_chatid(update, context)
    elif data == "chatinfo":
        await cmd_chatinfo(update, context)
    elif data == "admins":
        await cmd_admins(update, context)
    elif data == "members":
        await cmd_members(update, context)
    elif data == "export":
        await cmd_export(update, context)
    elif data == "userinfo":
        await cmd_userinfo(update, context)
    elif data == "messageinfo":
        await cmd_messageid(update, context)
    elif data == "fileid":
        await cmd_fileid(update, context)
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
        CommandHandler("replyid", cmd_replyid),
        CommandHandler("chatid", cmd_chatid),
        CommandHandler("chatinfo", cmd_chatinfo),
        CommandHandler("topicid", cmd_topicid),
        CommandHandler("members", cmd_members),
        CommandHandler("admins", cmd_admins),
        CommandHandler("export", cmd_export),
        CommandHandler("userinfo", cmd_userinfo),
        CommandHandler("messageid", cmd_messageid),
        CommandHandler("ping", cmd_ping),
        CommandHandler("fileid", cmd_fileid),
        CallbackQueryHandler(on_callback),
    ]
    
    for handler in handlers:
        app.add_handler(handler)
    
    log.info(f"✅ Registered {len(handlers)} Handlers")

# ---------- Application Lifespan ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage Application LifeSpan With Proper Startup and Shutdown"""
    global application
    application_initialized = False
    application_started = False
    
    try:
        # Startup
        log.info("🚀 Starting Telegram ID Bot...")
        shutdown_event.clear()

        # Validate Environment (Moved Here So Import-Time Doesn't Fail When Env Is Missing)
        try:
            validate_environment()
        except Exception as e:
            log.error(f"Environment validation failed during startup: {e}")
            raise

        # Re-Read BOT_TOKEN After Validation
        global BOT_TOKEN
        BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

        # Create The Application With Better Configuration
        # For Webhook Mode, We Don't Need Polling-Related Timeouts
        application = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .connect_timeout(REQUEST_TIMEOUT)  # Connection Establishment: 30s
            .read_timeout(REQUEST_TIMEOUT)      # Regular API Reads: 30s
            .write_timeout(REQUEST_TIMEOUT)     # Regular API Writes: 30s
            .pool_timeout(REQUEST_TIMEOUT)      # Connection Pool: 30s
            .concurrent_updates(True)
            .build()
        )

        # Register Handlers
        register_handlers(application)

        # Start The PTB Application In Webhook Mode Without Starting Polling.
        await application.initialize()
        application_initialized = True
        await application.start()
        application_started = True

        # Set Webhook With Error Handling
        try:
            webhook_url = build_webhook_url()
            allowed_updates = getattr(Update, "ALL_TYPES", None)
            webhook_kwargs = {"url": webhook_url, "drop_pending_updates": False}
            if allowed_updates:
                webhook_kwargs["allowed_updates"] = allowed_updates
            await application.bot.set_webhook(**webhook_kwargs)
            log.info(f"✅ Webhook Set To: {webhook_url}")
        except Exception as webhook_error:
            log.exception(f"❌ Failed To Set Webhook: {webhook_error}")
            if APP_ENV == "production":
                raise RuntimeError("Webhook Registration Failed In Production") from webhook_error
            log.warning("⚠️ Continuing Without Webhook Because APP_ENV Is Not Production")

        log.info(f"✅ Bot Started Successfully — Webhook Active On Port {PORT}")

        yield
        
    except Exception as e:
        log.error(f"❌ Failed To Start Bot: {e}")
        raise
    finally:
        # Shutdown
        log.info("🛑 Shutting Down Bot...")
        
        # Signal shutdown
        shutdown_event.set()
        
        # Ensure Application Cleanup
        if application:
            try:
                if application_started:
                    await application.stop()
                if application_initialized:
                    await application.shutdown()
            except Exception as e:
                log.error(f"❌ Error During Application Shutdown: {e}")
            finally:
                application = None
        
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
        # Return A Not-Initialized Status Instead Of Raising So The Endpoint Remains
        # Reachable; Orchestration Platforms Can Use This For Finer-Grained Checks.
        return {"status": "Not_Initialized", "detail": "Bot Not Initialized"}

    try:
        # For Webhook-Based Bots, We Can Skip The Telegram API Call Since Webhooks
        # Don't Require Constant Polling. This Prevents Network Timeouts In Restricted Environments.
        if SKIP_TELEGRAM_HEALTH_CHECK or APP_ENV == "production":
            return {
                "status": "Healthy",
                "bot_username": "webhook-mode",
                "timestamp": time.time(),
                "version": APP_VERSION,
                "note": "Webhook Mode - Telegram API Check Skipped For Stability"
            }

        me = await application.bot.get_me()
        return {
            "status": "Healthy",
            "bot_username": me.username,
            "timestamp": time.time(),
            "version": APP_VERSION
        }
    except Exception as e:
        # Return Degraded Status Rather Than Raising. This Prevents The Process From
        # Being Killed Immediately By Health Probes When Telegram Is Temporarily
        # Unreachable (e.g., Network Partitions, Short Outages).
        log.error(f"Health Check Failed : {e}")
        return {
            "status": "Degraded",
            "reason": "Telegram_UnReachable",
            "error": str(e),
            "timestamp": time.time(),
            "version": APP_VERSION
        }

@app.get("/metrics")
async def metrics():
    """Basic Metrics Endpoint For Monitoring"""
    global application
    
    if not application:
        return {"error": "Bot Not Initialized"}

    try:
        return {
            "uptime": time.time(),
            "bot_running": bool(application and getattr(application, "running", False) and not shutdown_event.is_set()),
            "webhook_active": True,  # Webhook Is Always Active When App Is Running
            "version": APP_VERSION
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
        webhook_info = await application.bot.get_webhook_info()
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
                "version": APP_VERSION,
                "environment": APP_ENV,
                "port": PORT,
                "maintainer": SIGNATURE,
            },
            "webhook_info": {
                "url": webhook_info.url or build_webhook_url(),
                "pending_update_count": webhook_info.pending_update_count,
                "max_connections": webhook_info.max_connections,
                "ip_address": webhook_info.ip_address,
                "allowed_updates": webhook_info.allowed_updates,
                "last_error_date": webhook_info.last_error_date.isoformat() if webhook_info.last_error_date else None,
                "last_error_message": webhook_info.last_error_message,
            },
            "system_info": {
                "python_version": sys.version,
                "timestamp": time.time(),
                "shutdown_event_set": shutdown_event.is_set(),
                "webhook_url": build_webhook_url(),
            }
        }
    except Exception as e:
        log.error(f"Status Check Failed : {e}")
        return {"status": "error", "message": str(e)}


@app.get("/webhook-info")
async def webhook_info():
    """Inspect The Registered Telegram Webhook For Deployment Debugging."""
    global application

    if not application:
        return {"status": "not_initialized"}

    try:
        info = await application.bot.get_webhook_info()
        return {
            "status": "ok",
            "configured_webhook_url": build_webhook_url(),
            "telegram_webhook": {
                "url": info.url,
                "pending_update_count": info.pending_update_count,
                "max_connections": info.max_connections,
                "ip_address": info.ip_address,
                "allowed_updates": info.allowed_updates,
                "last_error_date": info.last_error_date.isoformat() if info.last_error_date else None,
                "last_error_message": info.last_error_message,
            },
        }
    except Exception as e:
        log.error(f"Webhook Info Check Failed : {e}")
        return {
            "status": "error",
            "configured_webhook_url": build_webhook_url(),
            "message": str(e),
        }

# ---------- Error Handlers ----------
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    log.exception(f"Global Exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "timestamp": time.time()}
    )

# ---------- Webhook Endpoint ----------
@app.post(WEBHOOK_ENDPOINT)
async def webhook(update: Dict[str, Any]):
    """Handle Telegram Webhook Updates"""
    global application
    
    if not application:
        log.error("❌ Webhook Received But Application Not Initialized")
        raise HTTPException(status_code=503, detail="Application Not Initialized")
    
    try:
        # Convert Dict To Update Object
        telegram_update = Update.de_json(update, application.bot)
        
        # Process The Update
        await application.process_update(telegram_update)
        
        return {"status": "ok"}
    except Exception as e:
        log.exception(f"❌ Error Processing Webhook Update : {e}")
        raise HTTPException(status_code=500, detail="Failed To Process Update") from e

if __name__ == "__main__":
    try:
        import uvicorn
    except Exception as e:
        log.error(f"Uvicorn Is Not Available : {e}. The App Cannot Be Served in This Environment Without Uvicorn.")
    else:
        uvicorn.run(
            "Main:app",
            host="0.0.0.0",
            port=PORT,
            reload=False,
            workers=1,
            log_level=LOG_LEVEL.lower()
        )
