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
# CONFIG
# ==============================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

SOURCE_RESUME = "Purushottam_Kumar_CV.pdf"
DEST_FOLDER = "resumes"
RESUME_PREFIX = "Purushottam_Kumar_Resume"

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
def get_driver():
    options = Options()

    # Use headless only for GitHub
    options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    return driver

# ==============================
def login_and_upload(resume_path):
    driver = get_driver()
    wait = WebDriverWait(driver, 30)

    try:
        print("🌐 Opening login page...")
        driver.get("https://www.naukri.com/nlogin/login")

        time.sleep(5)

        print("📄 Page title:", driver.title)

        # Wait for page
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # ==============================
        # LOGIN USING JS (FIXED)
        # ==============================
        print("✉️ Setting email via JS...")
        driver.execute_script(
            "document.getElementById('usernameField').value = arguments[0];",
            EMAIL
        )

        time.sleep(1)

        print("🔑 Setting password via JS...")
        driver.execute_script(
            "document.getElementById('passwordField').value = arguments[0];",
            PASSWORD
        )

        time.sleep(1)

        print("🔐 Clicking login button...")
        driver.execute_script(
            "document.querySelector('button[type=\"submit\"]').click();"
        )

        time.sleep(8)

        print("📍 Current URL:", driver.current_url)

        # Check login success
        if "login" in driver.current_url:
            print("❌ Login failed (blocked or incorrect)")
            driver.save_screenshot("error.png")
            return

        # ==============================
        # UPLOAD RESUME
        # ==============================
        print("📂 Opening profile...")
        driver.get("https://www.naukri.com/mnjuser/profile")

        time.sleep(5)

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
if __name__ == "__main__":
    print("===== Naukri Automation Started =====")

    if not EMAIL or not PASSWORD:
        print("❌ Missing credentials")
        exit(1)

    path = generate_resume()
    login_and_upload(path)

    print("===== Completed =====")
