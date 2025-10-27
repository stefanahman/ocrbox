# Multi-User Setup Guide

This guide shows how to set up OCRBox for multiple users (you + your girlfriend/friends).

## 🎯 Quick Setup

### Step 1: Configure for Multi-User

Edit your `.env` file:

```bash
nano .env
```

Add/update these lines:

```env
# Enable multi-user mode
OAUTH_ALWAYS_ENABLED=true

# Add all users to allowlist (comma-separated)
ALLOWED_ACCOUNTS=your@email.com,girlfriend@email.com

# Use your local IP for network access
DROPBOX_REDIRECT_URI=http://192.168.1.100:8080/oauth/callback
```

**Find your local IP:**
```bash
# macOS
ipconfig getifaddr en0

# Linux
hostname -I | awk '{print $1}'

# Windows
ipconfig | findstr IPv4
```

Replace `192.168.1.100` with your actual IP.

### Step 2: Update Dropbox App Settings

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Select your OCRBox app
3. Go to **Settings** tab
4. Under **OAuth 2** → **Redirect URIs**, add **both**:
   ```
   http://localhost:8080/oauth/callback
   http://192.168.1.100:8080/oauth/callback
   ```
   (Replace with your actual IP)
5. Click **Add** and **Save**

### Step 3: Restart Service

```bash
docker-compose restart
```

You should see:
```
🔓 Multi-user mode enabled - OAuth server will stay running
OAuth server running at http://0.0.0.0:8080
Visit http://localhost:8080 to authorize additional users
```

### Step 4: Authorize Users

**For you (on same computer):**
Visit: `http://localhost:8080`

**For girlfriend (on same WiFi):**
Share this URL: `http://192.168.1.100:8080` (your IP)

She should:
1. Open the URL on her phone/computer
2. Click "Authorize with Dropbox"
3. Log in with her Dropbox account
4. Grant permissions
5. See "Authorization Successful!"

### Step 5: Verify

Check logs to see both accounts:
```bash
docker-compose logs -f
```

You should see:
```
Authorized accounts: 2
  - your@email.com (dbid:xxx)
  - girlfriend@email.com (dbid:yyy)
```

## 📱 Mobile Authorization

### Option 1: Share Link

Send her:
```
http://192.168.1.100:8080
```

She opens it in Safari/Chrome on her phone (must be on same WiFi).

### Option 2: QR Code

Generate a QR code she can scan:

```bash
# Install qrencode
brew install qrencode

# Generate QR code
echo "http://192.168.1.100:8080" | qrencode -t UTF8
```

She scans it with her camera app!

## 🌐 Remote Authorization (Not on Same Network)

If she's not on your WiFi, use **ngrok**:

### Setup ngrok

```bash
# Install ngrok
brew install ngrok

# Sign up at https://ngrok.com and get auth token
ngrok config add-authtoken YOUR_TOKEN

# Expose port 8080
ngrok http 8080
```

You'll get a URL like: `https://abc123.ngrok-free.app`

### Update Configuration

1. **Dropbox redirect URI**:
   ```
   https://abc123.ngrok-free.app/oauth/callback
   ```

2. **`.env` file**:
   ```env
   DROPBOX_REDIRECT_URI=https://abc123.ngrok-free.app/oauth/callback
   ```

3. **Share with her**:
   ```
   https://abc123.ngrok-free.app
   ```

Works from anywhere! 🌍

## ❓ Troubleshooting

### "Cannot connect to server"

**Check firewall:**
```bash
# macOS - allow Docker
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/docker

# Check if port is listening
lsof -i :8080
```

### "Account not in allowlist"

Add her email to `ALLOWED_ACCOUNTS` in `.env`:
```env
ALLOWED_ACCOUNTS=your@email.com,her@email.com
```

Then restart:
```bash
docker-compose restart
```

### "Invalid redirect URI"

Make sure the redirect URI in:
1. Dropbox App Console
2. `.env` file

**Exactly match** and include the port (`:8080`).

### OAuth server not running

Check `.env`:
```env
OAUTH_ALWAYS_ENABLED=true  # Must be true, not false
```

Restart if changed:
```bash
docker-compose restart
```

## 🔐 Security Notes

- Only allowlisted accounts can authorize
- Each user has their own isolated App Folder
- Tokens are stored securely (600 permissions)
- OAuth server runs on local network only (unless using ngrok)
- You can revoke access anytime

## 📊 Managing Users

### List Authorized Users

```bash
docker-compose exec ocrbox ls -la /app/data/tokens/
```

### Remove a User

```bash
docker-compose exec ocrbox rm /app/data/tokens/dbid_*.json
```

Or just delete the file manually from `data/tokens/`.

### Check Processing Stats Per User

```bash
docker-compose exec ocrbox python -c "
from src.storage import ProcessedFilesDB
db = ProcessedFilesDB('/app/data/processed.db')
print(db.get_stats())
"
```

## 🎉 You're Done!

Now both you and your girlfriend can:
1. Upload images to your respective Dropbox App Folders
2. Get OCR processing automatically
3. Receive notifications
4. Find results in `/ocr_output/`
5. See processed files in `/processed/`

Each user operates independently with their own isolated folders!

---

**Need help?** Check the [main README](../README.md) or [Troubleshooting](../README.md#troubleshooting)

