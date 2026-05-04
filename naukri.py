import os
import shutil
import time
import random
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ==============================
# CONFIG
# ==============================
EMAIL = os.getenv("NAUKRI_EMAIL") 
PASSWORD = os.getenv("NAUKRI_PASSWORD") 

FIREFOX_PROFILE_PATH = r"C:\Users\Lenovo\AppData\Roaming\Mozilla\Firefox\Profiles\cckbmrt3.default-release"

SOURCE_RESUME = "Purushottam_Kumar_CV.pdf"
DEST_FOLDER = "Naukri_resume"
RESUME_PREFIX = "Purushottam_Kumar_Resume"

SCREENSHOT_DIR = "screenshots"


# ==============================
# UTILS
# ==============================
def ensure_dirs():
    os.makedirs(DEST_FOLDER, exist_ok=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def ss(driver, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    print(f"[SS] {path}")


def human_delay(a=2, b=5):
    time.sleep(random.uniform(a, b))


def slow_type(element, text):
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.1, 0.3))


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
# DRIVER (WITH PROFILE)
# ==============================
def get_driver():
    options = Options()

    # 🔥 USE EXISTING FIREFOX PROFILE
    options.add_argument("-profile")
    options.add_argument(FIREFOX_PROFILE_PATH)

    # Basic stealth
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)

    print("[INFO] Launching Firefox with profile...")
    driver = webdriver.Firefox(service=Service(), options=options)
    driver.maximize_window()

    # Remove webdriver flag
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    return driver


# ==============================
# CHECK LOGIN
# ==============================
def is_logged_in(driver):
    try:
        driver.get("https://www.naukri.com/mnjuser/profile")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )
        print("[INFO] Already logged in ✅")
        return True
    except:
        print("[INFO] Not logged in ❌")
        return False


# ==============================
# LOGIN (ONLY IF NEEDED)
# ==============================
def login(driver, wait):
    print("[STEP] Logging in...")

    driver.get("https://www.naukri.com/nlogin/login")
    human_delay(4, 6)

    # Email
    email = wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
    email.clear()
    slow_type(email, EMAIL)

    human_delay()

    # Password
    pwd = wait.until(EC.presence_of_element_located((By.ID, "passwordField")))
    pwd.clear()
    slow_type(pwd, PASSWORD)

    human_delay()

    # Click login
    btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
    driver.execute_script("arguments[0].click();", btn)

    print("[INFO] Login submitted (handle OTP manually if asked)")
    human_delay(8, 12)


# ==============================
# UPLOAD RESUME
# ==============================
def upload_resume(driver, wait, resume_path):
    print("[STEP] Opening profile page")

    driver.get("https://www.naukri.com/mnjuser/profile")
    human_delay(5, 7)

    upload = wait.until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )

    upload.send_keys(os.path.abspath(resume_path))

    print("[STEP] Resume uploaded ✅")
    human_delay(5, 7)


# ==============================
# MAIN
# ==============================
def run():
    driver = get_driver()
    wait = WebDriverWait(driver, 30)

    try:
        resume = generate_resume()

        # 🔥 KEY LOGIC: SKIP LOGIN IF SESSION EXISTS
        if not is_logged_in(driver):
            login(driver, wait)

        upload_resume(driver, wait, resume)

        print("🎉 SUCCESS")

    except Exception as e:
        print("❌ ERROR:", e)
        ss(driver, "error")

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
