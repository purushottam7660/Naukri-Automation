import os
import sys
import shutil
import time
import random
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from webdriver_manager.chrome import ChromeDriverManager


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
PROXY = os.getenv("PROXY", "").strip()

SOURCE_RESUME = "Purushottam_Kumar_CV.pdf"
DEST_FOLDER = "Naukri_resume"
RESUME_PREFIX = "Purushottam_Kumar_Resume"

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

HOME_URL = "https://www.naukri.com/"
PROFILE_URL = "https://www.naukri.com/mnjuser/profile"


# ==========================================
# SCREENSHOT
# ==========================================
def snap(driver, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    print("[SCREENSHOT]", path)


# ==========================================
# HUMAN TYPE
# ==========================================
def type_like_human(element, text):
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.05, 0.12))


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
# DRIVER
# ==========================================
def get_driver():
    options = Options()

    options.page_load_strategy = "eager"

    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-http2")
    options.add_argument("--lang=en-US,en")

    # reduce heavy rendering
    options.add_argument("--blink-settings=imagesEnabled=false")

    if PROXY:
        options.add_argument(f"--proxy-server={PROXY}")

    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(
        service=service,
        options=options
    )

    browser_version = driver.capabilities.get("browserVersion", "")
    major = browser_version.split(".")[0]

    real_ua = (
        f"Mozilla/5.0 (X11; Linux x86_64) "
        f"AppleWebKit/537.36 (KHTML, like Gecko) "
        f"Chrome/{major}.0.0.0 Safari/537.36"
    )

    driver.execute_cdp_cmd(
        "Network.setUserAgentOverride",
        {"userAgent": real_ua}
    )

    print("[INFO] Browser version:", browser_version)
    print("[INFO] User-Agent:", real_ua)

    driver.set_page_load_timeout(20)

    return driver


# ==========================================
# SAFE OPEN
# ==========================================
def open_url(driver, url):
    try:
        driver.get(url)
        return True

    except TimeoutException:
        print("[WARN] Page load timeout, stopping load")

        try:
            driver.execute_script("window.stop();")
            time.sleep(2)
            return True
        except Exception:
            return False

    except Exception as e:
        print("[ERROR] Open failed:", e)
        return False


# ==========================================
# CHECK LOGIN
# ==========================================
def already_logged_in(driver):
    if not open_url(driver, PROFILE_URL):
        return False

    time.sleep(3)

    if "login" not in driver.current_url.lower():
        print("[INFO] Already logged in")
        return True

    return False


# ==========================================
# LOGIN
# ==========================================
def login(driver, wait):
    print("[INFO] Opening home page")

    if not open_url(driver, HOME_URL):
        return False

    time.sleep(3)
    snap(driver, "1_home")

    try:
        login_link = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//a[contains(., 'Login')]"
                )
            )
        )

        login_link.click()

        email = wait.until(
            EC.element_to_be_clickable(
                (By.ID, "usernameField")
            )
        )

        password = wait.until(
            EC.element_to_be_clickable(
                (By.ID, "passwordField")
            )
        )

        email.clear()
        type_like_human(email, EMAIL)

        password.clear()
        type_like_human(password, PASSWORD)

        snap(driver, "2_credentials")

        login_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(., 'Login')]"
                )
            )
        )

        time.sleep(1)
        login_btn.click()

    except Exception as e:
        print("[ERROR] Login failed:", e)
        snap(driver, "login_error")
        return False

    time.sleep(6)
    snap(driver, "3_after_login")

    page = driver.page_source.lower()

    if "otp" in page:
        print("[ERROR] OTP triggered")
        return False

    if "login" not in driver.current_url.lower():
        print("[SUCCESS] Login successful")
        return True

    return False


# ==========================================
# UPLOAD
# ==========================================
def upload_resume(driver, wait, resume_path):
    print("[INFO] Opening profile")

    if not open_url(driver, PROFILE_URL):
        return False

    time.sleep(4)
    snap(driver, "4_profile")

    try:
        update_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//span[contains(text(),'Update resume')]"
                )
            )
        )

        driver.execute_script(
            "arguments[0].scrollIntoView(true);",
            update_btn
        )

        time.sleep(1)
        update_btn.click()

        upload = wait.until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//input[@type='file']"
                )
            )
        )

        upload.send_keys(resume_path)

        time.sleep(4)
        snap(driver, "5_uploaded")

        print("[SUCCESS] Resume uploaded")
        return True

    except Exception as e:
        print("[ERROR] Upload failed:", e)
        snap(driver, "upload_error")
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

    driver = get_driver()
    wait = WebDriverWait(driver, 25)

    try:
        snap(driver, "start")

        if already_logged_in(driver):
            upload_resume(driver, wait, resume_path)
            return

        if login(driver, wait):
            upload_resume(driver, wait, resume_path)
        else:
            print("[ERROR] Could not login")

    except Exception as e:
        print("[FATAL]", e)
        snap(driver, "fatal_error")

    finally:
        driver.quit()
        print("===== DONE =====)


if __name__ == "__main__":
    main()
