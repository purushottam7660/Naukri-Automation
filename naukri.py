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
# CONFIG (GitHub Secrets)
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

    date = datetime.now().strftime("%d_%b_%Y")
    path = os.path.join(DEST_FOLDER, f"{RESUME_PREFIX}_{date}.pdf")

    if os.path.exists(path):
        os.remove(path)

    shutil.copy2(SOURCE_RESUME, path)
    print("✅ Resume ready:", path)

    # ✅ IMPORTANT: Absolute path for Selenium
    return os.path.abspath(path)

# ==============================
# SETUP DRIVER (GitHub Friendly)
# ==============================
def get_driver():
    options = Options()

    # 🔴 MUST for GitHub
    options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # reduce detection
    options.add_argument("--disable-blink-features=AutomationControlled")

    print("🚀 Launching Chrome...")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    print("✅ Chrome launched")
    return driver

# ==============================
# LOGIN
# ==============================
def login(driver, wait):
    print("🌐 Opening login page...")
    driver.get("https://www.naukri.com/nlogin/login")

    email = wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
    password = driver.find_element(By.ID, "passwordField")

    email.clear()
    password.clear()

    email.send_keys(EMAIL)
    time.sleep(0.5)
    password.send_keys(PASSWORD)
    time.sleep(0.5)

    password.send_keys(Keys.RETURN)

    print("🔐 Logging in...")

    try:
        wait.until(lambda d: "login" not in d.current_url)
        print("✅ Login success")
        return True
    except:
        print("❌ Login failed")
        driver.save_screenshot("login_error.png")
        return False

# ==============================
# UPLOAD RESUME
# ==============================
def upload_resume(driver, wait, resume_path):
    print("📂 Opening profile...")
    driver.get("https://www.naukri.com/mnjuser/profile")

    upload = wait.until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )

    print("📤 Uploading:", resume_path)
    upload.send_keys(resume_path)

    print("🎉 Resume uploaded!")

# ==============================
# MAIN
# ==============================
def main():
    print("===== START =====")

    if not EMAIL or not PASSWORD:
        print("❌ Missing credentials")
        return

    print("🔍 Debug:")
    print("Email:", EMAIL)
    print("Password length:", len(PASSWORD))

    resume_path = generate_resume()
    print("📂 Absolute path:", resume_path)

    driver = get_driver()
    wait = WebDriverWait(driver, 25)

    try:
        for i in range(2):  # retry
            print(f"🔁 Attempt {i+1}")

            if login(driver, wait):
                upload_resume(driver, wait, resume_path)
                break
            else:
                print("Retrying...")
                time.sleep(3)

    except Exception as e:
        print("❌ Error:", e)
        driver.save_screenshot("error.png")

    finally:
        driver.quit()
        print("🧹 Browser closed")
        print("===== DONE =====")

# ==============================
if __name__ == "__main__":
    main()
