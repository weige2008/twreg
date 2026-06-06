# main.py - Registration client entry point
# reg/main.py
#
# Linux服务器首次运行请执行以下命令安装字体：
# sudo apt update
# sudo apt install -y fonts-noto-color-emoji fonts-freefont-ttf fonts-unifont \
#     fonts-ipafont-gothic fonts-wqy-zenhei fonts-tlwg-loma-otf

import asyncio
import os
import subprocess
import sys
from pathlib import Path

from loguru import logger

from .config import (
    THREADS, REGISTER_COUNT, PREFIX, PASSWORD, TIMEOUT, MAX_RETRIES,
    NO_HEADLESS, CTF_MODE,
)
from .api_client import APIClient
from .twitch_registration import register_account


def start_xvfb():
    """Start Xvfb virtual display on :99 if not already running."""
    if os.environ.get("DISPLAY") == ":99":
        return
    try:
        result = subprocess.run(
            ["pgrep", "-f", "Xvfb :99"],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            os.environ["DISPLAY"] = ":99"
            return
    except Exception:
        pass
    try:
        subprocess.Popen(
            ["Xvfb", ":99", "-screen", "0", "1920x1080x24"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        os.environ["DISPLAY"] = ":99"
        logger.info("Xvfb started on :99 (1920x1080x24)")
    except FileNotFoundError:
        logger.warning("Xvfb not found. Install: sudo apt install -y xvfb")
    except Exception as e:
        logger.warning(f"Xvfb start failed: {e}")


logger.remove()
_log_level = os.environ.get("LOGURU_LEVEL", os.environ.get("DEBUG", "false").lower() == "true" and "DEBUG" or "INFO")
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    level=_log_level,
)
logger.add(
    Path(__file__).parent / "reg_linux_{time:YYYY-MM-DD}.log",
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
)

os.environ["TWITCH_CTF"] = "1" if CTF_MODE else "0"


async def run_registration(
    index: int,
    api_client: APIClient,
) -> None:
    try:
        from cloakbrowser import launch_async
    except ImportError:
        logger.error("cloakbrowser not installed. Run: pip install cloakbrowser")
        return

    logger.info(f"[{index}] Launching browser (direct)")
    browser = None
    context = None
    try:
        start_xvfb()
        browser = await asyncio.wait_for(
            launch_async(
                headless=False,
                humanize=True,
            ),
            timeout=30,
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en_US",
        )
        logger.debug(f"[{index}] Browser launched OK")
        page = await context.new_page()
        logger.debug(f"[{index}] Page ready, starting registration")

        result = await register_account(
            index=index,
            context=context,
            page=page,
            prefix=PREFIX,
            password=PASSWORD,
            timeout=TIMEOUT,
            max_retries=MAX_RETRIES,
        )

        if result.get("status") == "success":
            uploaded = api_client.upload_account(
                username=result["username"],
                password=result["password"],
                email=result.get("email", ""),
                auth_token=result.get("auth_token", ""),
                cookies=result.get("cookies", ""),
            )
            if uploaded:
                logger.info(f"[{index}] {result['username']} - uploaded to API")
            else:
                logger.warning(f"[{index}] {result['username']} - API upload failed")
        else:
            logger.warning(f"[{index}] Registration failed: {result.get('error')}")

        return result

    except asyncio.TimeoutError:
        logger.error(f"[{index}] Browser launch timeout")
    except Exception as e:
        logger.error(f"[{index}] Browser error: {e}")
    finally:
        if context:
            try:
                await context.close()
            except Exception:
                pass
        if browser:
            try:
                await browser.close()
            except Exception:
                pass

    # If exception occurred before result was produced, return failure
    return {"status": "failed", "error": "browser error or exception"}


async def main() -> None:
    api_client = APIClient()

    logger.info(f"Starting registration: {REGISTER_COUNT} accounts, {THREADS} threads, direct network")

    sem = asyncio.Semaphore(THREADS)
    completed = 0
    failure_count = 0
    lock = asyncio.Lock()
    FAILURE_THRESHOLD = int(os.getenv("FAILURE_THRESHOLD", "5"))

    tasks = []

    async def run_one(i: int) -> None:
        nonlocal completed, failure_count, tasks
        async with sem:
            api_client.heartbeat("reg_worker", "reg")
            try:
                result = await run_registration(i, api_client)
            except asyncio.CancelledError:
                logger.warning(f"[{i}] Task cancelled")
                return

            async with lock:
                completed += 1
                if not result or result.get("status") != "success":
                    failure_count += 1
                logger.info(f"Progress: {completed}/{REGISTER_COUNT} (failures: {failure_count})")

                if failure_count >= FAILURE_THRESHOLD:
                    logger.error(f"Failure threshold reached ({failure_count}), cancelling remaining tasks")
                    for t in tasks:
                        if not t.done():
                            t.cancel()

    tasks = [asyncio.create_task(run_one(i)) for i in range(REGISTER_COUNT)]
    await asyncio.gather(*tasks, return_exceptions=True)

    api_client.heartbeat("reg_worker", "reg")
    logger.info(f"Registration complete. {REGISTER_COUNT} accounts attempted.")


def entry():
    asyncio.run(main())


if __name__ == "__main__":
    entry()
