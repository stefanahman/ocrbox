# OCRBox Production Deployment Guide

Complete guide for deploying OCRBox on your own server using systemd and Docker.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [SSH Tunnel for OAuth](#ssh-tunnel-for-oauth)
- [Service Management](#service-management)
- [Updating](#updating)
- [Monitoring](#monitoring)
- [Backup & Restore](#backup--restore)
- [Security Best Practices](#security-best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

OCRBox uses a modern CI/CD approach for production deployments:

- **GitHub Actions** automatically builds Docker images on every push to `main`
- **GitHub Container Registry (ghcr.io)** hosts the images
- **Production servers** pull pre-built images (no build time, consistent deployments)
- **Systemd** manages the service lifecycle
- **SSH tunnels** provide secure OAuth access without exposing the server

## Prerequisites

### Server Requirements

- **OS**: Ubuntu 20.04+ (or any Linux with systemd)
- **RAM**: 512MB minimum, 1GB recommended
- **Disk**: 2GB+ free space
- **User**: Non-root user with sudo access
- **SSH**: SSH key-based authentication configured

### Software Requirements

1. **Docker** (20.10+)
   ```bash
   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Add user to docker group
   sudo usermod -aG docker $USER

   # Log out and back in for group changes to take effect
   ```

2. **Docker Compose** (2.0+)
   ```bash
   # Usually included with Docker, verify:
   docker compose version
   ```

3. **Git**
   ```bash
   sudo apt update && sudo apt install -y git
   ```

### API Keys & Credentials

1. **Gemini API Key** (Required)
   - Get from: https://makersuite.google.com/app/apikey

2. **Dropbox App** (Required for Dropbox mode)
   - Create at: https://www.dropbox.com/developers/apps
   - Choose "Scoped access" → "App folder"
   - Note the App Key and App Secret
   - Set redirect URI: `http://localhost:8080/oauth/callback`

3. **Telegram Bot** (Optional, for notifications)
   - Create via: https://t.me/BotFather
   - Get chat ID from: https://t.me/userinfobot

## GitHub Setup (One-Time)

Before deploying, ensure GitHub Actions can build and your server can pull images:

### Enable GitHub Actions

1. **Push your code** to GitHub (if not already):
   ```bash
   git add .
   git commit -m "Add production deployment"
   git push origin main
   ```

2. **GitHub Actions will automatically build** the Docker image
   - No secrets to configure! `GITHUB_TOKEN` is provided automatically
   - Check build status: https://github.com/stefanahman/ocrbox/actions

3. **Make package public** (so servers can pull without authentication):
   - Go to: https://github.com/stefanahman?tab=packages
   - Click on **"ocrbox"** package
   - Click **"Package settings"** (bottom right)
   - Scroll to **"Danger Zone"** → **"Change visibility"** → **"Public"**
   - Confirm the change

**Alternative for Private Packages:**
If you want to keep the package private, your server needs authentication:
```bash
# On your server, create GitHub token with read:packages scope
# Then login:
echo $GITHUB_TOKEN | docker login ghcr.io -u stefanahman --password-stdin
```

## Installation

### Step 1: Clone Repository

```bash
# On your server
cd /opt
sudo git clone https://github.com/stefanahman/ocrbox.git
sudo chown -R $USER:$USER ocrbox
cd ocrbox
```

### Step 2: Create Environment File

All application configuration is stored in `.env` file on your server. **Never commit this file to git!**

```bash
# Create .env file
nano /opt/ocrbox/.env
chmod 600 /opt/ocrbox/.env  # Secure it!
```

**Complete .env template:**

```env
# ============================================
# Docker Registry (Production Deployment)
# ============================================
GITHUB_REPOSITORY=stefanahman/ocrbox

# ============================================
# Operation Mode
# ============================================
MODE=dropbox  # or 'local' for local folder watching

# ============================================
# Gemini API Configuration (REQUIRED)
# ============================================
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite

# ============================================
# Dropbox Configuration (Required for Dropbox mode)
# ============================================
DROPBOX_APP_KEY=your_dropbox_app_key
DROPBOX_APP_SECRET=your_dropbox_app_secret
DROPBOX_REDIRECT_URI=http://localhost:8080/oauth/callback
ALLOWED_ACCOUNTS=your@email.com,friend@email.com

# ============================================
# OAuth Server
# ============================================
OAUTH_SERVER_PORT=8080
OAUTH_SERVER_HOST=0.0.0.0
OAUTH_ALWAYS_ENABLED=false  # true for multi-user setups

# ============================================
# Telegram Notifications (Optional)
# ============================================
TELEGRAM_ENABLED=false
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# ============================================
# Email Notifications (Optional)
# ============================================
EMAIL_ENABLED=false
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=recipient@example.com

# ============================================
# Processing Options
# ============================================
POLL_INTERVAL=30
MAX_RETRIES=3
RETRY_DELAY=2
LOG_LEVEL=INFO

# ============================================
# Storage Paths (usually don't need to change)
# ============================================
DATA_DIR=/app/data
```

**Important Notes:**
- ✅ File should have **600 permissions** (owner read/write only)
- ✅ **Never** commit `.env` to git (it's in `.gitignore`)
- ✅ All secrets stay on the server only
- ✅ No environment variables in docker-compose files (they read from `.env`)

### Step 3: Run Installation Script

```bash
sudo ./deployment/install.sh
```

The script will:
- ✅ Check prerequisites
- ✅ Create directory structure at `/opt/ocrbox`
- ✅ Set proper permissions
- ✅ Pull latest Docker image from registry
- ✅ Install systemd service
- ✅ Enable auto-start on boot

### Step 4: Start the Service

```bash
sudo systemctl start ocrbox@$USER
sudo systemctl status ocrbox@$USER
```

## Configuration

### Environment Variables

Full configuration reference:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GITHUB_REPOSITORY` | Docker image repository | `stefanahman/ocrbox` | Yes |
| `MODE` | Operation mode | `local` | Yes |
| `GEMINI_API_KEY` | Gemini API key | - | Yes |
| `GEMINI_MODEL` | Model to use | `gemini-2.5-flash-lite` | No |
| `DROPBOX_APP_KEY` | Dropbox app key | - | Dropbox mode |
| `DROPBOX_APP_SECRET` | Dropbox app secret | - | Dropbox mode |
| `DROPBOX_REDIRECT_URI` | OAuth callback | `http://localhost:8080/oauth/callback` | No |
| `ALLOWED_ACCOUNTS` | Allowed user emails | - | No |
| `OAUTH_SERVER_PORT` | OAuth server port | `8080` | No |
| `OAUTH_SERVER_HOST` | OAuth bind address | `0.0.0.0` | No |
| `TELEGRAM_ENABLED` | Enable Telegram | `false` | No |
| `TELEGRAM_BOT_TOKEN` | Bot token | - | If enabled |
| `TELEGRAM_CHAT_ID` | Chat ID | - | If enabled |
| `POLL_INTERVAL` | Polling interval (sec) | `30` | No |
| `LOG_LEVEL` | Logging level | `INFO` | No |

### Updating Configuration

```bash
# Edit configuration
sudo nano /opt/ocrbox/.env

# Restart service to apply changes
sudo systemctl restart ocrbox@$USER
```

## SSH Tunnel for OAuth

For Dropbox mode, OAuth authorization is done via SSH tunnel to keep your server private.

### Why SSH Tunnel?

- ✅ Server stays private (no public ports)
- ✅ No reverse proxy needed
- ✅ No domain or SSL certificates required
- ✅ Same setup as local development
- ✅ Your Gemini API key never exposed

### Authorization Process

**On your server**, ensure the service is running:
```bash
sudo systemctl status ocrbox@$USER
```

**From your local machine**, create SSH tunnel:
```bash
# Replace 'user' and 'yourserver.com' with your details
ssh -L 8080:localhost:8080 user@yourserver.com

# Or use IP address
ssh -L 8080:localhost:8080 user@192.168.1.100
```

**Keep the SSH session open** and visit in your browser:
```
http://localhost:8080
```

**Complete the OAuth flow**:
1. Click "Authorize with Dropbox"
2. Grant permissions
3. You'll see "Authorization Successful!"
4. Token is saved on the server

**Disconnect the tunnel**:
```bash
# Just Ctrl+C or close the SSH session
```

The service continues running and processing files with the saved token!

### Multiple Users

To authorize additional users:

1. **Enable persistent OAuth** in `/opt/ocrbox/.env`:
   ```env
   OAUTH_ALWAYS_ENABLED=true
   ALLOWED_ACCOUNTS=user1@example.com,user2@example.com
   ```

2. **Restart service**:
   ```bash
   sudo systemctl restart ocrbox@$USER
   ```

3. **Each user** creates their own SSH tunnel and authorizes via `http://localhost:8080`

## Service Management

### Basic Commands

```bash
# Start service
sudo systemctl start ocrbox@$USER

# Stop service
sudo systemctl stop ocrbox@$USER

# Restart service
sudo systemctl restart ocrbox@$USER

# Check status
sudo systemctl status ocrbox@$USER

# Enable auto-start on boot (already done by install.sh)
sudo systemctl enable ocrbox@$USER

# Disable auto-start
sudo systemctl disable ocrbox@$USER
```

### Viewing Logs

```bash
# Follow logs in real-time
sudo journalctl -u ocrbox@$USER -f

# View last 100 lines
sudo journalctl -u ocrbox@$USER -n 100

# View logs since boot
sudo journalctl -u ocrbox@$USER -b

# View logs for today
sudo journalctl -u ocrbox@$USER --since today

# View Docker Compose logs directly
cd /opt/ocrbox
docker compose -f docker-compose.prod.yml logs -f
```

## Updating

### Update Process

When new code is pushed to the `main` branch, GitHub Actions automatically builds and pushes a new Docker image. To deploy the update:

```bash
# Stop the service
sudo systemctl stop ocrbox@$USER

# Pull latest image
cd /opt/ocrbox
docker compose -f docker-compose.prod.yml pull

# Start service with new image
sudo systemctl start ocrbox@$USER

# Verify update
sudo systemctl status ocrbox@$USER
docker images | grep ocrbox
```

### Update Script (Optional)

Create `/opt/ocrbox/update.sh`:
```bash
#!/bin/bash
set -e

echo "Stopping OCRBox..."
sudo systemctl stop ocrbox@$USER

echo "Pulling latest image..."
cd /opt/ocrbox
docker compose -f docker-compose.prod.yml pull

echo "Starting OCRBox..."
sudo systemctl start ocrbox@$USER

echo "Checking status..."
sleep 2
sudo systemctl status ocrbox@$USER

echo "Update complete!"
```

Make it executable:
```bash
chmod +x /opt/ocrbox/update.sh
```

## Monitoring

### Service Health Check

```bash
# Quick status
sudo systemctl is-active ocrbox@$USER

# Detailed status
sudo systemctl status ocrbox@$USER

# Check if container is running
docker ps | grep ocrbox
```

### Disk Usage

```bash
# Check data directory size
du -sh /opt/ocrbox/data/*

# Check Docker disk usage
docker system df

# Clean up old images (optional)
docker image prune -a
```

### Processing Stats

```bash
# Check processed files database
docker exec ocrbox sqlite3 /app/data/processed.db "SELECT COUNT(*) FROM processed_files;"

# View recent processed files
docker exec ocrbox sqlite3 /app/data/processed.db "SELECT * FROM processed_files ORDER BY processed_at DESC LIMIT 10;"
```

## Backup & Restore

### What to Back Up

- `/opt/ocrbox/data/tokens/` - OAuth tokens (critical)
- `/opt/ocrbox/data/processed.db` - Processing history
- `/opt/ocrbox/.env` - Configuration
- `/opt/ocrbox/data/output/` - Extracted text files (optional)

### Backup Script

```bash
#!/bin/bash
BACKUP_DIR="/backup/ocrbox"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ocrbox_backup_$TIMESTAMP.tar.gz"

mkdir -p "$BACKUP_DIR"

# Create backup
tar -czf "$BACKUP_FILE" \
    -C /opt/ocrbox \
    data/tokens \
    data/processed.db \
    .env

echo "Backup created: $BACKUP_FILE"

# Keep only last 7 backups
ls -t "$BACKUP_DIR"/ocrbox_backup_*.tar.gz | tail -n +8 | xargs rm -f
```

### Restore Process

```bash
# Stop service
sudo systemctl stop ocrbox@$USER

# Restore from backup
cd /opt/ocrbox
tar -xzf /backup/ocrbox/ocrbox_backup_YYYYMMDD_HHMMSS.tar.gz

# Fix permissions
sudo chown -R $USER:$USER data
chmod 700 data/tokens

# Start service
sudo systemctl start ocrbox@$USER
```

## Security Best Practices

### File Permissions

```bash
# Secure .env file
chmod 600 /opt/ocrbox/.env

# Secure token directory
chmod 700 /opt/ocrbox/data/tokens

# Verify
ls -la /opt/ocrbox/.env
ls -la /opt/ocrbox/data/
```

### Firewall Configuration

OCRBox binds to localhost:8080, not accessible from outside:

```bash
# Verify port binding (should show 127.0.0.1:8080)
sudo ss -tlnp | grep 8080

# No firewall rules needed - port is not exposed
# OAuth access is via SSH tunnel only
```

### Token Management

```bash
# List token files
ls -lh /opt/ocrbox/data/tokens/

# Revoke access (delete token)
rm /opt/ocrbox/data/tokens/dbid_*.json
sudo systemctl restart ocrbox@$USER
```

### Regular Maintenance

1. **Weekly**: Check logs for errors
2. **Monthly**: Update to latest image
3. **Quarterly**: Review authorized users
4. **Annually**: Rotate API keys

## Troubleshooting

### Service Won't Start

```bash
# Check detailed status
sudo systemctl status ocrbox@$USER -l

# Check journal logs
sudo journalctl -u ocrbox@$USER -n 50 --no-pager

# Test Docker manually
cd /opt/ocrbox
docker compose -f docker-compose.prod.yml up
```

### Permission Denied Errors

```bash
# Fix ownership
sudo chown -R $USER:$USER /opt/ocrbox/data

# Fix token directory
chmod 700 /opt/ocrbox/data/tokens

# Check Docker group membership
groups $USER | grep docker
```

### OAuth Not Accessible

```bash
# Check if container is running
docker ps | grep ocrbox

# Check port binding
docker port ocrbox

# Test SSH tunnel
ssh -L 8080:localhost:8080 -v user@server

# Check if port 8080 is listening on server
sudo ss -tlnp | grep 8080
```

### Image Pull Fails

```bash
# Check if image exists
docker pull ghcr.io/stefanahman/ocrbox:latest

# Login to GitHub Container Registry (if repository is private)
echo $GITHUB_TOKEN | docker login ghcr.io -u stefanahman --password-stdin

# Verify GITHUB_REPOSITORY in .env
grep GITHUB_REPOSITORY /opt/ocrbox/.env
```

### Gemini API Errors

```bash
# Check API key in .env
grep GEMINI_API_KEY /opt/ocrbox/.env

# Test API key manually
docker exec ocrbox python3 -c "
import os
import google.generativeai as genai
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
print('API key is valid')
"

# Check rate limits
# Visit: https://makersuite.google.com/app/apikey
```

### High Disk Usage

```bash
# Check data directory size
du -sh /opt/ocrbox/data/*

# Clean up old archives
cd /opt/ocrbox/data/archive
find . -type f -mtime +90 -delete

# Clean Docker
docker system prune -a
```

## Advanced Configuration

### Custom Data Directory

To use a different data directory (e.g., mounted storage):

1. Update docker-compose.prod.yml:
   ```yaml
   volumes:
     - /mnt/storage/ocrbox:/app/data
   ```

2. Create directories:
   ```bash
   mkdir -p /mnt/storage/ocrbox/{tokens,output,archive,watch}
   chmod 700 /mnt/storage/ocrbox/tokens
   ```

### Resource Limits

Add to docker-compose.prod.yml:
```yaml
services:
  ocrbox:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### Multiple Instances

Run multiple OCRBox instances for different users:

1. Clone directory: `cp -r /opt/ocrbox /opt/ocrbox-user2`
2. Update `.env` with different port
3. Create new service: `cp /etc/systemd/system/ocrbox.service /etc/systemd/system/ocrbox-user2.service`
4. Update service file paths
5. Enable and start

## Support

- 📖 [Main README](../README.md)
- 🐛 [Issue Tracker](https://github.com/stefanahman/ocrbox/issues)
- 💡 [Discussions](https://github.com/stefanahman/ocrbox/discussions)
- 📁 [Quick Reference](../deployment/README.md)

---

**Questions?** Open an issue on GitHub or check the discussions board.

