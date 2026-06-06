#!/bin/bash
# Twitch CDK Registration - One-Click Installation Script
# Usage: bash install.sh

set -e

echo "=========================================="
echo "Twitch CDK Registration - Installation"
echo "=========================================="

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo "ERROR: Cannot detect OS"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Installation directory: $SCRIPT_DIR"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================
# 1. System Dependencies
# ============================================
echo ""
echo "[1/4] Installing system dependencies..."

if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    echo "Detected: Ubuntu/Debian"
    
    # Update package manager
    sudo apt-get update -qq
    
    # Install core dependencies
    echo "  Installing: xvfb, fonts, build tools..."
    sudo apt-get install -y -qq \
        xvfb \
        fonts-noto-color-emoji \
        fonts-freefont-ttf \
        fonts-unifont \
        fonts-ipafont-gothic \
        fonts-wqy-zenhei \
        fonts-tlwg-loma-otf \
        build-essential \
        python3-dev \
        python3-pip \
        git \
        curl \
        wget
    
    echo "  ✓ System dependencies installed"

elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ] || [ "$OS" = "fedora" ]; then
    echo "Detected: CentOS/RHEL/Fedora"
    
    sudo yum update -y -q
    sudo yum install -y -q \
        xorg-x11-server-Xvfb \
        google-noto-emoji-fonts \
        liberation-fonts \
        noto-fonts-cjk \
        noto-fonts-korean \
        texlive-fonts-all \
        gcc \
        gcc-c++ \
        make \
        kernel-devel \
        python3-devel \
        python3-pip \
        git \
        curl \
        wget
    
    echo "  ✓ System dependencies installed"

else
    echo "ERROR: Unsupported OS: $OS"
    echo "Supported: ubuntu, debian, centos, rhel, fedora"
    exit 1
fi

# ============================================
# 2. Python Dependencies
# ============================================
echo ""
echo "[2/4] Installing Python dependencies..."

if ! command_exists python3; then
    echo "ERROR: Python 3 not found. Please install Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python version: $PYTHON_VERSION"

# Upgrade pip
python3 -m pip install --upgrade -q pip setuptools wheel 2>/dev/null || true

# Install Python packages
echo "  Installing: cloakbrowser, playwright, requests, python-dotenv, loguru..."
pip3 install -q \
    cloakbrowser>=0.3.0 \
    playwright>=1.50.0 \
    requests>=2.28.0 \
    python-dotenv>=1.0.0 \
    loguru>=0.7.0 \
    urllib3

# Install Playwright browsers (required for CloakBrowser)
python3 -m playwright install chromium 2>&1 | grep -E "^(Installing|installing|Downloading)" || echo "  ✓ Playwright browsers ready"

echo "  ✓ Python dependencies installed"

# ============================================
# 3. Virtual Display Setup
# ============================================
echo ""
echo "[3/4] Configuring virtual display..."

# Create systemd service for persistent Xvfb (optional)
if command_exists systemctl; then
    echo "  Detected systemd"
    if ! systemctl is-active --quiet xvfb; then
        echo "  (Optional: Xvfb can be started manually with 'Xvfb :99 -screen 0 1920x1080x24 &')"
    fi
fi

echo "  ✓ Virtual display configured"

# ============================================
# 4. Configuration
# ============================================
echo ""
echo "[4/4] Initializing configuration..."

CONFIG_FILE="$SCRIPT_DIR/config.txt"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "  Creating default config.txt..."
    cat > "$CONFIG_FILE" << 'EOF'
# Twitch CDK Registration Configuration
FRONT_IP=8.138.198.37
API_TOKEN=twitch-cdk-api-token-2024
MAIL_API_URL=https://mailapi.izlvxhe.cn
MAIL_ADMIN_AUTH=Aalcsttkx1!
MAIL_DOMAINS=htazmbb.shop

# Registration settings
REGISTER_COUNT=10
REG_THREADS=2
PREFIX=blue_ctf
PASSWORD=BlueCtf2026!Secure

# Debugging
DEBUG=false
EOF
    echo "  ✓ Config created: $CONFIG_FILE"
    echo "  ⓘ Edit config.txt if needed, then run: cd $(dirname "$SCRIPT_DIR") && bash reg_linux/start.sh"
else
    echo "  ✓ Config already exists: $CONFIG_FILE"
fi

# ============================================
# Installation Complete
# ============================================
echo ""
echo "=========================================="
echo "✓ Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit configuration (optional):"
echo "     nano $(dirname "$SCRIPT_DIR")/reg_linux/config.txt"
echo ""
echo "  2. Run registration:"
echo "     cd $(dirname "$SCRIPT_DIR")"
echo "     bash reg_linux/start.sh"
echo ""
echo "Requirements:"
echo "  - Python 3.8+"
echo "  - 2 GB+ free disk space (for CloakBrowser)"
echo "  - Internet connection"
echo "  - For headless mode: DISPLAY=:99 will be used"
echo ""
echo "For more info, see: $SCRIPT_DIR/README.md"
echo "=========================================="
