import os
import shutil
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
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
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# ==============================
# FUNCTION: SCREENSHOT
# ==============================
def take_screenshot(driver, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    print(f"[SCREENSHOT] {path}")


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

    return os.path.abspath(destination_path)


# ==============================
# FUNCTION: Setup Chrome Driver
# ==============================
def get_driver():
    chrome_options = Options()

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-application-cache")
    chrome_options.add_argument("--disable-cache")
    chrome_options.add_argument("--disk-cache-size=0")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    print("Launching Chrome...")

    driver = webdriver.Chrome(options=chrome_options)

    print("Chrome launched successfully")

    return driver


# ==============================
# FUNCTION: CLICK REAL LOGIN BUTTON
# ==============================
def click_real_login_button(driver):
    buttons = driver.find_elements(By.XPATH, "//button[@type='submit']")

    for btn in buttons:
        try:
            text = btn.text.strip()

            if text == "Login":
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    btn
                )

                time.sleep(1)

                driver.execute_script(
                    "arguments[0].click();",
                    btn
                )

                print("Clicked exact Login button")
                return True

        except Exception:
            continue

    return False


# ==============================
# FUNCTION: Login
# ==============================
def login_to_naukri(driver, wait):
    print("Opening Naukri login...")

    driver.get("https://www.naukri.com/nlogin/login")

    time.sleep(4)

    take_screenshot(driver, "01_login_page")

    wait.until(
        EC.presence_of_element_located((By.ID, "usernameField"))
    )

    email_field = driver.find_element(By.ID, "usernameField")
    email_field.clear()
    email_field.send_keys(EMAIL)

    take_screenshot(driver, "02_email_entered")

    password_field = driver.find_element(By.ID, "passwordField")
    password_field.clear()
    password_field.send_keys(PASSWORD)

    take_screenshot(driver, "03_password_entered")

    time.sleep(2)

    take_screenshot(driver, "04_before_login_click")

    if not click_real_login_button(driver):
        raise Exception("Exact Login button not found")

    time.sleep(6)

    take_screenshot(driver, "05_after_login")


# ==============================
# FUNCTION: Upload Resume
# ==============================
def upload_resume(driver, wait, resume_path):
    print("Opening profile page...")

    driver.get("https://www.naukri.com/mnjuser/profile")

    time.sleep(4)

    take_screenshot(driver, "06_profile_page")

    upload_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@type='file']")
        )
    )

    take_screenshot(driver, "07_upload_input_found")

    upload_input.send_keys(resume_path)

    time.sleep(4)

    take_screenshot(driver, "08_resume_uploaded")

    print("Resume uploaded successfully")


# ==============================
# FUNCTION: Upload Flow
# ==============================
def upload_to_naukri(resume_path):
    driver = get_driver()
    wait = WebDriverWait(driver, 30)

    try:
        take_screenshot(driver, "00_browser_started")

        login_to_naukri(driver, wait)

        upload_resume(driver, wait, resume_path)

        time.sleep(3)

        take_screenshot(driver, "09_final_state")

    except Exception as e:
        print("Error:", e)

        try:
            take_screenshot(driver, "error")
        except Exception:
            pass

        raise

    finally:
        driver.quit()
        print("Browser closed")


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    print("===== Naukri Automation Started =====")

    if not EMAIL or not PASSWORD:
        print("Missing NAUKRI_EMAIL or NAUKRI_PASSWORD")
        raise SystemExit(1)

    resume_path = generate_resume()

    upload_to_naukri(resume_path)

    print("===== Process Completed =====")
