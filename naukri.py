import os
import sys
import shutil
import time
from datetime import datetime

from playwright.sync_api import sync_playwright


# ==========================================
# UTF-8
# ==========================================
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8")


# ==========================================
# CONFIG
# ==========================================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

# explicit proxy or system proxy env
PROXY = (
    os.getenv("PROXY")
    or os.getenv("HTTPS_PROXY")
    or os.getenv("HTTP_PROXY")
    or ""
).strip()

SOURCE_RESUME = "Purushottam_Kumar_CV.pdf"
DEST_FOLDER = "Naukri_resume"
RESUME_PREFIX = "Purushottam_Kumar_Resume"

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

PROFILE_DIR = os.path.abspath("playwright_profile")

HOME_URL = "https://www.naukri.com/"
PROFILE_URL = "https://www.naukri.com/mnjuser/profile"

WINDOWS_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/147.0.0.0 Safari/537.36"
)


# ==========================================
# SCREENSHOT
# ==========================================
def snap(page, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=True)
    print("[SCREENSHOT]", path)


# ==========================================
# RESUME
# ==========================================
def generate_resume():
    os.makedirs(DEST_FOLDER, exist_ok=True)

    date = datetime.now().strftime("%d_%b_%Y")
    path = os.path.join(
        DEST_FOLDER,
        f"{RESUME_PREFIX}_{date}.pdf"
    )

    if os.path.exists(path):
        os.remove(path)

    shutil.copy2(SOURCE_RESUME, path)

    print("[SUCCESS] Resume ready:", path)
    return os.path.abspath(path)


# ==========================================
# SAFE OPEN
# ==========================================
def safe_open(page, url):
    try:
        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000
        )
        return True

    except Exception as e:
        print("[WARN] open failed:", e)

        try:
            page.evaluate("window.stop()")
            time.sleep(2)
            return True
        except Exception:
            return False


# ==========================================
# CHECK LOGIN
# ==========================================
def already_logged_in(page):
    if not safe_open(page, PROFILE_URL):
        return False

    time.sleep(3)

    if "login" not in page.url.lower():
        print("[INFO] Already logged in")
        return True

    return False


# ==========================================
# LOGIN
# ==========================================
def login(page):
    print("[INFO] Opening home page")

    if not safe_open(page, HOME_URL):
        return False

    time.sleep(3)
    snap(page, "1_home")

    try:
        page.locator("text=Login").first.click(timeout=15000)

        page.locator("#usernameField").fill(EMAIL)
        page.locator("#passwordField").fill(PASSWORD)

        snap(page, "2_credentials")

        page.locator("button:has-text('Login')").click()

        print("[INFO] Login clicked")

    except Exception as e:
        print("[ERROR] Login failed:", e)
        snap(page, "login_error")
        return False

    time.sleep(6)
    snap(page, "3_after_login")

    html = page.content().lower()

    if "otp" in html:
        print("[ERROR] OTP triggered")
        return False

    if "login" not in page.url.lower():
        print("[SUCCESS] Login successful")
        return True

    print("[ERROR] Login failed")
    return False


# ==========================================
# UPLOAD
# ==========================================
def upload_resume(page, resume_path):
    print("[INFO] Opening profile")

    if not safe_open(page, PROFILE_URL):
        return False

    time.sleep(4)
    snap(page, "4_profile")

    try:
        page.locator("text=Update resume").click(timeout=15000)

        file_input = page.locator("input[type='file']")
        file_input.set_input_files(resume_path)

        time.sleep(4)
        snap(page, "5_uploaded")

        print("[SUCCESS] Resume uploaded")
        return True

    except Exception as e:
        print("[ERROR] Upload failed:", e)
        snap(page, "upload_error")
        return False


# ==========================================
# MAIN
# ==========================================
def main():
    print("===== START =====")

    if not EMAIL or not PASSWORD:
        print("[ERROR] Missing credentials")
        return

    resume_path = generate_resume()

    launch_kwargs = {
        "headless": True,
        "args": [
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ],
    }

    if PROXY:
        print("[INFO] Using proxy:", PROXY)
        launch_kwargs["proxy"] = {"server": PROXY}
    else:
        print("[INFO] No proxy configured, using direct/system network")

    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)

        context = browser.new_context(
            viewport={
                "width": 1920,
                "height": 1080
            },
            locale="en-US",
            user_agent=WINDOWS_UA,
            storage_state=PROFILE_DIR if os.path.exists(PROFILE_DIR) else None
        )

        page = context.new_page()

        try:
            snap(page, "start")

            if already_logged_in(page):
                upload_resume(page, resume_path)
            else:
                if login(page):
                    context.storage_state(path=PROFILE_DIR)
                    upload_resume(page, resume_path)
                else:
                    print("[ERROR] Could not login")

        except Exception as e:
            print("[FATAL]", e)

            try:
                snap(page, "fatal_error")
            except Exception:
                pass

        finally:
            context.close()
            browser.close()

    print("===== DONE =====")


if __name__ == "__main__":
    main()
