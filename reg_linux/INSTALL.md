# Twitch CDK Registration - Installation Guide

## ⚡ Quick Installation (One Command)

### Ubuntu/Debian:
```bash
# 1. Extract archive
tar -xzf reg_linux_*.tar.gz
cd reg_linux

# 2. Run installation (installs all dependencies)
bash install.sh

# 3. Run registration
cd ..
bash reg_linux/start.sh
```

### CentOS/RHEL/Fedora:
```bash
# Same as above, install.sh detects your OS automatically
tar -xzf reg_linux_*.tar.gz
cd reg_linux
bash install.sh
cd ..
bash reg_linux/start.sh
```

## 📋 What Gets Installed

### System Level:
- **xvfb** - Virtual display server (for headless operation)
- **Fonts** - CJK fonts for internationalization
- **Build tools** - gcc, make, python3-dev (required for compiled packages)

### Python Packages:
- **cloakbrowser** - Anti-detection browser automation
- **playwright** - Browser automation framework  
- **requests** - HTTP client
- **python-dotenv** - Configuration management
- **loguru** - Logging

## ⚙️ Configuration

After installation, edit configuration (optional):

```bash
nano reg_linux/config.txt
```

Configuration options:
```ini
# API Settings
FRONT_IP=8.138.198.37              # Your API server
API_TOKEN=twitch-cdk-api-token-2024

# Mail API
MAIL_API_URL=https://mailapi.izlvxhe.cn
MAIL_ADMIN_AUTH=Aalcsttkx1!
MAIL_DOMAINS=htazmbb.shop

# Registration
REGISTER_COUNT=10      # How many accounts to register
REG_THREADS=2          # Concurrent threads (2-4 recommended)
PREFIX=blue_ctf        # Account prefix
PASSWORD=BlueCtf2026!Secure

# Debug
DEBUG=false            # Set to true for verbose logging
```

## 🚀 Running Registration

### Basic (uses config.txt):
```bash
bash reg_linux/start.sh
```

### With Custom Settings (override config):
```bash
export REGISTER_COUNT=20
export REG_THREADS=4
bash reg_linux/start.sh
```

### Headless Mode (no display window):
```bash
export DISPLAY=:99
bash reg_linux/start.sh
```

## 📊 Monitoring

View live registration progress:
```bash
tail -f reg_linux/reg_linux_*.log
```

Registered accounts are saved to configured API backend.

## 🔧 Troubleshooting

### "xvfb not found" on fresh install:
```bash
# Ubuntu/Debian
sudo apt-get install xvfb

# CentOS/RHEL
sudo yum install xorg-x11-server-Xvfb
```

### "Python not found":
```bash
# Ubuntu/Debian
sudo apt-get install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip
```

### CloakBrowser requires 2GB+ disk space
Ensure sufficient disk space before running.

### Port conflicts:
By default uses virtual display `:99`. If conflicts occur:
```bash
export DISPLAY=:100
bash reg_linux/start.sh
```

## 📝 Requirements

- **OS**: Ubuntu 20.04+, Debian 10+, CentOS 7+, RHEL 7+, or Fedora 30+
- **Python**: 3.8 or higher
- **Disk**: 2 GB+ (for CloakBrowser)
- **RAM**: 2 GB+ recommended
- **Network**: Stable internet connection

## 📚 Project Structure

```
reg_linux/
├── install.sh                 # One-click installation
├── start.sh                   # Registration launcher
├── main.py                    # Entry point
├── twitch_registration.py     # Registration logic
├── api_client.py              # API client
├── config.py                  # Configuration loader
├── config.txt                 # Runtime configuration
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation
└── reg_linux_*.log            # Execution logs
```

## 🎯 Success Indicators

After running, you should see:
```
=== Twitch CDK Registration Client (Linux) ===
Starting registration: 10 accounts, 2 threads, direct network
Progress: 1/10
...
Progress: 10/10
Registration complete. 10 accounts attempted.
```

## 📞 Support

Check logs for detailed error messages:
```bash
cat reg_linux/reg_linux_*.log | grep ERROR
```

For installation issues, verify Python and pip versions:
```bash
python3 --version
pip3 --version
```
