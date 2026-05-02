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

from webdriver_manager.chrome import ChromeDriverManager

# ==============================
# UTF-8
# ==============================
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8")

# ==============================
# CONFIG
# ==============================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")
PROXY = os.getenv("PROXY")

SOURCE_RESUME = "Purushottam_Kumar_CV.pdf"
DEST_FOLDER = "Naukri_resume"
RESUME_PREFIX = "Purushottam_Kumar_Resume"

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# persistent profile (important)
PROFILE_DIR = os.path.abspath("chrome_profile")

LOGIN_URL = "https://www.naukri.com/nlogin/login"
PROFILE_URL = "https://www.naukri.com/mnjuser/profile"


# ==============================
# SCREENSHOT
# ==============================
def snap(driver, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    print("[SCREENSHOT]", path)


# ==============================
# HUMAN TYPING
# ==============================
def type_like_human(element, text):
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.08, 0.18))


# ==============================
# RESUME GENERATION
# ==============================
def generate_resume():
    os.makedirs(DEST_FOLDER, exist_ok=True)

    date = datetime.now().strftime("%d_%b_%Y")
    path = os.path.join(DEST_FOLDER, f"{RESUME_PREFIX}_{date}.pdf")

    if os.path.exists(path):
        os.remove(path)

    shutil.copy2(SOURCE_RESUME, path)

    print("[SUCCESS] Resume ready:", path)
    return os.path.abspath(path)


# ==============================
# DRIVER
# ==============================
def get_driver():
    options = Options()

    # visible browser is safer than headless
    # options.add_argument("--headless=new")

    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    # persistent browser profile
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    )

    if PROXY:
        print("[INFO] Using proxy:", PROXY)
        options.add_argument(f"--proxy-server={PROXY}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    return driver


# ==============================
# CHECK LOGIN
# ==============================
def already_logged_in(driver):
    driver.get(PROFILE_URL)
    time.sleep(4)

    url = driver.current_url.lower()

    if "login" not in url:
        print("[INFO] Already logged in")
        return True

    return False


# ==============================
# LOGIN
# ==============================
def login(driver, wait):
    print("[INFO] Opening login page")
    driver.get(LOGIN_URL)
    time.sleep(4)
    snap(driver, "1_login_page")

    try:
        email = wait.until(
            EC.element_to_be_clickable((By.ID, "usernameField"))
        )

        password = wait.until(
            EC.element_to_be_clickable((By.ID, "passwordField"))
        )

        email.clear()
        type_like_human(email, EMAIL)
        snap(driver, "2_email_filled")

        password.clear()
        type_like_human(password, PASSWORD)
        snap(driver, "3_password_filled")

        login_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(., 'Login')]"
                )
            )
        )

        time.sleep(random.uniform(1.0, 2.0))
        login_btn.click()

        print("[SUCCESS] Login clicked")

    except Exception as e:
        print("[ERROR] Login flow failed:", e)
        snap(driver, "login_error")
        return False

    time.sleep(6)
    snap(driver, "4_after_login")

    page = driver.page_source.lower()

    if "otp" in page:
        print("[ERROR] OTP triggered")
        return False

    if "login" not in driver.current_url.lower():
        print("[SUCCESS] Login successful")
        return True

    print("[ERROR] Login failed")
    return False


# ==============================
# UPLOAD RESUME
# ==============================
def upload_resume(driver, wait, resume_path):
    print("[INFO] Opening profile page")

    driver.get(PROFILE_URL)
    time.sleep(5)
    snap(driver, "5_profile")

    try:
        update_btn = wait.until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//span[contains(text(),'Update resume')]"
                )
            )
        )

        update_btn.click()
        time.sleep(2)
        snap(driver, "6_popup")

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
        snap(driver, "7_uploaded")

        print("[SUCCESS] Resume uploaded")

    except Exception as e:
        print("[ERROR] Upload failed:", e)
        snap(driver, "upload_error")


# ==============================
# MAIN
# ==============================
def main():
    print("===== START =====")

    if not EMAIL or not PASSWORD:
        print("[ERROR] Missing credentials")
        return

    resume_path = generate_resume()

    driver = get_driver()
    wait = WebDriverWait(driver, 60)

    try:
        snap(driver, "start")

        # first try existing session
        if already_logged_in(driver):
            upload_resume(driver, wait, resume_path)
            snap(driver, "success")
            return

        # single login attempt only
        if login(driver, wait):
            upload_resume(driver, wait, resume_path)
            snap(driver, "success")
        else:
            print("[ERROR] Could not login. OTP probably required.")
            snap(driver, "login_failed")

    except Exception as e:
        print("[ERROR]", e)
        snap(driver, "fatal_error")

    finally:
        driver.quit()
        print("===== DONE =====")


if __name__ == "__main__":
    main()
