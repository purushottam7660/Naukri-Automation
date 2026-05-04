import os
import shutil
import time
import random
import sys
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ==============================
# FIX: UTF-8 console support
# ==============================
sys.stdout.reconfigure(encoding='utf-8')


# ==============================
# CONFIG
# ==============================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

SOURCE_RESUME = "Purushottam_Kumar_CV.pdf"
DEST_FOLDER = "Naukri_resume"
RESUME_PREFIX = "Purushottam_Kumar_Resume"

SCREENSHOT_DIR = "screenshots"
HTML_DIR = "html_dump"


# ==============================
# UTILS
# ==============================
def ensure_dirs():
    os.makedirs(DEST_FOLDER, exist_ok=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(HTML_DIR, exist_ok=True)


def ss(driver, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    print("[SS]", path)


def html(driver, name):
    path = os.path.join(HTML_DIR, f"{name}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)


def human_delay(a=2, b=5):
    time.sleep(random.uniform(a, b))


# ==============================
# RESUME
# ==============================
def generate_resume():
    ensure_dirs()

    date = datetime.now().strftime("%d_%b_%Y")
    new_file = f"{RESUME_PREFIX}_{date}.pdf"
    path = os.path.join(DEST_FOLDER, new_file)

    if os.path.exists(path):
        os.remove(path)

    shutil.copy2(SOURCE_RESUME, path)
    print("[INFO] Resume ready:", path)
    return path


# ==============================
# DRIVER (GITHUB SAFE)
# ==============================
def get_driver():
    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    print("[INFO] Starting Chrome headless")

    driver = webdriver.Chrome(service=Service(), options=options)
    driver.set_page_load_timeout(120)

    return driver


# ==============================
# SAFE PAGE OPEN
# ==============================
def safe_open(driver):
    driver.get("https://www.naukri.com")
    time.sleep(5)
    driver.get("https://www.naukri.com/nlogin/login")
    time.sleep(5)


# ==============================
# LOGIN (FIXED)
# ==============================
def login(driver, wait):
    print("[STEP] Login started")

    safe_open(driver)

    driver.save_screenshot("login_page.png")

    try:
        email = wait.until(
            EC.visibility_of_element_located((By.ID, "usernameField"))
        )
    except:
        driver.save_screenshot("login_failed.png")
        raise Exception("Login page not loaded or blocked by Naukri")

    email.clear()
    email.send_keys(EMAIL)

    pwd = wait.until(
        EC.visibility_of_element_located((By.ID, "passwordField"))
    )

    pwd.clear()
    pwd.send_keys(PASSWORD)

    human_delay()

    btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )

    btn.click()

    print("[INFO] Login submitted")
    time.sleep(10)


# ==============================
# UPLOAD RESUME
# ==============================
def upload_resume(driver, wait, resume_path):
    print("[STEP] Uploading resume")

    driver.get("https://www.naukri.com/mnjuser/profile")
    time.sleep(6)

    upload = wait.until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )

    upload.send_keys(os.path.abspath(resume_path))

    print("[INFO] Resume uploaded")
    time.sleep(5)


# ==============================
# MAIN
# ==============================
def run():
    driver = get_driver()
    wait = WebDriverWait(driver, 40)

    try:
        resume = generate_resume()

        login(driver, wait)
        upload_resume(driver, wait, resume)

        print("[SUCCESS] Automation completed")

    except Exception as e:
        print("[ERROR]", str(e))
        ss(driver, "error")
        html(driver, "error")

    finally:
        driver.quit()
        print("[INFO] Browser closed")


# ==============================
# START
# ==============================
if __name__ == "__main__":
    print("===== START =====")
    run()
    print("===== DONE =====")
