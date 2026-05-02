import os
import shutil
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


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
# FUNCTION: EDGE DRIVER
# ==============================
def get_edge_driver():
    options = EdgeOptions()

    options.add_argument("--headless=new")
    options.add_argument("--inprivate")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    print("Launching Microsoft Edge...")

    return webdriver.Edge(options=options)


# ==============================
# FUNCTION: CHROME DRIVER
# ==============================
def get_chrome_driver():
    options = ChromeOptions()

    options.add_argument("--headless=new")
    options.add_argument("--incognito")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    print("Launching Chrome...")

    return webdriver.Chrome(options=options)


# ==============================
# FUNCTION: FIND LOGIN INPUTS
# ==============================
def wait_for_login_inputs(driver):
    wait = WebDriverWait(driver, 40)

    try:
        wait.until(
            lambda d: (
                len(d.find_elements(By.ID, "usernameField")) > 0
                or len(d.find_elements(By.XPATH, "//input[@type='email']")) > 0
            )
        )
    except TimeoutException:
        take_screenshot(driver, "login_inputs_not_found")
        raise Exception("Login inputs not found")

    email_candidates = [
        (By.ID, "usernameField"),
        (By.XPATH, "//input[@type='email']")
    ]

    password_candidates = [
        (By.ID, "passwordField"),
        (By.XPATH, "//input[@type='password']")
    ]

    email_field = None
    password_field = None

    for by, value in email_candidates:
        elems = driver.find_elements(by, value)
        if elems:
            email_field = elems[0]
            break

    for by, value in password_candidates:
        elems = driver.find_elements(by, value)
        if elems:
            password_field = elems[0]
            break

    if not email_field or not password_field:
        take_screenshot(driver, "login_fields_missing")
        raise Exception("Login fields not found")

    return email_field, password_field


# ==============================
# FUNCTION: CLICK EXACT LOGIN
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
# FUNCTION: LOGIN
# ==============================
def login_to_naukri(driver, browser_name):
    print(f"Opening Naukri login using {browser_name}...")

    driver.get("https://www.naukri.com/nlogin/login")

    time.sleep(5)

    take_screenshot(driver, f"{browser_name}_01_login_page")

    email_field, password_field = wait_for_login_inputs(driver)

    email_field.clear()
    email_field.send_keys(EMAIL)

    take_screenshot(driver, f"{browser_name}_02_email_entered")

    password_field.clear()
    password_field.send_keys(PASSWORD)

    take_screenshot(driver, f"{browser_name}_03_password_entered")

    time.sleep(2)

    if not click_real_login_button(driver):
        take_screenshot(driver, f"{browser_name}_login_button_missing")
        raise Exception("Login button not found")

    time.sleep(6)

    take_screenshot(driver, f"{browser_name}_04_after_login")


# ==============================
# FUNCTION: UPLOAD RESUME
# ==============================
def upload_resume(driver, browser_name, resume_path):
    print("Opening profile page...")

    driver.get("https://www.naukri.com/mnjuser/profile")

    wait = WebDriverWait(driver, 30)

    time.sleep(4)

    take_screenshot(driver, f"{browser_name}_05_profile_page")

    upload_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@type='file']")
        )
    )

    upload_input.send_keys(resume_path)

    time.sleep(4)

    take_screenshot(driver, f"{browser_name}_06_resume_uploaded")

    print("Resume uploaded successfully")


# ==============================
# FUNCTION: RUN ONE BROWSER
# ==============================
def run_browser(driver_factory, browser_name, resume_path):
    driver = driver_factory()

    try:
        take_screenshot(driver, f"{browser_name}_00_started")

        login_to_naukri(driver, browser_name)

        upload_resume(driver, browser_name, resume_path)

        take_screenshot(driver, f"{browser_name}_07_final")

        return True

    finally:
        driver.quit()
        print(f"{browser_name} closed")


# ==============================
# FUNCTION: MAIN FLOW
# ==============================
def upload_to_naukri(resume_path):
    try:
        print("Trying Microsoft Edge first...")
        return run_browser(get_edge_driver, "edge", resume_path)

    except Exception as e:
        print("Edge skipped/failed:", e)

    print("Retrying with Chrome...")
    return run_browser(get_chrome_driver, "chrome", resume_path)


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
