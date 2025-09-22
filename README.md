# 🔑 Telegram Identity Bot

A Lightweight Telegram Bot That Helps You Fetch **IDs, Chat Info, User Info, Admins, And More**.
It Works With **FastAPI** + **Python-Telegram-Bot** And Is Deployable To **Google Cloud Run**.

👉 Live Demo: [TeleIdentity\_Bot](https://t.me/TeleIdentity_Bot)
👉 Cloud Run: [Web Service](https://bot.durgaaisolutions.in)

<a href="https://www.producthunt.com/products/telegram-identity-bot/reviews?utm_source=badge-product_review&utm_medium=badge&utm_source=badge-telegram&#0045;identity&#0045;bot" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/product_review.svg?product_id=1110182&theme=dark" alt="Telegram&#0032;Identity&#0032;Bot - Telegram&#0032;Identity&#0032;&#0038;&#0032;Chat&#0032;Management&#0032;Tool&#0032;For&#0032;Power&#0032;Users | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>
<a href="https://www.producthunt.com/products/telegram-identity-bot?utm_source=badge-follow&utm_medium=badge&utm_source=badge-telegram&#0045;identity&#0045;bot" target="_blank"><img src="https://api.producthunt.com/widgets/embed-image/v1/follow.svg?product_id=1110182&theme=dark" alt="Telegram&#0032;Identity&#0032;Bot - Telegram&#0032;Identity&#0032;&#0038;&#0032;Chat&#0032;Management&#0032;Tool&#0032;For&#0032;Power&#0032;Users | Product Hunt" style="width: 250px; height: 54px;" width="250" height="54" /></a>
---

## ✨ Features

* 👤 Get Your **Telegram User ID**
* 💬 Get Current **Chat/Group ID**
* 🧵 Fetch **Topic IDs** In Threaded Groups
* 👥 Count Members In A Chat/Group
* 👑 List Group **Admins**
* 📦 Export Chat Snapshot As **JSON**
* ℹ️ Show Detailed **User Info**
* 🏓 Check Bot Latency With `/ping`
* 🆔 Extract **File IDs** Of Media Files

---

## ⚙️ Tech Stack

* [Python 3.11+](https://www.python.org/)
* [FastAPI](https://fastapi.tiangolo.com/) – For Web Server & Health Checks
* [python-telegram-bot v21](https://github.com/python-telegram-bot/python-telegram-bot) – For Telegram Bot Logic
* [Uvicorn](https://www.uvicorn.org/) / [Gunicorn](https://gunicorn.org/) – For Production Deployment
* [Google Cloud Run](https://cloud.google.com/run) – Server Hosting

---

## 📦 Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/i8o8i-Developer/Telegram-Identity-Bot.git
cd Telegram-Identity-Bot
```

### 2️⃣ Setup Virtual Environment

```bash
python -m venv .venv
```bash
python -m venv .venv
source .venv/bin/activate   # Linux / Mac
.venv\Scripts\activate      # Windows
```

### 3️⃣ Install Requirements

```bash
pip install -r Requirements.txt
```

### 4️⃣ Environment Variables

Create `.env` file:

```ini
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
```

### 5️⃣ Run Locally

# 🔑 Telegram Identity Bot

A Lightweight Telegram Bot That Helps You Fetch IDs, Chat Info, User Info, Admins, And More. The Bot Is Production-Ready, Uses FastAPI For Health Endpoints, And Runs The Telegram Polling Worker In The Background.

👉 Live Demo: [teleidentity_bot](https://t.me/TeleIdentity_Bot)

---

## ✨ Features

- 👤 Get Your Telegram User Id
- 💬 Get Current Chat/Group Id
- 🧵 Fetch Topic Ids In Threaded Groups
- 👥 Count Members In A Chat/Group
- 👑 List Group Admins
- 📦 Export Chat Snapshot As Json
- ℹ️ Show Detailed User Info
- 🏓 Check Bot Latency With <code>/ping</code>
- 🆔 Extract File Ids Of Media Files

---

## ⚙️ Tech Stack

- Python 3.11+
- Fastapi – Web Server And Health Checks
- Python-Telegram-Bot v21 – Telegram Bot Logic
- Gunicorn + Uvicorn Workers – Production Server
- Coolify / Cloud Run – Deployment Targets

---

## 📦 Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/i8o8i-Developer/Telegram-Identity-Bot.git
cd Telegram-Identity-Bot
```

### 2️⃣ Setup Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate   # linux / mac
.venv\Scripts\activate      # windows
```

### 3️⃣ Install Requirements

```bash
pip install -r Requirements.txt
```

### 4️⃣ Environment Variables

Create A `.env` File With Your Bot Token:

```ini
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
BOT_SIGNATURE="i8o8i Developer"
PORT=3000
```

### 5️⃣ Run Locally (Development)

```bash
uvicorn Main:app --reload --port 3000
```

The Bot Runs In Polling Mode And Exposes Fastapi Endpoints At `http://127.0.0.1:3000`.

---

## ☁️ Deploy To Coolify (Recommended)

### 1️⃣ Build And Push Docker Image

```bash
docker build -t telegram-identity-bot .
docker tag telegram-identity-bot i8o8i-Developer/telegram-identity-bot:latest
docker push i8o8i-Developer/telegram-identity-bot:latest
```

### 2️⃣ Configure Coolify

- Set The App Port To `3000`.
- Add Environment Variables: `TELEGRAM_BOT_TOKEN`, `BOT_SIGNATURE`, `APP_ENV=production`.
- Deploy The Image.

Coolify Will Use The Health Endpoint `/healthz` To Verify The Service.

---

## 📋 Available Commands

| Command | Description |
| --- | --- |
| <code>/start</code> | Show Main Menu |
| <code>/help</code> | Show Help Message |
| <code>/id</code> | Show Your Telegram Id |
| <code>/chatid</code> | Show Current Chat Id |
| <code>/topicid</code> | Show Topic Id (If In Thread) |
| <code>/members</code> | Get Chat Member Count |
| <code>/admins</code> | List Chat Admins |
| <code>/export</code> | Export Chat Snapshot As Json |
| <code>/userinfo</code> | Show Your User Info |
| <code>/ping</code> | Test Bot Latency |
| <code>/fileid</code> | Get File Id Of Media (Reply To File) |

---

## 🐳 Docker Usage (Optional)

Run The Production Image Locally (Port 3000):

```bash
docker build -t telegram-identity-bot .
docker run -e TELEGRAM_BOT_TOKEN=YOUR_TOKEN -e PORT=3000 -p 3000:3000 telegram-identity-bot
```

---

## 📜 License

This Project Is Licensed Under The Mit License — You Are Free To Use, Modify, And Distribute.

---

Maintained By: i8o8i Developer
