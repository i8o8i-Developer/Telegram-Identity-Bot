# Telegram ID Bot - Production Ready

## 🚀 Production Deployment on Coolify

This bot is optimized for production deployment on Coolify with the following features:

### ✅ Production Features
- ✅ Port 3000 (Coolify compatible)
- ✅ Multi-stage Docker build for optimization
- ✅ Non-root user for security
- ✅ Health checks and monitoring endpoints
- ✅ Graceful shutdown handling
- ✅ Production logging with file rotation
- ✅ Error handling and recovery
- ✅ Environment validation
- ✅ CORS middleware
- ✅ Gunicorn with Uvicorn workers

### 🔧 Configuration

#### Required Environment Variables
```bash
TELEGRAM_BOT_TOKEN=
```

#### Optional Environment Variables
```bash
APP_ENV=production
LOG_LEVEL=INFO
PORT=3000
MAX_RETRIES=3
REQUEST_TIMEOUT=30
```

### 🐳 Coolify Deployment

1. **Create a new project** in Coolify
2. **Connect your repository** containing this code
3. **Set environment variables:**
   - `TELEGRAM_BOT_TOKEN`: Get from @BotFather on Telegram
4. **Configure port:** Set to `3000` (default)
5. **Deploy!**

### 📊 Health Check Endpoints

- `GET /` - Basic status
- `GET /healthz` - Kubernetes-style health check
- `GET /metrics` - Basic metrics
- `GET /status` - Detailed status information

### 🔍 Bot Commands

- `/start` - Show interactive menu
- `/id` - Get your Telegram ID
- `/chatid` - Get chat/group ID
- `/topicid` - Get topic ID (for supergroups)
- `/members` - Get member count
- `/admins` - List chat administrators
- `/export` - Export chat info as JSON
- `/userinfo` - Show detailed user information
- `/ping` - Test bot latency
- `/fileid` - Get file ID from media

### 🛡️ Security Features

- Non-root Docker user
- Environment variable validation
- Error handling without data exposure
- CORS protection
- Request timeouts
- Input validation

### 📈 Monitoring

The bot includes built-in monitoring endpoints:
- Health checks for uptime monitoring
- Metrics endpoint for basic statistics
- Structured logging for debugging

### 🚨 Troubleshooting

1. **Bot not starting?**
   - Check `TELEGRAM_BOT_TOKEN` is set correctly
   - Verify bot token format (should contain `:`)

2. **Health check failing?**
   - Ensure port 3000 is accessible
   - Check logs for startup errors

3. **Commands not working?**
   - Verify bot has necessary permissions
   - Check Telegram API rate limits

### 📋 Deployment Checklist

- [ ] Get bot token from @BotFather
- [ ] Set `TELEGRAM_BOT_TOKEN` environment variable
- [ ] Configure Coolify project
- [ ] Deploy and test health endpoints
- [ ] Test bot commands in Telegram

---

**Bot Version:** 2.0.0  
**Python Version:** 3.11  
**Port:** 3000  
**Platform:** Coolify Ready