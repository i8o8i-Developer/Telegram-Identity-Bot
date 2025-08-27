# 🔑 Telegram Identity Bot

A Lightweight Telegram Bot That Helps You Fetch **IDs, Chat Info, User Info, Admins, And More**.
It Works With **FastAPI** + **Python-Telegram-Bot** And Is Deployable To **Google Cloud Run**.

👉 Live Demo: [TeleIdentity\_Bot](https://t.me/TeleIdentity_Bot)
👉 Cloud Run: [Web Service](https://telegram-identity-bot-1086929523482.europe-west1.run.app/)

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
* [Google Cloud Run](https://cloud.google.com/run) – Serverless Hosting

---

## 📦 Installation

### 1️⃣ Clone Repository

```bash
git clone https://github.com/YourUsername/Telegram-Identity-Bot.git
cd Telegram-Identity-Bot
```

### 2️⃣ Setup Virtual Environment

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

```bash
uvicorn Main:app --reload --port 8080
```

Bot will run in polling mode + FastAPI server available at `http://127.0.0.1:8080`

---

## ☁️ Deploy To Google Cloud Run

### 1️⃣ Build Docker Image

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/telegram-identity-bot
```

### 2️⃣ Deploy To Cloud Run

```bash
gcloud run deploy telegram-identity-bot \
  --image gcr.io/YOUR_PROJECT_ID/telegram-identity-bot \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --set-env-vars TELEGRAM_BOT_TOKEN=YOUR_TOKEN
```

---

## 📋 Available Commands

| Command     | Description                          |
| ----------- | ------------------------------------ |
| `/start`    | Show Main Menu                       |
| `/help`     | Show Help Message                    |
| `/id`       | Show Your Telegram ID                |
| `/chatid`   | Show Current Chat ID                 |
| `/topicid`  | Show Topic ID (If In Thread)         |
| `/members`  | Get Chat Member Count                |
| `/admins`   | List Chat Admins                     |
| `/export`   | Export Chat Snapshot As JSON         |
| `/userinfo` | Show Your User Info                  |
| `/ping`     | Test Bot Latency                     |
| `/fileid`   | Get File ID Of Media (Reply To File) |

---

## 🐳 Docker Usage (Optional)

```bash
docker build -t telegram-identity-bot .
docker run -e TELEGRAM_BOT_TOKEN=YOUR_TOKEN -p 8080:8080 telegram-identity-bot
```

---

## 📜 License

This Project Is Licensed Under The **MIT License** – You Are Free To Use, Modify, And Distribute.
