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
# USER CONFIGURATION
# ==============================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

SOURCE_RESUME = "Purushottam_Kumar_CV.pdf"
DEST_FOLDER = "Naukri_resume"
RESUME_PREFIX = "Purushottam_Kumar_Resume"

SCREENSHOT_DIR = "screenshots"
HTML_DIR = "html_dump"

# ==============================
# IMPORTANT: PROXY (DISABLED BY DEFAULT)
# ==============================
# ⚠️ Free proxy causes timeout issues → KEEP NONE for stability
PROXY = "182.72.150.242:8080"
# Example (ONLY paid proxy recommended):
# PROXY = "http://username:password@ip:port"


# ==============================
# UTILITIES
# ==============================
def ensure_dirs():
    os.makedirs(DEST_FOLDER, exist_ok=True)
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    os.makedirs(HTML_DIR, exist_ok=True)


def take_screenshot(driver, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    print(f"[SS] Saved: {path}")


def dump_html(driver, name):
    path = os.path.join(HTML_DIR, f"{name}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print(f"[HTML] Saved: {path}")


# ==============================
# RESUME GENERATION
# ==============================
def generate_resume():
    ensure_dirs()

    current_date = datetime.now().strftime("%d_%b_%Y")
    new_filename = f"{RESUME_PREFIX}_{current_date}.pdf"
    destination_path = os.path.join(DEST_FOLDER, new_filename)

    if os.path.exists(destination_path):
        os.remove(destination_path)

    shutil.copy2(SOURCE_RESUME, destination_path)
    print(f"[INFO] Resume ready: {destination_path}")

    return destination_path


# ==============================
# FIREFOX DRIVER (STABLE)
# ==============================
def get_driver():
    options = Options()

    # Headless for GitHub Actions
    options.add_argument("--headless")

    # Stability settings
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)

    # User agent
    options.set_preference(
        "general.useragent.override",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) "
        "Gecko/20100101 Firefox/120.0"
    )

    print("[INFO] Launching Firefox...")

    driver = webdriver.Firefox(service=Service(), options=options)
    driver.maximize_window()

    return driver


# ==============================
# LOGIN FLOW
# ==============================
def login(driver, wait):
    print("[STEP] Opening login page")

    driver.get("https://www.naukri.com/nlogin/login")
    time.sleep(3)

    take_screenshot(driver, "01_login_page")
    dump_html(driver, "01_login_page")

    email = wait.until(EC.element_to_be_clickable((By.ID, "usernameField")))
    email.clear()
    email.send_keys(EMAIL)

    password = wait.until(EC.element_to_be_clickable((By.ID, "passwordField")))
    password.clear()
    password.send_keys(PASSWORD)

    take_screenshot(driver, "02_credentials_filled")

    login_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )
    login_btn.click()

    print("[STEP] Logging in...")
    time.sleep(5)

    take_screenshot(driver, "03_after_login")
    dump_html(driver, "03_after_login")


# ==============================
# UPLOAD RESUME
# ==============================
def upload_resume(driver, wait, resume_path):
    print("[STEP] Opening profile page")

    driver.get("https://www.naukri.com/mnjuser/profile")
    time.sleep(5)

    take_screenshot(driver, "04_profile")
    dump_html(driver, "04_profile")

    upload_input = wait.until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )

    upload_input.send_keys(os.path.abspath(resume_path))

    print("[STEP] Resume uploaded")

    time.sleep(5)

    take_screenshot(driver, "05_uploaded")
    dump_html(driver, "05_uploaded")


# ==============================
# MAIN RUN
# ==============================
def run():
    driver = get_driver()
    wait = WebDriverWait(driver, 25)

    try:
        resume_path = generate_resume()

        login(driver, wait)
        upload_resume(driver, wait, resume_path)

        print("✅ SUCCESS: Automation completed")

    except Exception as e:
        print("❌ ERROR:", e)
        take_screenshot(driver, "ERROR")
        dump_html(driver, "ERROR")

    finally:
        driver.quit()
        print("[INFO] Browser closed")


# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    print("===== Naukri Automation Started =====")
    run()
    print("===== Process Completed =====")
