# Deployment Changes Summary

## Environment Variables Setup

### GitHub Actions (CI/CD)
- ✅ **No setup needed!** `GITHUB_TOKEN` is automatically provided
- After first push, make package public at: https://github.com/stefanahman?tab=packages

### Production Server
- ✅ Create `/opt/ocrbox/.env` file with all secrets
- ✅ File should have `600` permissions
- ✅ Required: `GEMINI_API_KEY`, `MODE`, `GITHUB_REPOSITORY`
- ✅ For Dropbox: Add `DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`
- ✅ Optional: Telegram/Email notification settings

### Docker Compose
- ✅ **No secrets in compose files!**
- ✅ `docker-compose.prod.yml` reads from `.env` automatically
- ✅ Uses `${GITHUB_REPOSITORY}` variable substitution

See [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) for complete reference.

## What Was Changed

### 1. Docker Compose Modernization
- ✅ Removed deprecated `version: '3.8'` field from `docker-compose.yml`
- ✅ Created `docker-compose.prod.yml` for production deployments using pre-built images

### 2. Gemini Model Updates
- ✅ Updated default model from `gemini-1.5-flash` to `gemini-2.5-flash-lite` (latest stable)
- ✅ Updated in: `src/config.py`, `src/gemini_client.py`, `README.md`

### 3. Package Updates
- ✅ Changed requirements.txt to use `>=` for automatic latest version installation

### 4. CI/CD Pipeline
- ✅ Created `.github/workflows/docker-build.yml`
  - Automatically builds Docker images on push to `main`
  - Pushes to GitHub Container Registry (ghcr.io)
  - Tags images with `latest` and commit SHA

### 5. Systemd Deployment
- ✅ Created `deployment/ocrbox@.service` - systemd service template file
- ✅ Created `deployment/install.sh` - automated installation script
- ✅ Created `deployment/README.md` - quick reference guide

### 6. Documentation
- ✅ Created `docs/DEPLOYMENT.md` - comprehensive 500+ line deployment guide
- ✅ Updated `README.md` with production deployment section
- ✅ Added SSH tunnel instructions for private server OAuth

### 7. Repository Branding
- ✅ Updated all GitHub URLs to use `stefanahman/ocrbox`

## How It Works

### Development Workflow
```bash
# Local development - builds from source
docker-compose up
```

### Production Workflow
```bash
# 1. Push code to GitHub main branch
git push origin main

# 2. GitHub Actions automatically builds and pushes image to ghcr.io

# 3. Server pulls and runs pre-built image
cd /opt/ocrbox
docker compose -f docker-compose.prod.yml pull
sudo systemctl restart ocrbox@username
```

## Key Features

### SSH Tunnel for OAuth
- Server stays completely private (no public ports)
- OAuth accessible via: `ssh -L 8080:localhost:8080 user@server`
- Dropbox redirect URI stays: `http://localhost:8080/oauth/callback`
- No reverse proxy or SSL certificates needed

### Systemd Service
- Auto-starts on boot
- Auto-restarts on failure
- Managed via standard systemd commands
- Logs via journalctl

### Image Registry
- Pre-built images at `ghcr.io/stefanahman/ocrbox:latest`
- No build time on production server
- Consistent deployments across servers
- Fast updates (just pull new image)

## Quick Start

### For Production Server:
```bash
# Clone repository
git clone https://github.com/stefanahman/ocrbox.git /opt/ocrbox
cd /opt/ocrbox

# Configure .env file
cp .env.example .env
nano .env  # Add your GEMINI_API_KEY, etc.

# Run installation
sudo ./deployment/install.sh

# Service is now running!
sudo systemctl status ocrbox@$USER
```

### For OAuth Authorization:
```bash
# From your local machine
ssh -L 8080:localhost:8080 user@yourserver.com

# Visit http://localhost:8080 and complete OAuth
# Disconnect tunnel when done
```

## Files Created

### GitHub Actions
- `.github/workflows/docker-build.yml`

### Docker
- `docker-compose.prod.yml`

### Deployment
- `deployment/ocrbox@.service`
- `deployment/install.sh` (executable)
- `deployment/README.md`

### Documentation
- `docs/DEPLOYMENT.md`

## Security Notes

- ✅ OAuth server only binds to localhost (127.0.0.1:8080)
- ✅ SSH tunnel provides secure remote access
- ✅ Gemini API key never exposed via web interface
- ✅ Token files have 700 permissions
- ✅ Service runs as non-root user
- ✅ .env file should have 600 permissions

## Next Steps

1. **Push to GitHub**: Your changes will trigger the first image build
2. **Make Repository Public** (or configure GitHub token for private)
3. **Deploy to Server**: Follow the production quick start above
4. **Test OAuth**: Create SSH tunnel and authorize a Dropbox account
5. **Monitor**: Check logs with `sudo journalctl -u ocrbox@$USER -f`

## Troubleshooting

### If image pull fails:
```bash
# Check if workflow ran successfully
# Visit: https://github.com/stefanahman/ocrbox/actions

# Manually check image availability
docker pull ghcr.io/stefanahman/ocrbox:latest
```

### If service won't start:
```bash
# Check service status
sudo systemctl status ocrbox@$USER -l

# Check logs
sudo journalctl -u ocrbox@$USER -n 50

# Test Docker Compose manually
cd /opt/ocrbox
docker compose -f docker-compose.prod.yml up
```

## Documentation Links

- **Quick Reference**: [deployment/README.md](deployment/README.md)
- **Full Deployment Guide**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Main README**: [README.md](README.md)

---

**All changes complete and ready for production deployment! 🚀**

