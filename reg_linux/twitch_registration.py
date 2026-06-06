# twitch_registration.py - Adapted from cloakminer.registration
# reg/twitch_registration.py

import asyncio
import json
import time
from pathlib import Path
from typing import Optional

from loguru import logger

from .config import PREFIX, PASSWORD, TIMEOUT, MAX_RETRIES, CTF_MODE, MAIL_API_URL, MAIL_ADMIN_AUTH, MAIL_DOMAINS

try:
    import requests as sync_requests
    from urllib3 import disable_warnings as _dw
    _dw()
except ImportError:
    sync_requests = None


__no_proxy = {"http": None, "https": None}


async def _dump_input_xpaths(page, index: int, attempt: int) -> None:
    try:
        debug_dir = Path(f"profiles")
        debug_dir.mkdir(parents=True, exist_ok=True)
        script = """
        () => {
          function getXPath(element) {
            if (element.id) {
              return `//*[@id="${element.id}"]`;
            }
            if (element === document.body) {
              return '/html/body';
            }
            let ix = 0;
            const siblings = element.parentNode ? element.parentNode.childNodes : [];
            for (let i = 0; i < siblings.length; i++) {
              const sibling = siblings[i];
              if (sibling === element) {
                const tagName = element.tagName.toLowerCase();
                for (let j = 0; j < i; j++) {
                  if (siblings[j].nodeType === 1 && siblings[j].tagName === element.tagName) {
                    ix += 1;
                  }
                }
                ix += 1;
                return getXPath(element.parentNode) + '/' + tagName + '[' + ix + ']';
              }
            }
            return '';
          }

          const inputs = Array.from(document.querySelectorAll('input'));
          const items = inputs.map((el, idx) => ({
            index: idx,
            id: el.id || '',
            name: el.name || '',
            type: el.type || '',
            placeholder: el.placeholder || '',
            xpath: getXPath(el),
          }));
          const emailEl = document.querySelector('input#email-input');
          const emailInputXPath = emailEl ? getXPath(emailEl) : null;
          return {inputs: items, emailInputXPath};
        }
        """
        result = await page.evaluate(script)
        log_path = debug_dir / f"input_xpaths_{index}_attempt_{attempt}.txt"
        title = await page.title()
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"URL: {page.url}\n")
            f.write(f"Title: {title}\n\n")
            f.write("Email input xpath for id=email-input:\n")
            f.write(f"{result.get('emailInputXPath') or 'NOT FOUND'}\n\n")
            f.write("All input fields:\n")
            for item in result.get('inputs', []):
                f.write(f"[{item['index']}] id={item['id']} name={item['name']} type={item['type']} placeholder={item['placeholder']} xpath={item['xpath']}\n")
        logger.warning(f"[{index}] Saved input xpaths debug log: {log_path}")
        if result.get('emailInputXPath'):
            logger.warning(f"[{index}] Found email-input xpath: {result.get('emailInputXPath')}")
        else:
            logger.warning(f"[{index}] id=email-input not found on current page")
    except Exception as inner_e:
        logger.warning(f"[{index}] Failed to dump input xpaths: {inner_e}")


async def _try_fill_email_on_inputs(page, temp_email: str, index: int, attempt: int) -> str:
    try:
        script = """
        () => {
          function getXPath(element) {
            if (element.id) {
              return `//*[@id="${element.id}"]`;
            }
            if (element === document.body) {
              return '/html/body';
            }
            let ix = 0;
            const siblings = element.parentNode ? element.parentNode.childNodes : [];
            for (let i = 0; i < siblings.length; i++) {
              const sibling = siblings[i];
              if (sibling === element) {
                const tagName = element.tagName.toLowerCase();
                for (let j = 0; j < i; j++) {
                  if (siblings[j].nodeType === 1 && siblings[j].tagName === element.tagName) {
                    ix += 1;
                  }
                }
                ix += 1;
                return getXPath(element.parentNode) + '/' + tagName + '[' + ix + ']';
              }
            }
            return '';
          }

          const inputs = Array.from(document.querySelectorAll('input'));
          return inputs.map((el, idx) => ({
            index: idx,
            id: el.id || '',
            name: el.name || '',
            type: el.type || '',
            placeholder: el.placeholder || '',
            xpath: getXPath(el),
          }));
        }
        """
        result = await page.evaluate(script)
        debug_dir = Path("profiles")
        debug_dir.mkdir(parents=True, exist_ok=True)
        log_path = debug_dir / f"input_xpaths_tryfill_{index}_attempt_{attempt}.txt"
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"URL: {page.url}\n")
            title = await page.title()
            f.write(f"Title: {title}\n\n")
            f.write("Attempting to fill email using all input xpath candidates:\n")
            for item in result:
                f.write(f"[{item['index']}] id={item['id']} name={item['name']} type={item['type']} placeholder={item['placeholder']} xpath={item['xpath']}\n")
        for item in result:
            xpath = item.get('xpath')
            if not xpath:
                continue
            try:
                locator = page.locator(f"xpath={xpath}")
                if await locator.count() == 0:
                    continue
                await locator.evaluate("(el, val) => { const s = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; s.call(el, val); el.dispatchEvent(new Event('input', {bubbles:true})); }", temp_email)
                current_value = await locator.input_value()
                if current_value == temp_email:
                    logger.warning(f"[{index}] Alternate input xpath can fill email: {xpath}")
                    return xpath
            except Exception:
                continue
        logger.warning(f"[{index}] No alternate input xpath could fill email")
    except Exception as fill_err:
        logger.warning(f"[{index}] Failed to try filling email on inputs: {fill_err}")
    return ""


def _api_post_admin(url: str, json_data: dict, timeout: int = 15) -> Optional[dict]:
    try:
        resp = sync_requests.post(
            url,
            json=json_data,
            timeout=timeout,
            proxies=__no_proxy,
            headers={"x-admin-auth": MAIL_ADMIN_AUTH},
            verify=False,
        )
        if resp.status_code not in (200, 201):
            logger.warning(f"Mail Admin API POST {url} => HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        return resp.json()
    except Exception as e:
        logger.warning(f"Mail Admin API POST error: {e}")
        return None


def _api_get_jwt(url: str, jwt: str, timeout: int = 15) -> Optional[dict]:
    try:
        resp = sync_requests.get(
            url,
            timeout=timeout,
            proxies=__no_proxy,
            headers={"Authorization": f"Bearer {jwt}"},
            verify=False,
        )
        if resp.status_code != 200:
            logger.warning(f"Mail JWT API GET {url} => HTTP {resp.status_code}: {resp.text[:200]}")
            return None
        return resp.json()
    except Exception as e:
        logger.warning(f"Mail JWT API GET error: {e}")
        return None


def get_urls() -> dict:
    if CTF_MODE:
        return {
            "CLIENT_URL": "http://www.twitch.tv",
            "PASSPORT_TWITCH_TV": "http://passport.twitch.tv",
            "ID_TWITCH_TV": "http://id.twitch.tv",
            "GQL_TWITCH_TV": "http://gql.twitch.tv",
        }
    return {
        "CLIENT_URL": "https://www.twitch.tv",
        "PASSPORT_TWITCH_TV": "https://passport.twitch.tv",
        "ID_TWITCH_TV": "https://id.twitch.tv",
        "GQL_TWITCH_TV": "https://gql.twitch.tv",
    }


CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"


def create_temp_email(prefix: str = "blue_ctf") -> tuple:
    import secrets, random
    name = f"{prefix}_{secrets.token_hex(4)}"
    domains = [d.strip() for d in MAIL_DOMAINS.split(",") if d.strip()]
    if not domains:
        domains = ["xiiktcx.cn", "cabuhu.cn"]
    domain = random.choice(domains)
    data = _api_post_admin(
        f"{MAIL_API_URL}/admin/new_address",
        {"enablePrefix": True, "name": name, "domain": domain},
    )
    if not data or "address" not in data:
        raise Exception(f"Mail API create failed: {data}")
    logger.debug(f"Temp email created: {data['address']}")
    return data["address"], data["jwt"]


def get_verification_code(jwt: str, timeout: int = 90) -> tuple:
    import re
    start = time.time()
    while time.time() - start < timeout:
        try:
            data = _api_get_jwt(f"{MAIL_API_URL}/api/mails?limit=1&offset=0", jwt, timeout=10)
            if not data or not data.get("results"):
                time.sleep(3)
                continue
            raw = data["results"][0].get("raw", "")
            codes = re.findall(r"(?<=>)\d{6}(?=<)", raw)
            if codes:
                logger.debug(f"Verification code found: {codes[0]}")
                return codes[0], data["results"][0].get("id", "")
        except Exception as e:
            logger.debug(f"Mail poll error: {e}")
        time.sleep(3)
    return None, None


def extract_auth(cookies: list) -> Optional[dict]:
    auth_token = ""
    device_id = ""
    user_id = 0
    for c in cookies:
        name = c.get("name", "")
        value = c.get("value", "")
        if name == "auth-token":
            auth_token = value
        elif name == "unique_id":
            device_id = value
        elif name == "persistent":
            user_id_str = value.split("%")[0] if value else ""
            user_id = int(user_id_str) if user_id_str.isdigit() else 0
    if auth_token:
        return {"access_token": auth_token, "user_id": user_id, "device_id": device_id}
    return None


async def register_account(
    index: int,
    context,
    page,
    prefix: str = PREFIX,
    password: str = PASSWORD,
    timeout: int = TIMEOUT,
    max_retries: int = MAX_RETRIES,
) -> dict:
    """Register a single Twitch account using CloakBrowser/Playwright."""
    import json as _json

    # Track consecutive wait_for timeouts to abort early if they repeat
    consecutive_wait_for_timeouts = 0

    urls = get_urls()
    signup_url = f"{urls['CLIENT_URL']}/signup"

    for attempt in range(1, max_retries + 1):
        try:
            temp_email, mail_token = create_temp_email(prefix)
            username = temp_email.split("@")[0]
            logger.info(f"[{index}] {username} - registering (attempt {attempt})")

            await page.goto(signup_url, wait_until="networkidle", timeout=30000)
            # Let Twitch CSS animations finish (form slides/fades in)
            await asyncio.sleep(3)

            email_filled = False
            use_id_selectors = False
            email_input = page.locator('xpath=/html/body/div/div[1]/div[1]/div/div/div/div/div/div/div[2]/form/div/div[1]/div/div[1]/div[2]/div/input')
            try:
                await email_input.wait_for(state="attached", timeout=10000)
                await email_input.evaluate("(el, val) => { const s = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; s.call(el, val); el.dispatchEvent(new Event('input', {bubbles:true})); }", temp_email)
                email_filled = True
            except Exception as email_err:
                logger.warning(f"[{index}] Email input locator failed: {email_err}")
                await _dump_input_xpaths(page, index, attempt)
                alt_xpath = await _try_fill_email_on_inputs(page, temp_email, index, attempt)
                if alt_xpath:
                    logger.warning(f"[{index}] {alt_xpath} 可以填充邮箱地址")
                    email_filled = True
                    use_id_selectors = True
                else:
                    raise
            await asyncio.sleep(0.5)

            # Click Continue button after email input
            if use_id_selectors:
                continue_btn = page.locator('button[screen="signup_form"][data-a-target="passport-signup-button"]')
            else:
                continue_btn = page.locator('xpath=/html/body/div/div[1]/div[1]/div/div/div/div/div/div/div[2]/form/div/div[2]/div/div[1]/button')
            await continue_btn.wait_for(state="attached", timeout=10000)
            await continue_btn.click(force=True)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # Username step
            if use_id_selectors:
                username_input = page.locator('#signup-username')
            else:
                username_input = page.locator('xpath=/html/body/div/div[1]/div[1]/div/div/div/div/div[2]/form/div/div[2]/div/div[2]/div/input')
            await username_input.wait_for(state="attached", timeout=15000)
            await username_input.evaluate("(el, val) => { const s = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; s.call(el, val); el.dispatchEvent(new Event('input', {bubbles:true})); }", username)
            await asyncio.sleep(0.3)

            if use_id_selectors:
                password_input = page.locator('#password-input')
            else:
                password_input = page.locator('xpath=/html/body/div/div[1]/div[1]/div/div/div/div/div[2]/form/div/div[3]/div[2]/div[1]/div/input')
            await password_input.wait_for(state="attached", timeout=10000)
            await password_input.evaluate("(el, val) => { const s = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; s.call(el, val); el.dispatchEvent(new Event('input', {bubbles:true})); }", password)
            await asyncio.sleep(0.3)
            await page.keyboard.press("Enter")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)

            # Date of birth select fields
            if use_id_selectors:
                month_select = page.locator('select[data-a-target="birthday-month-select"]')
                day_select = page.locator('select[data-a-target="birthday-date-input"]')
                year_select = page.locator('select[aria-label="Select your birthday year"]')
            else:
                month_select = page.locator('xpath=/html/body/div/div[1]/div[1]/div/div/div/div/div[2]/form/div/div[4]/div/div[2]/div[1]/div/select')
                day_select = page.locator('xpath=/html/body/div/div[1]/div[1]/div/div/div/div/div[2]/form/div/div[4]/div/div[2]/div[2]/div/select')
                year_select = page.locator('xpath=/html/body/div/div[1]/div[1]/div/div/div/div/div[2]/form/div/div[4]/div/div[2]/div[3]/div/select')
            await month_select.wait_for(state="attached", timeout=15000)
            await month_select.evaluate("(el, v) => { el.value = v; el.dispatchEvent(new Event('change', {bubbles:true})); }", "6")
            await asyncio.sleep(0.2)
            await day_select.evaluate("(el, v) => { el.value = v; el.dispatchEvent(new Event('change', {bubbles:true})); }", "15")
            await asyncio.sleep(0.2)
            await year_select.evaluate("(el, v) => { el.value = v; el.dispatchEvent(new Event('change', {bubbles:true})); }", "1990")
            await asyncio.sleep(0.5)

            # Try primary XPath selector first, fallback to CSS selector if needed
            if use_id_selectors:
                signup_btn = page.locator('button[type="submit"][data-a-target="passport-signup-button"]')
            else:
                signup_btn = page.locator('xpath=/html/body/div/div[1]/div[1]/div/div/div/div/div[2]/form/div/div[6]/div/button')
            try:
                logger.info(f"[{index}] Waiting for primary signup button...")
                await signup_btn.wait_for(state="attached", timeout=5000)
                logger.info(f"[{index}] Primary signup button found!")
            except Exception as e:
                logger.info(f"[{index}] Primary signup button not found ({e}), trying fallback CSS selector...")
                signup_btn = page.locator('#root > div.Layout-sc-1xcs6mc-0.wpllh > div.scrollable-area > div > div > div > div > div.Layout-sc-1xcs6mc-0.lmgTLF > form > div > div:nth-child(6) > div > button')
                await signup_btn.wait_for(state="attached", timeout=5000)
                logger.info(f"[{index}] Fallback signup button found!")
            
            logger.info(f"[{index}] Clicking signup button...")
            # Click multiple times to ensure it registers, stop if element disappears
            for click_attempt in range(5):
                try:
                    logger.info(f"[{index}] Click attempt {click_attempt + 1}/5...")
                    if click_attempt < 4:
                        # First 4 attempts: short timeout
                        await signup_btn.click(force=True, timeout=2000)
                        await asyncio.sleep(0.3)
                    else:
                        # Last attempt: very short timeout, skip if element not available
                        try:
                            await signup_btn.click(force=True, timeout=500)
                            await asyncio.sleep(0.3)
                        except Exception as last_click_error:
                            logger.info(f"[{index}] Click attempt 5 skipped (element not available)")
                except Exception as click_error:
                    # Element disappeared, likely page navigation happened
                    logger.info(f"[{index}] Click attempt {click_attempt + 1} failed (page changing)")
                    break
            
            logger.info(f"[{index}] Signup button click sequence complete, waiting for page load...")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            logger.info(f"[{index}] Page load complete")

            body_text = await page.locator("body").inner_text()

            if "不允许" in body_text:
                return {"username": username, "email": temp_email, "password": password, "status": "failed", "error": "email domain blocked"}

            if "browser" in body_text.lower() and ("not currently supported" in body_text.lower() or "不受支持" in body_text):
                screenshot_path = Path(f"profiles/browser_not_supported_{index}_attempt_{attempt}.png")
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    await page.screenshot(path=str(screenshot_path))
                    logger.warning(f"[{index}] Browser not supported screenshot saved: {screenshot_path}")
                except Exception as e:
                    logger.warning(f"[{index}] Browser not supported screenshot failed: {e}")
                return {"username": username, "email": temp_email, "password": password, "status": "failed", "error": "browser not supported"}

            if any(kw in body_text for kw in ["验证", "verify", "code", "验证码", "enter the code"]):
                logger.info(f"[{index}] {username} - waiting for verification code...")
                code, _ = await asyncio.get_event_loop().run_in_executor(
                    None, get_verification_code, mail_token, timeout
                )
                if not code:
                    logger.warning(f"[{index}] {username} - verification timeout")
                    if attempt < max_retries:
                        continue
                    return {"username": username, "email": temp_email, "password": password, "status": "failed", "error": "verification timeout"}

                logger.info(f"[{index}] {username} - code: {code}")

                digit_labels = [
                    "Digit 1",
                    "Digit 2",
                    "Digit 3",
                    "Digit 4",
                    "Digit 5",
                    "Digit 6",
                ]
                code_locators = [page.locator(f"input[aria-label='{label}']") for label in digit_labels]
                try:
                    await code_locators[0].wait_for(state="attached", timeout=10000)
                except Exception:
                    logger.warning(f"[{index}] Digit 1 input not found by aria-label, falling back to xpath selectors")
                    code_xpaths = [
                        "/html/body/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[1]/div[2]/div/div[1]/div/div/input",
                        "/html/body/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[1]/div[2]/div/div[2]/div/div/input",
                        "/html/body/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[1]/div[2]/div/div[3]/div/div/input",
                        "/html/body/div/div[1]/div/div/div/div/div[2]/div/div[1]/div[2]/div/div[4]/div/div/input",
                        "/html/body/div/div[1]/div/div/div/div/div[2]/div/div[1]/div[2]/div/div[5]/div/div/input",
                        "/html/body/div/div[1]/div/div/div/div/div[2]/div/div[1]/div[2]/div/div[6]/div/div/input",
                    ]
                    code_locators = [page.locator(f"xpath={xpath}") for xpath in code_xpaths]

                for i, digit in enumerate(code):
                    code_input = code_locators[i]
                    await code_input.wait_for(state="attached", timeout=5000)
                    await code_input.evaluate("(el, val) => { const s = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set; s.call(el, val); el.dispatchEvent(new Event('input', {bubbles:true})); }", digit)
                await asyncio.sleep(1)

                await page.keyboard.press("Enter")
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)

            url = page.url
            body_text = await page.locator("body").inner_text()
            success = "signup" not in url or "welcome" in body_text.lower() or "欢迎" in body_text

            cookies = await context.cookies()
            auth_info = extract_auth(cookies)
            auth_token = auth_info.get("access_token", "") if auth_info else ""

            result = {
                "username": username,
                "email": temp_email,
                "password": password,
                "auth_token": auth_token or "",
                "cookies": _json.dumps(cookies, ensure_ascii=False),
                "status": "success" if success else "failed",
                "error": "" if success else "unclear registration result",
            }

            if success:
                logger.info(f"[{index}] {username} - registered")
            else:
                logger.warning(f"[{index}] {username} - unclear, url={url}")
                # Save screenshot when result is unclear
                try:
                    screenshot_path = Path(f"profiles/final_state_{index}_attempt_{attempt}.png")
                    screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                    await page.screenshot(path=str(screenshot_path))
                    logger.info(f"[{index}] Final state screenshot saved: {screenshot_path}")
                except Exception as e:
                    logger.warning(f"[{index}] Screenshot save failed: {e}")

            return result

        except Exception as e:
            logger.error(f"[{index}] attempt {attempt} error: {e}")

            # 检测是否为 locator.wait_for 超时错误
            e_str = str(e)
            is_wait_for_timeout = False
            try:
                if 'wait_for' in e_str and 'Timeout' in e_str:
                    consecutive_wait_for_timeouts += 1
                    is_wait_for_timeout = True
                else:
                    consecutive_wait_for_timeouts = 0
            except Exception:
                consecutive_wait_for_timeouts = 0

            # 保存异常时的截图以便调试
            try:
                screenshot_path = Path(f"profiles/error_{index}_attempt_{attempt}.png")
                screenshot_path.parent.mkdir(parents=True, exist_ok=True)
                if 'page' in locals() and page is not None:
                    try:
                        await page.screenshot(path=str(screenshot_path))
                        logger.info(f"[{index}] Error screenshot saved: {screenshot_path}")
                    except Exception as se:
                        logger.warning(f"[{index}] Error screenshot failed: {se}")
            except Exception:
                pass

            # 如果连续两次为 wait_for 超时，则直接放弃后续重试，返回失败
            if is_wait_for_timeout and consecutive_wait_for_timeouts >= 2:
                logger.error(f"[{index}] Consecutive wait_for timeouts ({consecutive_wait_for_timeouts}), aborting retries")
                return {"username": locals().get("username", "unknown"), "email": locals().get("temp_email", ""), "password": password, "status": "failed", "error": str(e)}

            if attempt < max_retries:
                logger.info(f"[{index}] retrying...")
                await asyncio.sleep(3)
            else:
                return {"username": locals().get("username", "unknown"), "email": locals().get("temp_email", ""), "password": password, "status": "failed", "error": str(e)}

    return {"status": "failed", "error": "max retries exceeded"}
