#!/bin/bash
# GitHub Actions initialization script for Twitch Registration
# This script is designed to run within GitHub Actions environment

set -e

echo "=== Twitch Registration GitHub Actions Setup ==="

# Environment setup for headless environment
export DISPLAY=:99
export XAUTHORITY=/tmp/.Xauthority

# Create virtual display if needed (Xvfb should be pre-installed)
if ! pgrep -x Xvfb > /dev/null; then
    echo "Starting Xvfb virtual display..."
    Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
    XVFB_PID=$!
    sleep 2
    echo "Xvfb started with PID: $XVFB_PID"
fi

# Export configuration from config.txt
if [ -f "reg_linux/config.txt" ]; then
    echo "Loading config.txt..."
    set -a
    source <(grep -v '^#' reg_linux/config.txt | grep -v '^$')
    set +a
    
    echo "Configuration loaded:"
    echo "  FRONT_IP: ${FRONT_IP:-not set}"
    echo "  API_TOKEN: ${API_TOKEN:0:20}***"
    echo "  REG_THREADS: ${REG_THREADS:-1}"
    echo "  REGISTER_COUNT: ${REGISTER_COUNT:-10}"
    echo "  PREFIX: ${PREFIX:-blue_ctf}"
else
    echo "ERROR: config.txt not found!"
    exit 1
fi

# Set environment variables for Python
export TWITCH_CTF=1
export LOGURU_LEVEL=INFO

# Change to project directory
cd reg_linux

# Install Python dependencies if not already installed
if ! python3 -c "import playwright" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Run the registration
echo "Starting registration with WORKER_ID: ${WORKER_ID:-reg_worker}"
python3 -m reg_linux.main

echo "Registration completed!"
