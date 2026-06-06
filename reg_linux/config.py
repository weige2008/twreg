# config.py - Configuration for registration client
# reg/config.py

import os
from pathlib import Path

from dotenv import load_dotenv

_self_dir = Path(__file__).resolve().parent
_config_file = _self_dir / "config.txt"

# Load config.txt first if it exists
_config_dict = {}
if _config_file.exists():
    with open(_config_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    _config_dict[key.strip()] = value.strip()

# Helper function to get config value
def _get_config(key: str, default: str = "") -> str:
    """Get config from config.txt or environment variables"""
    # Priority: environment variable > config.txt > default
    env_val = os.getenv(key)
    if env_val is not None and env_val != "":
        return env_val
    return _config_dict.get(key) or default

# Load .env files for environment variable overrides
load_dotenv(_self_dir / ".env")
load_dotenv(_self_dir.parent / ".env")

# Parse configuration - priority: env > config.txt > default
THREADS = int(_get_config("REG_THREADS", os.getenv("REG_THREADS", "2")))
FRONT_IP = _get_config("FRONT_IP", os.getenv("FRONT_IP", "127.0.0.1"))
API_URL = os.getenv("API_URL", f"http://{FRONT_IP}:5000")
API_TOKEN = _get_config("API_TOKEN", os.getenv("API_TOKEN", "twitch-cdk-api-token-2024"))
PROXY_FILE = os.getenv("PROXY_FILE", "")
CLASH_API = os.getenv("CLASH_API", "")
CLASH_GROUP = os.getenv("CLASH_GROUP", "Proxy")
CLASH_SECRET = os.getenv("CLASH_SECRET", "")

REGISTER_COUNT = int(_get_config("REGISTER_COUNT", os.getenv("REGISTER_COUNT", "10")))
PREFIX = _get_config("PREFIX", os.getenv("PREFIX", "blue_ctf"))
PASSWORD = _get_config("PASSWORD", os.getenv("PASSWORD", "BlueCtf2026!Secure"))
TIMEOUT = int(os.getenv("TIMEOUT", "90"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
CTF_MODE = os.getenv("TWITCH_CTF", "0") == "1"
NO_HEADLESS = os.getenv("NO_HEADLESS", "false").lower() == "true"
WORKER_ID = os.getenv("WORKER_ID", "reg_worker")

MAIL_API_URL = _get_config("MAIL_API_URL", os.getenv("MAIL_API_URL", "https://mailapi.izlvxhe.cn"))
MAIL_ADMIN_AUTH = _get_config("MAIL_ADMIN_AUTH", os.getenv("MAIL_ADMIN_AUTH", "Aalcsttkx1!"))
MAIL_DOMAINS = _get_config("MAIL_DOMAINS", os.getenv("MAIL_DOMAINS", ""))
