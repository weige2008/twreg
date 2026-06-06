#!/bin/sh
# Twitch CDK Registration Client - Linux
# Config: config.txt
# Usage: sh start.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PARENT_DIR"

echo "=== Twitch CDK Registration Client (Linux) ==="

# Python check
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "ERROR: Python not found"
    exit 1
fi
echo "Python: $($PYTHON --version)"

# pip check
if command -v pip3 >/dev/null 2>&1; then
    PIP=pip3
elif command -v pip >/dev/null 2>&1; then
    PIP=pip
else
    echo "ERROR: pip not found. apt install -y python3-pip"
    exit 1
fi

# Load config
CONFIG_FILE="$SCRIPT_DIR/config.txt"
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << 'EOF'
FRONT_IP=8.138.198.37
API_TOKEN=twitch-cdk-api-token-2024
MAIL_API_URL=https://mailapi.izlvxhe.cn
MAIL_ADMIN_AUTH=Aalcsttkx1!
MAIL_DOMAINS=htazmbb.shop
REGISTER_COUNT=10
REG_THREADS=1
PREFIX=blue_ctf
PASSWORD=BlueCtf2026!Secure
DEBUG=false
EOF
    echo "Config created: $CONFIG_FILE"
    echo "Please edit and re-run"
    exit 0
fi

# Source config
set -a
. "$CONFIG_FILE"
set +a

export API_URL="http://${FRONT_IP}:5000"

if [ "$DEBUG" = "true" ]; then
    export LOGURU_LEVEL="DEBUG"
fi

echo "Front: $API_URL | Count: ${REGISTER_COUNT} | Threads: ${REG_THREADS:-1} | Debug: ${DEBUG:-false}"

# Install deps
if ! $PYTHON -c "import loguru" 2>/dev/null; then
    echo "Installing Python deps..."
    if $PIP install --help 2>&1 | grep -q break-system-packages; then
        $PIP install -r "$SCRIPT_DIR/requirements.txt" --quiet --break-system-packages 2>&1
    else
        $PIP install -r "$SCRIPT_DIR/requirements.txt" --quiet 2>&1 || \
        $PIP install -r "$SCRIPT_DIR/requirements.txt" --user --quiet 2>&1 || \
        sudo $PIP install -r "$SCRIPT_DIR/requirements.txt" --quiet 2>&1
    fi
fi

# Install CloakBrowser (stealth Chromium binary auto-downloads on first launch)
echo "Installing CloakBrowser + system dependencies..."
if command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -qq 2>/dev/null
    sudo apt-get install -y -qq \
        libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
        libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 \
        libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \
        libnss3 libnspr4 libx11-xcb1 libxcb1 libasound2t64 \
        xvfb \
        2>/dev/null || true
fi
# Pre-download CloakBrowser binary during setup
$PYTHON -c "from cloakbrowser import ensure_binary; ensure_binary()" 2>/dev/null || true
echo "CloakBrowser ready"

mkdir -p "$PARENT_DIR/profiles"

echo "Starting..."
$PYTHON -m reg_linux.main
echo "Done."
