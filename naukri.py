import os
import shutil
import time
import random
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

# ==============================
# CONFIG
# ==============================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")
PROXY = os.getenv("PROXY")  # optional

SOURCE_RESUME = "Purushottam_Kumar_CV.pdf"
DEST_FOLDER = "Naukri_resume"
RESUME_PREFIX = "Purushottam_Kumar_Resume"

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# ==============================
# SCREENSHOT FUNCTION
# ==============================
def snap(driver, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    print(f"📸 Screenshot saved: {path}")

# ==============================
# HUMAN TYPING
# ==============================
def type_like_human(element, text):
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.05, 0.15))

# ==============================
# RESUME GENERATE
# ==============================
def generate_resume():
    os.makedirs(DEST_FOLDER, exist_ok=True)

    date = datetime.now().strftime("%d_%b_%Y")
    path = os.path.join(DEST_FOLDER, f"{RESUME_PREFIX}_{date}.pdf")

    if os.path.exists(path):
        os.remove(path)

    shutil.copy2(SOURCE_RESUME, path)
    print("✅ Resume ready:", path)

    return os.path.abspath(path)

# ==============================
# DRIVER
# ==============================
def get_driver():
    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    )

    options.add_argument("--lang=en-US,en;q=0.9")
    options.add_argument("--disable-blink-features=AutomationControlled")

    if PROXY:
        print("🌐 Proxy:", PROXY)
        options.add_argument(f"--proxy-server={PROXY}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
    })

    return driver

# ==============================
# LOGIN (WITH SCREENSHOTS)
# ==============================
def login(driver, wait):
    print("🌐 Opening login page...")
    driver.get("https://www.naukri.com/nlogin/login")
    time.sleep(4)
    snap(driver, "1_login_page")

    if "Access Denied" in driver.title:
        snap(driver, "blocked")
        return False

    try:
        email = wait.until(EC.element_to_be_clickable((By.ID, "usernameField")))
        password = wait.until(EC.element_to_be_clickable((By.ID, "passwordField")))

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", email)

        email.clear()
        type_like_human(email, EMAIL)
        snap(driver, "2_email_filled")

        time.sleep(1)

        password.clear()
        type_like_human(password, PASSWORD)
        snap(driver, "3_password_filled")

        password.send_keys(Keys.RETURN)
        print("🔐 Logging in...")

    except Exception:
        print("⚠️ JS fallback login")
        driver.execute_script("""
            document.getElementById('usernameField').value = arguments[0];
            document.getElementById('passwordField').value = arguments[1];
        """, EMAIL, PASSWORD)
        snap(driver, "2_js_login")

        driver.execute_script("document.querySelector('button[type=\"submit\"]').click();")

    time.sleep(6)
    snap(driver, "4_after_login")

    if "login" not in driver.current_url:
        print("✅ Login success")
        return True
    else:
        print("❌ Login failed")
        snap(driver, "login_failed")
        return False

# ==============================
# UPLOAD RESUME
# ==============================
def upload_resume(driver, wait, resume_path):
    print("📂 Opening profile page...")
    driver.get("https://www.naukri.com/mnjuser/profile")
    time.sleep(5)
    snap(driver, "5_profile_page")

    upload = wait.until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )

    upload.send_keys(resume_path)
    time.sleep(3)

    snap(driver, "6_after_upload")
    print("🎉 Resume uploaded!")

# ==============================
# MAIN
# ==============================
def main():
    print("===== START =====")

    if not EMAIL or not PASSWORD:
        print("❌ Missing credentials")
        return

    resume_path = generate_resume()
    print("📂 Resume:", resume_path)

    driver = get_driver()
    wait = WebDriverWait(driver, 120)

    try:
        snap(driver, "start_browser")

        for attempt in range(3):
            print(f"🔁 Attempt {attempt+1}")

            if login(driver, wait):
                time.sleep(random.uniform(3, 6))
                upload_resume(driver, wait, resume_path)
                snap(driver, "success_end")
                break
            else:
                time.sleep(random.uniform(5, 10))

    except Exception as e:
        print("❌ Error:", e)
        snap(driver, "error")

    finally:
        driver.quit()
        print("🧹 Browser closed")
        print("===== DONE =====")

if __name__ == "__main__":
    main()
