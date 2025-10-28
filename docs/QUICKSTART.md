# OCRBox Quick Start Guide

Get OCRBox running in under 5 minutes!

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
# Copy a screenshot or image
cp ~/Pictures/screenshot.png data/watch/

# Watch the logs
docker-compose logs -f
```

### Step 5: Check Results

```bash
# View extracted text
cat data/output/screenshot.txt

# Original image archived here
ls data/archive/
```

**That's it!** Your local OCR service is running. 🎉

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

2. You'll see OCRBox has created:
   - `/ocr_output/` - Extracted text files appear here
   - `/processed/` - Processed images move here
   - `README.txt` - Usage instructions

3. Upload an image or screenshot to the **root folder** (not in subfolders)

4. Watch the logs:
   ```bash
   docker-compose logs -f
   ```

   You'll see:
   ```
   Found 1 new file(s) for your@email.com
   Processing file: screenshot.png
   Uploaded text file to Dropbox: /ocr_output/screenshot.txt
   Moved processed image to: /processed/screenshot.png
   ```

5. Check results in Dropbox:
   - Text file in `/ocr_output/screenshot.txt`
   - Original moved to `/processed/screenshot.png`

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

- 🐛 [Report Issues](https://github.com/stefanahman/ocrbox/issues)
- 💬 [Ask Questions](https://github.com/stefanahman/ocrbox/discussions)
- 📧 Contact: your-email@example.com

---

**Happy OCR-ing!** 🚀

