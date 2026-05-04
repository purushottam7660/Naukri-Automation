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


# ==============================
# USER CONFIGURATION
# ==============================
EMAIL = "purushottam7660@gmail.com"
PASSWORD = "3911Pp@#"

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
        print("Old resume replaced")

    shutil.copy2(SOURCE_RESUME, destination_path)
    print(f"Resume ready: {destination_path}")

    return destination_path


# ==============================
# SETUP DRIVER
# ==============================
def get_driver():
    chrome_options = Options()

    # ❗ Disable headless for reliability (enable later if needed)
    # chrome_options.add_argument("--headless=new")

    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    print("Launching Chrome...")
    driver = webdriver.Chrome(service=Service(), options=chrome_options)
    print("Chrome launched")

    return driver


# ==============================
# LOGIN FUNCTION
# ==============================
def login(driver, wait):
    print("Opening login page...")
    driver.get("https://www.naukri.com/nlogin/login")

    # Email field
    email_field = wait.until(
        EC.element_to_be_clickable((By.ID, "usernameField"))
    )
    driver.execute_script("arguments[0].scrollIntoView(true);", email_field)
    time.sleep(1)
    email_field.clear()
    email_field.send_keys(EMAIL)

    # Password field
    password_field = wait.until(
        EC.element_to_be_clickable((By.ID, "passwordField"))
    )
    password_field.clear()
    password_field.send_keys(PASSWORD)

    # LOGIN BUTTON (important - avoid OTP)
    login_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
    )
    login_btn.click()

    print("Logging in...")
    time.sleep(5)


# ==============================
# UPLOAD RESUME
# ==============================
def upload_resume(driver, wait, resume_path):
    print("Opening profile page...")
    driver.get("https://www.naukri.com/mnjuser/profile")

    upload_input = wait.until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )

    upload_input.send_keys(os.path.abspath(resume_path))
    print("Resume uploaded successfully")

    time.sleep(5)


# ==============================
# MAIN FUNCTION
# ==============================
def upload_to_naukri(resume_path):
    driver = get_driver()
    wait = WebDriverWait(driver, 25)

    try:
        login(driver, wait)
        upload_resume(driver, wait, resume_path)

    except Exception as e:
        print("ERROR:", e)

    finally:
        driver.quit()
        print("Browser closed")


# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    print("===== Naukri Automation Started =====")

    resume_path = generate_resume()
    upload_to_naukri(resume_path)

    print("===== Process Completed =====")
