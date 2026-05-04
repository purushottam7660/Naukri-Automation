import os
import shutil
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
    print(f"[SS] {path}")


def html(driver, name):
    path = os.path.join(HTML_DIR, f"{name}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)


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
# DRIVER (IMPORTANT FIX HERE)
# ==============================
def get_driver():
    options = Options()

    # ⚠️ REMOVE HEADLESS (FIX FOR YOUR ISSUE)
    # options.add_argument("--headless")

    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)

    options.set_preference(
        "general.useragent.override",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
    )

    print("[INFO] Launching Firefox...")
    driver = webdriver.Firefox(service=Service(), options=options)
    driver.maximize_window()

    return driver


# ==============================
# LOGIN FIXED (IMPORTANT PART)
# ==============================
def login(driver, wait):
    print("[STEP] Opening login page")

    driver.get("https://www.naukri.com/nlogin/login")

    time.sleep(5)  # allow full JS load

    ss(driver, "login_page")
    html(driver, "login_page")

    # EMAIL
    email = wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
    email.clear()
    email.send_keys(EMAIL)

    time.sleep(1)

    # PASSWORD
    pwd = wait.until(EC.presence_of_element_located((By.ID, "passwordField")))
    pwd.clear()
    pwd.send_keys(PASSWORD)

    ss(driver, "filled_credentials")

    time.sleep(2)

    # LOGIN BUTTON (FIX: JS CLICK SAFE)
    try:
        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        driver.execute_script("arguments[0].click();", btn)
    except:
        pwd.send_keys(Keys.RETURN)

    print("[STEP] Login clicked")

    time.sleep(8)

    ss(driver, "after_login")
    html(driver, "after_login")


# ==============================
# UPLOAD
# ==============================
def upload_resume(driver, wait, resume_path):
    print("[STEP] Opening profile")

    driver.get("https://www.naukri.com/mnjuser/profile")

    time.sleep(6)

    ss(driver, "profile")
    html(driver, "profile")

    upload = wait.until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )

    upload.send_keys(os.path.abspath(resume_path))

    print("[STEP] Resume uploaded")

    time.sleep(5)

    ss(driver, "uploaded")
    html(driver, "uploaded")


# ==============================
# MAIN
# ==============================
def run():
    driver = get_driver()
    wait = WebDriverWait(driver, 30)

    try:
        resume = generate_resume()

        login(driver, wait)
        upload_resume(driver, wait, resume)

        print("✅ SUCCESS")

    except Exception as e:
        print("❌ ERROR:", e)
        ss(driver, "ERROR")
        html(driver, "ERROR")

    finally:
        driver.quit()
        print("[INFO] Closed")


# ==============================
# START
# ==============================
if __name__ == "__main__":
    print("===== START =====")
    run()
    print("===== DONE =====")
