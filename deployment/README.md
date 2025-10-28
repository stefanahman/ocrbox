# OCRBox Deployment Quick Reference

This directory contains files for deploying OCRBox as a systemd service.

## Deployment Overview

OCRBox uses a CI/CD approach for production deployments:
- GitHub Actions builds and pushes Docker images to GitHub Container Registry (ghcr.io)
- Images are built automatically on every push to `main` branch
- Production servers pull pre-built images (no compilation needed)
- Development uses local Docker builds

## Quick Installation

```bash
# On your server
cd /path/to/ocrbox
sudo ./deployment/install.sh
```

## Configuration

Edit your environment file:
```bash
sudo nano /opt/ocrbox/.env
```

Required settings:
```env
# Docker image repository (automatically set by install.sh)
GITHUB_REPOSITORY=stefanahman/ocrbox

# Application mode
MODE=local  # or 'dropbox'
GEMINI_API_KEY=your_api_key_here

# For Dropbox mode:
DROPBOX_APP_KEY=your_app_key
DROPBOX_APP_SECRET=your_app_secret
ALLOWED_ACCOUNTS=user@example.com
```

**Important**: The default is set to `stefanahman/ocrbox`. Update if you've forked the repository.

## Service Management

```bash
# Start the service
sudo systemctl start ocrbox@username

# Stop the service
sudo systemctl stop ocrbox@username

# Restart the service
sudo systemctl restart ocrbox@username

# Check status
sudo systemctl status ocrbox@username

# View logs (live)
sudo journalctl -u ocrbox@username -f

# View last 100 lines
sudo journalctl -u ocrbox@username -n 100

# Disable autostart
sudo systemctl disable ocrbox@username

# Enable autostart
sudo systemctl enable ocrbox@username
```

Replace `username` with your actual username.

## SSH Tunnel for OAuth (Dropbox Mode)

To authorize Dropbox accounts without exposing your server publicly:

```bash
# From your local machine
ssh -L 8080:localhost:8080 user@yourserver.com

# Keep this terminal open and visit in your browser:
# http://localhost:8080

# Complete the OAuth authorization
# Then you can close the SSH connection
```

The Dropbox redirect URI stays as:
```
http://localhost:8080/oauth/callback
```

## File Locations

- **Installation**: `/opt/ocrbox`
- **Data**: `/opt/ocrbox/data/`
  - `tokens/` - OAuth tokens (700 permissions)
  - `watch/` - Input folder (local mode)
  - `output/` - Processed text files
  - `archive/` - Processed images
- **Logs**: `journalctl -u ocrbox@username`
- **Service**: `/etc/systemd/system/ocrbox@.service`

## Troubleshooting

### Service won't start

```bash
# Check detailed status
sudo systemctl status ocrbox@username

# Check full logs
sudo journalctl -u ocrbox@username -n 50

# Test Docker Compose manually
cd /opt/ocrbox
docker compose up
```

### Permission issues

```bash
# Fix data directory permissions
sudo chown -R username:username /opt/ocrbox/data
sudo chmod 700 /opt/ocrbox/data/tokens
```

### OAuth not accessible

```bash
# Check if port 8080 is listening
sudo ss -tlnp | grep 8080

# Test SSH tunnel
ssh -L 8080:localhost:8080 -N user@server
# Then visit http://localhost:8080
```

### View Docker logs directly

```bash
cd /opt/ocrbox
docker compose logs -f
```

## Updating OCRBox

Production deployments automatically pull the latest image from GitHub Container Registry:

```bash
# Stop the service
sudo systemctl stop ocrbox@username

# Pull latest image from registry
cd /opt/ocrbox
docker compose -f docker-compose.prod.yml pull

# Start service (will use new image)
sudo systemctl start ocrbox@username

# Check status
sudo systemctl status ocrbox@username

# Verify running version
docker images | grep ocrbox
```

The image is automatically built and pushed when you push to the `main` branch on GitHub.

## Uninstalling

```bash
# Stop and disable service
sudo systemctl stop ocrbox@username
sudo systemctl disable ocrbox@username

# Remove service file
sudo rm /etc/systemd/system/ocrbox@.service
sudo systemctl daemon-reload

# Remove installation (optional, backs up data first)
sudo tar -czf ~/ocrbox-data-backup.tar.gz /opt/ocrbox/data
sudo rm -rf /opt/ocrbox
```

## Security Notes

- OAuth server (port 8080) is only bound to localhost
- Use SSH tunnel to access it remotely - keeps server private
- Gemini API key is never exposed via web interface
- Token files have restrictive permissions (700)
- Service runs as your user, not root
- `.env` file should have 600 permissions

## For More Details

See the comprehensive [Deployment Guide](../docs/DEPLOYMENT.md)

