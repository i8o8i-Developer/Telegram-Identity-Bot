# Telegram Identity Bot

A Lightweight Telegram Bot That Helps You Fetch IDs, Chat Info, User Info, Admins, And More.
It Works With FastAPI + Python-Telegram-Bot And Is Deployable To Coolify.

👉 Live Demo: [TeleIdentity_Bot](https://t.me/TeleIdentity_Bot)

<a href="https://www.producthunt.com/products/telegram-identity-bot/reviews?utm_source=badge-product_review&utm_medium=badge&utm_source=badge-telegram&#0045;identity&#0045;bot" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/product_review.svg?product_id=1110182&theme=dark" alt="Telegram&#0032;Identity&#0032;Bot - Telegram&#0032;Identity&#0032;&#0038;&#0032;Chat&#0032;Management&#0032;Tool&#0032;For&#0032;Power&#0032;Users | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>
<a href="https://www.producthunt.com/products/telegram-identity-bot?utm_source=badge-follow&utm_medium=badge&utm_source=badge-telegram&#0045;identity&#0045;bot" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/follow.svg?product_id=1110182&theme=dark" alt="Telegram&#0032;Identity&#0032;Bot - Telegram&#0032;Identity&#0032;&#0038;&#0032;Chat&#0032;Management&#0032;Tool&#0032;For&#0032;Power&#0032;Users | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>


## Features

* 👤 Get Your Telegram User ID
* ↩️ Extract User / Sender Chat IDs From Replied Messages
* 💬 Get Current Chat/Group ID
* 🏷️ Inspect Detailed Chat Metadata
* 🧵 Fetch Topic IDs In Threaded Groups
* 🧾 Show Message, Reply, And Topic IDs
* 👥 Count Members In A Chat/Group
* 👑 List Group Admins
* 📦 Export Chat Snapshot As JSON
* ℹ️ Show Detailed User Info
* 🏓 Check Bot Latency With `/ping`
* 🆔 Extract File IDs Of Media Files
* 🌐 Inspect Registered Telegram Webhook At `/webhook-info`


## TechStack

* [Python 3.11+](https://www.python.org/)
* [FastAPI](https://fastapi.tiangolo.com/) – For Web Server & Health Checks
* [python-telegram-bot v21](https://github.com/python-telegram-bot/python-telegram-bot) – For Telegram Bot Logic
* [Uvicorn](https://www.uvicorn.org/) / [Gunicorn](https://gunicorn.org/) – For Production Deployment
* [Coolify](https://coolify.io/) – Server Hosting


## Installation

### 1. CloneRepository

```bash
git clone https://github.com/i8o8i-Developer/Telegram-Identity-Bot.git
cd Telegram-Identity-Bot
```

### 2. SetupVirtualEnvironment

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / Mac
.venv\Scripts\activate      # Windows
```

### 3. InstallRequirements

```bash
pip install -r Requirements.txt
```

### 4. EnvironmentVariables

Create `.env` file:

```ini
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
BOT_SIGNATURE="i8o8i Developer"
PORT=5860
WEBHOOK_URL=https://your-domain.com
WEBHOOK_DOMAIN=your-domain.com
```

### 5. RunLocally

```bash
uvicorn Main:app --reload --port 5860
```

The Bot Runs In Webhook Mode And Exposes FastAPI Endpoints At `http://127.0.0.1:5860`.


## Deploy To Coolify

### 1. Build And Push Docker Image

```bash
docker build -t telegram-identity-bot .
docker tag telegram-identity-bot i8o8i-Developer/telegram-identity-bot:latest
docker push i8o8i-Developer/telegram-identity-bot:latest
```

### 2. Configure Coolify

- Set The App Port To `5860`.
- Add Environment Variables: `TELEGRAM_BOT_TOKEN`, `WEBHOOK_URL`, `WEBHOOK_DOMAIN`, `BOT_SIGNATURE`, `APP_ENV=production`.
- Deploy The Image.

Coolify Will Use The Health Endpoint `/healthz` To Verify The Service.
Use `/webhook-info` or `/status` after deploy to confirm Telegram is pointing at the expected webhook.


## Available Commands

| Command | Description |
| --- | --- |
| `/start` | Show Main Menu |
| `/help` | Show Help Message |
| `/id` | Show Your Telegram ID |
| `/replyid` | Show ID Of Replied User Or Sender Chat |
| `/chatid` | Show Current Chat ID |
| `/chatinfo` | Show Detailed Chat Metadata |
| `/topicid` | Show Topic ID (If In Thread) |
| `/members` | Get Chat Member Count |
| `/admins` | List Chat Admins |
| `/messageid` | Show Current Message / Reply / Topic IDs |
| `/export` | Export Chat Snapshot As JSON |
| `/userinfo` | Show Your User Info |
| `/ping` | Test Bot Latency |
| `/fileid` | Get File ID Of Media (Reply To File) |


## DockerUsage

Run The Production Image Locally (Port 5860):

```bash
docker build -t telegram-identity-bot .
docker run -e TELEGRAM_BOT_TOKEN=YOUR_TOKEN -e WEBHOOK_URL=https://your-domain.com -e PORT=5860 -p 5860:5860 telegram-identity-bot
```


## License

This Project Is Licensed Under The MIT License — You Are Free To Use, Modify, And Distribute.


Maintained By: i8o8i Developer

Now You Can Do Your Edits And Changes In New Branch Named Developement
