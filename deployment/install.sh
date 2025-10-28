#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/ocrbox"
SERVICE_NAME="ocrbox@${SUDO_USER}"
SERVICE_FILE="ocrbox@.service"

echo "================================================"
echo "OCRBox Systemd Installation Script"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: Please run as root (use sudo)${NC}"
    exit 1
fi

# Check if we have a real user
if [ -z "$SUDO_USER" ]; then
    echo -e "${RED}Error: Please run with sudo, not as root directly${NC}"
    echo "Usage: sudo ./install.sh"
    exit 1
fi

echo -e "${YELLOW}Installing as user: $SUDO_USER${NC}"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/engine/install/"
    exit 1
fi

if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose first"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
echo ""

# Create installation directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    echo "Creating installation directory at $INSTALL_DIR..."
    mkdir -p "$INSTALL_DIR"
    echo -e "${GREEN}✓ Directory created${NC}"
else
    echo -e "${YELLOW}Installation directory already exists${NC}"
fi
echo ""

# Copy files to installation directory
echo "Copying files to $INSTALL_DIR..."
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Copy all files except .git, data, and __pycache__
rsync -av --exclude='.git' --exclude='data' --exclude='__pycache__' --exclude='*.pyc' \
    "$PROJECT_DIR/" "$INSTALL_DIR/" > /dev/null

echo -e "${GREEN}✓ Files copied${NC}"
echo ""

# Set ownership
echo "Setting ownership to $SUDO_USER..."
chown -R "$SUDO_USER:$SUDO_USER" "$INSTALL_DIR"
echo -e "${GREEN}✓ Ownership set${NC}"
echo ""

# Create data directories
echo "Creating data directories..."
mkdir -p "$INSTALL_DIR/data"/{tokens,output,archive,watch}
chown -R "$SUDO_USER:$SUDO_USER" "$INSTALL_DIR/data"
chmod 700 "$INSTALL_DIR/data/tokens"
echo -e "${GREEN}✓ Data directories created${NC}"
echo ""

# Check for .env file
if [ ! -f "$INSTALL_DIR/.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    if [ -f "$INSTALL_DIR/.env.example" ]; then
        echo "Creating .env from .env.example..."
        cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
        chown "$SUDO_USER:$SUDO_USER" "$INSTALL_DIR/.env"
        chmod 600 "$INSTALL_DIR/.env"
        echo -e "${YELLOW}Please edit $INSTALL_DIR/.env with your configuration${NC}"
    else
        echo -e "${YELLOW}Please create $INSTALL_DIR/.env before starting the service${NC}"
    fi
    echo ""
fi

# Add GITHUB_REPOSITORY to .env if not present
if [ -f "$INSTALL_DIR/.env" ]; then
    if ! grep -q "GITHUB_REPOSITORY=" "$INSTALL_DIR/.env"; then
        echo "" >> "$INSTALL_DIR/.env"
        echo "# Docker image repository (for production deployment)" >> "$INSTALL_DIR/.env"
        echo "GITHUB_REPOSITORY=stefanahman/ocrbox" >> "$INSTALL_DIR/.env"
        echo -e "${YELLOW}Added GITHUB_REPOSITORY to .env - update with your repository name${NC}"
        echo ""
    fi
fi

# Pull latest Docker image
echo "Pulling latest Docker image..."
cd "$INSTALL_DIR"
if sudo -u "$SUDO_USER" docker compose -f docker-compose.prod.yml pull 2>/dev/null; then
    echo -e "${GREEN}✓ Docker image pulled${NC}"
else
    echo -e "${YELLOW}Warning: Could not pull image. Will use local build if available.${NC}"
    echo -e "${YELLOW}Make sure GITHUB_REPOSITORY is set correctly in .env${NC}"
fi
echo ""

# Install systemd service
echo "Installing systemd service..."
cp "$INSTALL_DIR/deployment/$SERVICE_FILE" "/etc/systemd/system/"
echo -e "${GREEN}✓ Service file installed${NC}"
echo ""

# Reload systemd
echo "Reloading systemd daemon..."
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd reloaded${NC}"
echo ""

# Enable service
echo "Enabling service to start on boot..."
systemctl enable "$SERVICE_NAME"
echo -e "${GREEN}✓ Service enabled${NC}"
echo ""

# Add user to docker group if not already
if ! groups "$SUDO_USER" | grep -q docker; then
    echo "Adding $SUDO_USER to docker group..."
    usermod -aG docker "$SUDO_USER"
    echo -e "${GREEN}✓ User added to docker group${NC}"
    echo -e "${YELLOW}Note: You may need to log out and back in for group changes to take effect${NC}"
    echo ""
fi

echo "================================================"
echo -e "${GREEN}Installation complete!${NC}"
echo "================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Configure your environment:"
echo "   sudo nano $INSTALL_DIR/.env"
echo ""
echo "2. Start the service:"
echo "   sudo systemctl start $SERVICE_NAME"
echo ""
echo "3. Check status:"
echo "   sudo systemctl status $SERVICE_NAME"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "5. For Dropbox OAuth (from your local machine):"
echo "   ssh -L 8080:localhost:8080 $SUDO_USER@$(hostname -I | awk '{print $1}')"
echo "   Then visit: http://localhost:8080"
echo ""
echo "Service management commands:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo ""

