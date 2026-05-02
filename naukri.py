import os
import shutil
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

# ==============================
# CONFIG (GitHub Secrets / Local fallback)
# ==============================
EMAIL = os.getenv("NAUKRI_EMAIL") or "your_email_here"
print(EMAIL)
PASSWORD = os.getenv("NAUKRI_PASSWORD") or "your_password_here"
print(PASSWORD)

SOURCE_RESUME = "Purushottam_Kumar_CV.pdf"
DEST_FOLDER = "Naukri_resume"
RESUME_PREFIX = "Purushottam_Kumar_Resume"

# ==============================
# GENERATE RESUME
# ==============================
def generate_resume():
    os.makedirs(DEST_FOLDER, exist_ok=True)

    date = datetime.now().strftime("%d_%b_%Y")
    new_file = f"{RESUME_PREFIX}_{date}.pdf"
    path = os.path.join(DEST_FOLDER, new_file)

    if os.path.exists(path):
        os.remove(path)

    shutil.copy2(SOURCE_RESUME, path)
    print("✅ Resume ready:", path)

    return os.path.abspath(path)

# ==============================
# SETUP DRIVER
# ==============================
def get_driver():
    options = Options()

    # 🔹 For GitHub keep this ON
    options.add_argument("--headless=new")

    # 🔹 For LOCAL (better success), comment above line

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    options.add_argument("--disable-blink-features=AutomationControlled")

    print("🚀 Launching Chrome...")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    print("✅ Chrome launched")
    return driver

# ==============================
# LOGIN + UPLOAD
# ==============================
def upload_to_naukri(resume_path):
    driver = get_driver()
    wait = WebDriverWait(driver, 30)

    try:
        print("🌐 Opening login page...")
        driver.get("https://www.naukri.com/nlogin/login")

        time.sleep(5)

        print("📄 Page Title:", driver.title)

        # ✅ WAIT until element exists (FIX for null error)
        print("⏳ Waiting for login fields...")
        wait.until(lambda d: d.execute_script(
            "return document.getElementById('usernameField') !== null"
        ))

        time.sleep(2)

        # ==============================
        # LOGIN USING JS (STABLE)
        # ==============================
        print("✉️ Setting Email...")
        driver.execute_script(
            "document.getElementById('usernameField').value = arguments[0];",
            EMAIL
        )

        print("🔑 Setting Password...")
        driver.execute_script(
            "document.getElementById('passwordField').value = arguments[0];",
            PASSWORD
        )

        time.sleep(1)

        print("🔐 Clicking Login...")
        driver.execute_script(
            "document.querySelector('button[type=\"submit\"]').click();"
        )

        time.sleep(8)

        print("📍 Current URL:", driver.current_url)

        # ==============================
        # CHECK LOGIN
        # ==============================
        if "login" in driver.current_url:
            print("❌ Login failed (blocked / wrong / captcha)")
            driver.save_screenshot("error.png")
            return

        # ==============================
        # OPEN PROFILE
        # ==============================
        print("📂 Opening profile...")
        driver.get("https://www.naukri.com/mnjuser/profile")

        time.sleep(5)

        # ==============================
        # UPLOAD RESUME
        # ==============================
        print("📤 Uploading resume...")
        upload = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )

        upload.send_keys(resume_path)

        print("🎉 Resume uploaded successfully!")

        time.sleep(5)

    except Exception as e:
        print("❌ Error:", e)
        driver.save_screenshot("error.png")

    finally:
        driver.quit()
        print("🧹 Browser closed")

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    print("===== Naukri Automation Started =====")

    if not EMAIL or not PASSWORD:
        print("❌ Missing credentials")
        exit(1)

    resume_path = generate_resume()
    upload_to_naukri(resume_path)

    print("===== Process Completed =====")
