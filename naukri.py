import os
import shutil
import time
from datetime import datetime
import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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

# ==============================
# FUNCTION: Generate Resume
# ==============================
def generate_resume():
    os.makedirs(DEST_FOLDER, exist_ok=True)

    current_date = datetime.now().strftime("%d_%b_%Y")
    new_filename = f"{RESUME_PREFIX}_{current_date}.pdf"
    destination_path = os.path.join(DEST_FOLDER, new_filename)

    if os.path.exists(destination_path):
        os.remove(destination_path)
        print("Old resume replaced")

    shutil.copy2(SOURCE_RESUME, destination_path)
    print(f"Resume ready: {destination_path}")

    return destination_path

# ==============================
# FUNCTION: Setup Chrome Driver
# ==============================
def get_driver():
    chrome_options = Options()

    # ✅ STABLE headless mode (fix crash)
    chrome_options.add_argument("--headless=old")

    # ✅ Stability (VERY IMPORTANT)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--incognito")  # ✅ no cookies stored
    chrome_options.add_argument("--disable-application-cache")
    chrome_options.add_argument("--disable-cache")
    chrome_options.add_argument("--disk-cache-size=0")


    # Prevent crash
    chrome_options.add_argument("--remote-debugging-port=9222")

    # Required window size
    chrome_options.add_argument("--window-size=1920,1080")

    # Reduce detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    # Fake user-agent (important for Naukri)
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    print("Launching Chrome...")

    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)

    print("Chrome launched successfully")
    return driver

# ==============================
# FUNCTION: Upload Resume
# ==============================
def upload_to_naukri(resume_path):
    driver = get_driver()
    wait = WebDriverWait(driver, 20)

    try:
        print("Opening Naukri login...")

        driver.get("https://www.naukri.com/nlogin/login")

        # Wait for login page
        wait.until(EC.presence_of_element_located((By.ID, "usernameField")))

        # Enter email
        driver.find_element(By.ID, "usernameField").send_keys(EMAIL)

        # Enter password
        password_field = driver.find_element(By.ID, "passwordField")
        password_field.send_keys(PASSWORD)
        password_field.send_keys(Keys.RETURN)

        print("Logging in...")
        time.sleep(5)

        # Open profile page
        driver.get("https://www.naukri.com/mnjuser/profile")

        # Wait for upload input
        upload_input = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )

        # Upload resume
        upload_input.send_keys(resume_path)

        print("✅ Resume uploaded successfully!")

        time.sleep(5)

    except Exception as e:
        print("❌ Error:", e)

    finally:
        driver.quit()
        print("Browser closed")

# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    print("===== Naukri Automation Started =====")

    resume_path = generate_resume()
    upload_to_naukri(resume_path)

    print("===== Process Completed =====")
