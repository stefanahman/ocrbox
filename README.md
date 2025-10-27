# OCRBox 📸→📝

**A lightweight, self-hosted service for automatic OCR processing using Google's Gemini API**

OCRBox automatically extracts text from screenshots and images through Dropbox integration or local folder watching, providing a private and efficient way to convert images into searchable text.

## ✨ Features

- **🤖 Advanced OCR**: Powered by Google Gemini (1.5-flash or 1.5-pro)
- **☁️ Dropbox Integration**: App Folder support with multi-tenant access control
- **🔒 Secure Authorization**: OAuth 2.0 with allowlist validation
- **💻 Development Mode**: Local folder watching for testing
- **📬 Notifications**: Telegram and email support for processing updates
- **🔄 Idempotent Processing**: Files are never processed twice
- **🐳 Docker Ready**: Self-contained deployment with Docker Compose
- **🔐 Privacy First**: All processing happens locally, only image bytes sent to Gemini

## 🏗️ Architecture

```
┌─────────────┐
│   Dropbox   │  ← Users upload images to App Folder
│ App Folder  │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────────┐
│           OCRBox Service                │
│  ┌─────────────┐     ┌──────────────┐  │
│  │   Watcher   │────→│   Gemini     │  │
│  │  (Polling)  │     │  OCR Client  │  │
│  └─────────────┘     └──────────────┘  │
│         │                    │          │
│         ↓                    ↓          │
│  ┌─────────────┐     ┌──────────────┐  │
│  │  Storage    │     │ Notification │  │
│  │  (Tokens &  │     │   Manager    │  │
│  │  Processed) │     │              │  │
│  └─────────────┘     └──────────────┘  │
└─────────────────────────────────────────┘
       │
       ↓
┌─────────────┐
│   Output    │  ← Extracted text files
│  Directory  │
└─────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))
- For Dropbox mode: Dropbox App credentials ([Create app](https://www.dropbox.com/developers/apps))
- For Telegram notifications: Telegram bot token ([Create bot](https://t.me/BotFather))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ocrbox.git
   cd ocrbox
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Configure environment variables** (edit `.env`)
   ```env
   # Required
   GEMINI_API_KEY=your_gemini_api_key
   MODE=local  # or 'dropbox'
   
   # For Dropbox mode
   DROPBOX_APP_KEY=your_app_key
   DROPBOX_APP_SECRET=your_app_secret
   ALLOWED_ACCOUNTS=user@example.com
   
   # For notifications
   TELEGRAM_ENABLED=true
   TELEGRAM_BOT_TOKEN=your_bot_token
   TELEGRAM_CHAT_ID=your_chat_id
   ```

4. **Start the service**
   ```bash
   docker-compose up -d
   ```

### Local Development Mode

Perfect for testing without Dropbox:

```bash
# Set MODE=local in .env
MODE=local

# Start service
docker-compose up

# In another terminal, add images to watch folder
cp screenshot.png data/watch/

# Check output
cat data/output/screenshot.txt
```

### Dropbox Mode

For production multi-user deployment:

1. **Create Dropbox App**
   - Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
   - Create new "Scoped App" with "App folder" access
   - Get App Key and App Secret
   - Set Redirect URI: `http://localhost:8080/oauth/callback`

2. **Configure allowlist**
   ```env
   ALLOWED_ACCOUNTS=dbid:AAH4f99T0taONIb,user@example.com,another@example.com
   ```

3. **Start and authorize**
   ```bash
   docker-compose up
   
   # Visit http://localhost:8080
   # Click "Authorize with Dropbox"
   # Grant permissions
   ```

4. **How it works**
   - OCRBox automatically creates required folders on first run:
     - `/ocr_output/` - For extracted text files
     - `/processed/` - For processed images
     - `README.txt` - Usage instructions
   - Upload images or screenshots to your App Folder root
   - OCRBox processes them automatically (every 30 seconds)
   - Extracted text appears in `/ocr_output/`
   - Processed images move to `/processed/`

5. **Monitor logs**
   ```bash
   docker-compose logs -f
   ```

## 📋 Configuration Reference

### Core Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MODE` | Operation mode (`local` or `dropbox`) | `local` | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | - | Yes |
| `GEMINI_MODEL` | Gemini model to use | `gemini-1.5-flash` | No |
| `LOG_LEVEL` | Logging verbosity | `INFO` | No |

### Dropbox Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DROPBOX_APP_KEY` | Dropbox app key | - | Yes (Dropbox mode) |
| `DROPBOX_APP_SECRET` | Dropbox app secret | - | Yes (Dropbox mode) |
| `DROPBOX_REDIRECT_URI` | OAuth callback URL | `http://localhost:8080/oauth/callback` | No |
| `ALLOWED_ACCOUNTS` | Comma-separated account IDs/emails | - | No |

### Notification Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TELEGRAM_ENABLED` | Enable Telegram notifications | `false` | No |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | - | Yes (if enabled) |
| `TELEGRAM_CHAT_ID` | Target chat ID | - | Yes (if enabled) |
| `EMAIL_ENABLED` | Enable email notifications | `false` | No |
| `EMAIL_SMTP_HOST` | SMTP server host | `smtp.gmail.com` | No |
| `EMAIL_SMTP_PORT` | SMTP server port | `587` | No |

### Processing Options

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POLL_INTERVAL` | Seconds between polls | `30` | No |
| `MAX_RETRIES` | Maximum API retry attempts | `3` | No |
| `RETRY_DELAY` | Initial retry delay (seconds) | `2` | No |

## 🔐 Security & Access Control

### Multi-Tenant Allowlist

OCRBox supports multiple users with strict account validation:

```env
ALLOWED_ACCOUNTS=dbid:AAH4f99T0taONIb-OurWxbNQ6ywGRopQngc,user@example.com
```

- Only allowlisted accounts can authorize
- Each user gets isolated App Folder access
- Tokens stored securely with restrictive permissions (600)
- OAuth uses PKCE for enhanced security

### Adding Additional Users

To allow multiple users to authorize after the first user:

1. **Enable multi-user mode** in `.env`:
   ```env
   OAUTH_ALWAYS_ENABLED=true
   ```

2. **Add their email to allowlist**:
   ```env
   ALLOWED_ACCOUNTS=your@email.com,girlfriend@email.com,friend@email.com
   ```

3. **Update Dropbox redirect URI** for network access (optional):
   ```env
   DROPBOX_REDIRECT_URI=http://YOUR_LOCAL_IP:8080/oauth/callback
   ```
   
   Get your local IP: `ipconfig getifaddr en0` (macOS) or `hostname -I` (Linux)

4. **Restart the service**:
   ```bash
   docker-compose restart
   ```

5. **Share authorization URL** with new users:
   ```
   http://YOUR_LOCAL_IP:8080  (same network)
   or
   http://localhost:8080  (same computer)
   ```

The OAuth server now runs continuously alongside the file watcher, allowing new users to authorize at any time!

### Token Management

Tokens are stored as JSON files in `data/tokens/`:
- One file per user
- File permissions: `0600` (owner read/write only)
- Includes refresh tokens for automatic renewal
- Can be manually revoked by deleting the file

### Revoking Access

**Method 1: Delete token file**
```bash
docker-compose exec ocrbox rm /app/data/tokens/dbid_*.json
```

**Method 2: Dropbox settings**
- Visit [Dropbox Connected Apps](https://www.dropbox.com/account/connected_apps)
- Remove OCRBox from connected apps

## 📬 Notifications

### Telegram Setup

1. Create a bot via [@BotFather](https://t.me/BotFather)
2. Get your chat ID from [@userinfobot](https://t.me/userinfobot)
3. Configure in `.env`:
   ```env
   TELEGRAM_ENABLED=true
   TELEGRAM_BOT_TOKEN=110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
   TELEGRAM_CHAT_ID=123456789
   ```

Notification format:
```
✅ OCR Processing Complete

File: screenshot.png
Time: 2025-10-27 14:30:00
Account: user@example.com
Output: /app/data/output/screenshot.txt
Characters: 1,234

Text Preview:
Hello world...
```

### Email Setup

For Gmail:
1. Enable 2FA on your Google account
2. Create an [App Password](https://myaccount.google.com/apppasswords)
3. Configure:
   ```env
   EMAIL_ENABLED=true
   EMAIL_SMTP_HOST=smtp.gmail.com
   EMAIL_SMTP_PORT=587
   EMAIL_USERNAME=your_email@gmail.com
   EMAIL_PASSWORD=your_app_password
   EMAIL_FROM=your_email@gmail.com
   EMAIL_TO=recipient@example.com
   ```

## 🔧 Maintenance

### View Logs

```bash
# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100
```

### Check Processing Stats

```bash
docker-compose exec ocrbox python -c "
from src.storage import ProcessedFilesDB
db = ProcessedFilesDB('/app/data/processed.db')
print(db.get_stats())
"
```

### Backup Data

```bash
# Backup tokens and database
tar -czf ocrbox-backup-$(date +%Y%m%d).tar.gz data/
```

### Update Service

```bash
git pull
docker-compose build --no-cache
docker-compose up -d
```

## 🐛 Troubleshooting

### "No authorized accounts found"

**Solution**: Complete OAuth flow by visiting `http://localhost:8080` after starting in Dropbox mode.

### "Account not in allowlist"

**Solution**: Add the account email or ID to `ALLOWED_ACCOUNTS` in `.env` and restart.

### "Failed to extract text after X attempts"

**Possible causes**:
- Invalid Gemini API key
- Rate limiting (wait and retry)
- Network issues
- Image format not supported

**Solution**: Check logs for specific error, verify API key, ensure network connectivity.

### Notifications not sending

**Solution**: 
- Verify credentials in `.env`
- Check `docker-compose logs` for error messages
- Test bot token: `curl https://api.telegram.org/bot<TOKEN>/getMe`

## 📊 Supported Image Formats

- PNG (`.png`)
- JPEG (`.jpg`, `.jpeg`)
- GIF (`.gif`)
- WebP (`.webp`)
- BMP (`.bmp`)
- TIFF (`.tiff`, `.tif`)

## 🛣️ Roadmap

- [ ] Web dashboard for monitoring
- [ ] Support for additional OCR engines (Tesseract, Azure Vision)
- [ ] Batch processing API endpoint
- [ ] PDF support
- [ ] Custom output templates
- [ ] Webhook support for integrations
- [ ] Multi-language OCR optimization

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- [Google Gemini](https://deepmind.google/technologies/gemini/) for powerful OCR capabilities
- [Dropbox API](https://www.dropbox.com/developers) for seamless cloud integration
- [Watchdog](https://github.com/gorakhargosh/watchdog) for filesystem monitoring

## 💬 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](https://github.com/yourusername/ocrbox/issues)
- 💡 [Discussions](https://github.com/yourusername/ocrbox/discussions)

---

**Built with ❤️ for privacy-conscious automation**

