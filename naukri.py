import os
import shutil
import time
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
# USER CONFIG (GitHub Secrets)
# ==============================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

SOURCE_RESUME = "Purushottam_Kumar_CV.pdf"
DEST_FOLDER = "resumes"
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

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    print("🚀 Launching Chrome...")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    return driver

# ==============================
# MAIN AUTOMATION
# ==============================
def upload_to_naukri(resume_path):
    driver = get_driver()
    wait = WebDriverWait(driver, 30)

    try:
        print("🌐 Opening Naukri login...")
        driver.get("https://www.naukri.com/nlogin/login")

        time.sleep(5)

        print("🔍 Waiting for email field...")
        email_field = wait.until(
            EC.element_to_be_clickable((By.ID, "usernameField"))
        )

        driver.execute_script("arguments[0].scrollIntoView();", email_field)
        time.sleep(2)

        email_field.click()
        email_field.clear()
        email_field.send_keys(EMAIL)
        print("✅ Email entered")

        print("🔍 Waiting for password field...")
        password_field = wait.until(
            EC.element_to_be_clickable((By.ID, "passwordField"))
        )

        password_field.click()
        password_field.clear()
        password_field.send_keys(PASSWORD)
        password_field.send_keys(Keys.RETURN)

        print("🔐 Login submitted")
        time.sleep(8)

        print("📍 Current URL after login:", driver.current_url)

        print("📂 Opening profile page...")
        driver.get("https://www.naukri.com/mnjuser/profile")

        time.sleep(5)

        print("📤 Waiting for upload input...")
        upload_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )

        upload_input.send_keys(resume_path)

        print("🎉 Resume uploaded successfully!")

        time.sleep(5)

    except Exception as e:
        print("❌ Error:", e)
        driver.save_screenshot("error.png")
        print("📸 Screenshot saved as error.png")

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
