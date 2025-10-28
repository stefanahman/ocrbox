# Environment Variables Reference

## Overview

OCRBox uses environment variables for all configuration. This keeps secrets secure and makes deployment flexible.

## Where Environment Variables Are Set

### ✅ GitHub Actions (CI/CD)
**Location:** Automatically handled by GitHub
**What's needed:** Nothing! GitHub provides `GITHUB_TOKEN` automatically
**Action required:** Just push code to trigger builds

### ✅ Production Server
**Location:** `/opt/ocrbox/.env` file
**Permissions:** `600` (owner read/write only)
**Read by:** docker-compose.prod.yml via `env_file: .env`

### ❌ NOT in docker-compose files
**Why:** Secrets should never be hardcoded in compose files
**How it works:** Compose files reference `.env` automatically

## Complete .env File Template

Save this as `/opt/ocrbox/.env` on your server:

```env
# ============================================
# Docker Registry
# ============================================
# Your GitHub repository (for pulling images)
GITHUB_REPOSITORY=stefanahman/ocrbox

# ============================================
# Application Mode
# ============================================
# 'local' for local folder watching
# 'dropbox' for Dropbox integration
MODE=dropbox

# ============================================
# Gemini API (REQUIRED)
# ============================================
# Get key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_actual_api_key_here

# Model to use (default: gemini-2.5-flash-lite)
GEMINI_MODEL=gemini-2.5-flash-lite

# ============================================
# Dropbox OAuth (Required for Dropbox mode)
# ============================================
# Create app at: https://www.dropbox.com/developers/apps
DROPBOX_APP_KEY=your_dropbox_app_key
DROPBOX_APP_SECRET=your_dropbox_app_secret

# Keep as localhost when using SSH tunnel
DROPBOX_REDIRECT_URI=http://localhost:8080/oauth/callback

# Comma-separated emails or account IDs
ALLOWED_ACCOUNTS=you@example.com,friend@example.com

# ============================================
# OAuth Server Configuration
# ============================================
# Port for OAuth authorization server
OAUTH_SERVER_PORT=8080

# Bind address (0.0.0.0 for all interfaces)
OAUTH_SERVER_HOST=0.0.0.0

# Keep OAuth server running after first auth (for multi-user)
OAUTH_ALWAYS_ENABLED=false

# ============================================
# Telegram Notifications (Optional)
# ============================================
# Enable notifications
TELEGRAM_ENABLED=false

# Get token from: https://t.me/BotFather
TELEGRAM_BOT_TOKEN=your_bot_token

# Get chat ID from: https://t.me/userinfobot
TELEGRAM_CHAT_ID=your_chat_id

# ============================================
# Email Notifications (Optional)
# ============================================
# Enable email notifications
EMAIL_ENABLED=false

# SMTP server settings
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587

# Email credentials (use app password for Gmail)
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Sender and recipient
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com

# ============================================
# Processing Options
# ============================================
# Seconds between file checks
POLL_INTERVAL=30

# Max retry attempts for failed OCR
MAX_RETRIES=3

# Initial retry delay in seconds (exponential backoff)
RETRY_DELAY=2

# ============================================
# Logging
# ============================================
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# ============================================
# Storage Paths (Docker internal paths)
# ============================================
# Usually don't need to change these
DATA_DIR=/app/data
```

## Required vs Optional Variables

### Absolutely Required
```env
GITHUB_REPOSITORY=stefanahman/ocrbox  # For production deployments
MODE=local                             # or 'dropbox'
GEMINI_API_KEY=xxx                     # Your Gemini API key
```

### Required for Dropbox Mode
```env
DROPBOX_APP_KEY=xxx
DROPBOX_APP_SECRET=xxx
```

### Optional (Notifications)
```env
TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=xxx

EMAIL_ENABLED=true
EMAIL_USERNAME=xxx
EMAIL_PASSWORD=xxx
# ... other email settings
```

### Optional (Defaults work fine)
```env
GEMINI_MODEL=gemini-2.5-flash-lite
OAUTH_SERVER_PORT=8080
POLL_INTERVAL=30
MAX_RETRIES=3
LOG_LEVEL=INFO
```

## Security Best Practices

### File Permissions
```bash
# Secure your .env file
chmod 600 /opt/ocrbox/.env

# Verify
ls -la /opt/ocrbox/.env
# Should show: -rw------- (600)
```

### Never Commit Secrets
```bash
# .env is already in .gitignore
# Double-check:
cat .gitignore | grep .env
```

### Token Directory Security
```bash
# Token files should have 700 permissions
chmod 700 /opt/ocrbox/data/tokens

# Verify
ls -la /opt/ocrbox/data/
# tokens/ should show: drwx------ (700)
```

## How Docker Compose Reads .env

### docker-compose.prod.yml
```yaml
services:
  ocrbox:
    image: ghcr.io/${GITHUB_REPOSITORY}:latest  # ← Reads from .env
    env_file:
      - .env  # ← Loads all variables from .env file
```

Docker Compose automatically:
1. Reads `.env` file in the same directory
2. Substitutes `${VARIABLE}` in compose file
3. Passes all variables to the container

## Updating Environment Variables

```bash
# 1. Edit .env file
nano /opt/ocrbox/.env

# 2. Restart service to apply changes
sudo systemctl restart ocrbox@$USER

# 3. Verify changes took effect
sudo journalctl -u ocrbox@$USER -n 20
```

## Troubleshooting

### Check what variables are set
```bash
# View .env file (be careful - contains secrets!)
sudo cat /opt/ocrbox/.env

# Check if container has variables
docker exec ocrbox env | grep GEMINI
docker exec ocrbox env | grep DROPBOX
```

### Test specific variable
```bash
# Test Gemini API key
docker exec ocrbox python3 -c "
import os
print('GEMINI_API_KEY is set:', bool(os.getenv('GEMINI_API_KEY')))
"

# Test Dropbox credentials
docker exec ocrbox python3 -c "
import os
print('DROPBOX_APP_KEY:', bool(os.getenv('DROPBOX_APP_KEY')))
print('DROPBOX_APP_SECRET:', bool(os.getenv('DROPBOX_APP_SECRET')))
"
```

## GitHub Actions (No Setup Needed!)

The `.github/workflows/docker-build.yml` workflow needs **NO manual configuration**:

```yaml
# These are automatically provided by GitHub:
permissions:
  contents: read    # ← Automatic
  packages: write   # ← Automatic

- name: Log in to GitHub Container Registry
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}              # ← Automatic
    password: ${{ secrets.GITHUB_TOKEN }}      # ← Automatic
```

### What you DO need to do:
1. Push code to GitHub
2. Wait for workflow to run
3. Make package public (or configure docker login on server)

That's it!

## Summary

| Location | File | Purpose | Commit to Git? |
|----------|------|---------|----------------|
| GitHub Actions | N/A | Uses `GITHUB_TOKEN` (automatic) | N/A |
| Production Server | `/opt/ocrbox/.env` | All secrets and config | ❌ NO! |
| Docker Compose | `docker-compose.prod.yml` | References `.env`, no secrets | ✅ Yes |
| Code | `src/config.py` | Reads from env vars | ✅ Yes |

**Key principle:** Secrets in `.env` files, never in code or compose files!

---

For more details, see [DEPLOYMENT.md](docs/DEPLOYMENT.md)

