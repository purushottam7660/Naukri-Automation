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
DEST_FOLDER = "Naukri_resume"
RESUME_PREFIX = "Purushottam_Kumar_Resume"

# ==============================
# GENERATE RESUME
# ==============================
def generate_resume():
    os.makedirs(DEST_FOLDER, exist_ok=True)

    current_date = datetime.now().strftime("%d_%b_%Y")
    new_filename = f"{RESUME_PREFIX}_{current_date}.pdf"
    destination_path = os.path.join(DEST_FOLDER, new_filename)

    if os.path.exists(destination_path):
        os.remove(destination_path)

    shutil.copy2(SOURCE_RESUME, destination_path)
    print(f"✅ Resume ready: {destination_path}")

    return os.path.abspath(destination_path)

# ==============================
# SETUP DRIVER
# ==============================
def get_driver():
    chrome_options = Options()

    # ✅ Headless for GitHub
    chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    print("🚀 Launching Chrome...")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    print("✅ Chrome launched")
    return driver

# ==============================
# MAIN AUTOMATION
# ==============================
def upload_to_naukri(resume_path):
    driver = get_driver()
    wait = WebDriverWait(driver, 30)

    try:
        print("🌐 Opening login page...")
        driver.get("https://www.naukri.com/nlogin/login")

        time.sleep(5)

        print("📄 Page Title:", driver.title)

        # Wait for page load
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # ==============================
        # LOGIN USING JS (FIXED)
        # ==============================
        print("✉️ Setting Email...")
        driver.execute_script(
            "document.getElementById('usernameField').value = arguments[0];",
            EMAIL
        )

        time.sleep(1)

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
        # CHECK LOGIN SUCCESS
        # ==============================
        if "login" in driver.current_url:
            print("❌ Login failed (blocked / not filled)")
            driver.save_screenshot("error.png")
            return

        # ==============================
        # OPEN PROFILE
        # ==============================
        print("📂 Opening profile page...")
        driver.get("https://www.naukri.com/mnjuser/profile")

        time.sleep(5)

        # ==============================
        # UPLOAD RESUME
        # ==============================
        print("📤 Uploading resume...")
        upload_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )

        upload_input.send_keys(resume_path)

        print("🎉 Resume uploaded successfully!")

        time.sleep(5)

    except Exception as e:
        print("❌ Error:", e)
        driver.save_screenshot("error.png")

    finally:
        driver.quit()
        print("🧹 Browser closed")

# ==============================
# ENTRY POINT
# ==============================
if __name__ == "__main__":
    print("===== Naukri Automation Started =====")

    if not EMAIL or not PASSWORD:
        print("❌ Missing credentials (check GitHub Secrets)")
        exit(1)

    resume_path = generate_resume()
    upload_to_naukri(resume_path)

    print("===== Process Completed =====")
