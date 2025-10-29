# OCRBox v2 Quick Start Guide

Get OCRBox v2 running in under 5 minutes with smart tagging!

## Prerequisites

- Docker and Docker Compose installed
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## Local Mode (Development)

Perfect for testing OCR functionality without Dropbox.

### Step 1: Clone and Setup

```bash
git clone <your-repo-url> ocrbox
cd ocrbox
./scripts/setup.sh
```

### Step 2: Configure API Key

Edit `.env` and set your Gemini API key:

```env
MODE=local
GEMINI_API_KEY=your_actual_api_key_here
```

### Step 3: Start the Service

```bash
docker-compose up
```

You should see:
```
ocrbox  | ============================================================
ocrbox  | OCRBox - Self-Hosted OCR Service
ocrbox  | ============================================================
ocrbox  | Mode: local
ocrbox  | Ready to process images!
```

### Step 4: Test OCR

In a new terminal, add an image:

```bash
# Copy a screenshot or image to Inbox (v2)
cp ~/Pictures/screenshot.png data/Inbox/

# Watch the logs
docker-compose logs -f
```

### Step 5: Check Results (v2)

```bash
# List tagged output files
ls data/Outbox/
# Example output: [receipts]_grocery-bill.txt

# View extracted text with tags
cat data/Outbox/[receipts]_grocery-bill.txt

# Check processing logs
ls data/Logs/
# llm_responses/ processing/ categories/ errors/

# Original image archived here
ls data/Archive/
```

###  Step 6: Customize Tags (Optional)

```bash
# Edit tags file
nano data/Outbox/tags.txt

# Add your own categories:
# groceries
# projects
# family
# etc.
```

**That's it!** Your local OCR v2 service is running with smart tagging! 🎉

## Dropbox Mode (Production)

For multi-user cloud integration.

### Step 1: Create Dropbox App

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Click "Create app"
3. Choose:
   - **API**: Scoped access
   - **Access**: App folder
   - **Name**: `OCRBox-YourName`
4. Go to Settings tab:
   - Copy **App key** and **App secret**
   - Set **Redirect URI**: `http://localhost:8080/oauth/callback`

### Step 2: Configure Environment

Edit `.env`:

```env
MODE=dropbox
GEMINI_API_KEY=your_gemini_key
DROPBOX_APP_KEY=your_app_key
DROPBOX_APP_SECRET=your_app_secret
ALLOWED_ACCOUNTS=your_email@example.com
```

### Step 3: Start and Authorize

```bash
docker-compose up
```

You should see:
```
ocrbox  | Starting OAuth authorization server...
ocrbox  | Visit http://localhost:8080 to begin authorization
```

1. Open `http://localhost:8080` in your browser
2. Click "Authorize with Dropbox"
3. Grant permissions
4. You'll see "Authorization Successful!"

The service will automatically restart in watcher mode.

### Step 4: Test Dropbox Integration

1. Open Dropbox and navigate to:
   ```
   Apps → OCRBox-YourName
   ```

2. You'll see OCRBox v2 has created:
   - `/Inbox/` - Drop images here for processing
   - `/Outbox/` - Tagged text files appear here
   - `/Archive/` - Processed images move here
   - `/Logs/` - Processing logs
   - `/Outbox/tags.txt` - Customize your tags
   - `README.txt` - Usage instructions

3. Upload an image or screenshot to `/Inbox/`

4. Watch the logs:
   ```bash
   docker-compose logs -f
   ```
   
   You'll see:
   ```
   Found 1 new file(s) for your@email.com
   Processing file: screenshot.png
   Tags: [receipts] (95%), [shopping] (82%)
   Generated title: coffee-purchase
   Uploaded text file to Dropbox: /Outbox/[receipts][shopping]_coffee-purchase.txt
   Moved processed image to: /Archive/screenshot.png
   ```

5. Check results in Dropbox:
   - Tagged text file in `/Outbox/[receipts][shopping]_coffee-purchase.txt`
   - Original moved to `/Archive/screenshot.png`
   - Detailed logs in `/Logs/`

**Done!** Your Dropbox OCR service is live. 📸→📝

## Enable Notifications (Optional)

### Telegram Setup

1. **Create a bot**:
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Send `/newbot` and follow instructions
   - Copy the bot token

2. **Get your chat ID**:
   - Message [@userinfobot](https://t.me/userinfobot)
   - Copy your chat ID

3. **Configure**:
   ```env
   TELEGRAM_ENABLED=true
   TELEGRAM_BOT_TOKEN=110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
   TELEGRAM_CHAT_ID=123456789
   ```

4. **Restart**:
   ```bash
   docker-compose restart
   ```

You'll now receive notifications like:
```
✅ OCR Processing Complete

File: screenshot.png
Time: 2025-10-27 14:30:00
Characters: 1,234

Text Preview:
Hello world...
```

## Common Commands

```bash
# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down

# Restart service
docker-compose restart

# Rebuild after code changes
docker-compose build --no-cache
docker-compose up -d

# Check processing stats
docker-compose exec ocrbox python -c "
from src.storage import ProcessedFilesDB
db = ProcessedFilesDB('/app/data/processed.db')
print(db.get_stats())
"
```

## Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs

# Common issues:
# 1. GEMINI_API_KEY not set → Edit .env
# 2. Port 8080 in use → Change OAUTH_SERVER_PORT in .env
# 3. Permission issues → chmod 700 data/tokens
```

### OCR not working

```bash
# Enable debug logging
echo "LOG_LEVEL=DEBUG" >> .env
docker-compose restart
docker-compose logs -f

# Test Gemini API
docker-compose exec ocrbox python -c "
import google.generativeai as genai
import os
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
print('API key works!')
"
```

### Dropbox authorization fails

1. Check redirect URI matches exactly: `http://localhost:8080/oauth/callback`
2. Verify app key and secret are correct
3. Check if account is in `ALLOWED_ACCOUNTS`

## Next Steps

- 📖 Read the [Full Documentation](../README.md)
- 🏗️ Learn about [Architecture](ARCHITECTURE.md)
- 🤝 See [Contributing Guide](../CONTRIBUTING.md)
- 🔧 Advanced [Configuration Options](../README.md#configuration-reference)

## Support

- 🐛 [Report Issues](https://github.com/yourusername/ocrbox/issues)
- 💬 [Ask Questions](https://github.com/yourusername/ocrbox/discussions)
- 📧 Contact: your-email@example.com

---

**Happy OCR-ing!** 🚀

