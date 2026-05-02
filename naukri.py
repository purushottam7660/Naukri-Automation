import os
import shutil
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
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
# FUNCTION: EDGE DRIVER
# ==============================
def get_edge_driver():
    options = EdgeOptions()

    options.add_argument("--headless=new")
    options.add_argument("--inprivate")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-application-cache")
    options.add_argument("--disable-cache")
    options.add_argument("--disk-cache-size=0")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    print("Launching Microsoft Edge...")

    driver = webdriver.Edge(options=options)

    print("Microsoft Edge launched successfully")

    return driver


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
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-application-cache")
    options.add_argument("--disable-cache")
    options.add_argument("--disk-cache-size=0")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    print("Launching Chrome...")

    driver = webdriver.Chrome(options=options)

    print("Chrome launched successfully")

    return driver


# ==============================
# FUNCTION: CLICK EXACT LOGIN BUTTON
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

                print("Clicked Login button")
                return True

        except Exception:
            continue

    return False


# ==============================
# FUNCTION: LOGIN
# ==============================
def login_to_naukri(driver, wait, browser_name):
    print(f"Opening Naukri login using {browser_name}...")

    driver.get("https://www.naukri.com/nlogin/login")

    time.sleep(4)

    take_screenshot(driver, f"{browser_name}_01_login_page")

    wait.until(
        EC.presence_of_element_located((By.ID, "usernameField"))
    )

    email_field = driver.find_element(By.ID, "usernameField")
    email_field.clear()
    email_field.send_keys(EMAIL)

    take_screenshot(driver, f"{browser_name}_02_email_entered")

    password_field = driver.find_element(By.ID, "passwordField")
    password_field.clear()
    password_field.send_keys(PASSWORD)

    take_screenshot(driver, f"{browser_name}_03_password_entered")

    time.sleep(2)

    if not click_real_login_button(driver):
        raise Exception("Login button not found")

    time.sleep(6)

    take_screenshot(driver, f"{browser_name}_04_after_login")

    current_url = driver.current_url.lower()

    if "login" in current_url:
        raise Exception("Login did not complete")

    print(f"Login successful using {browser_name}")


# ==============================
# FUNCTION: UPLOAD RESUME
# ==============================
def upload_resume(driver, wait, resume_path, browser_name):
    print("Opening profile page...")

    driver.get("https://www.naukri.com/mnjuser/profile")

    time.sleep(4)

    take_screenshot(driver, f"{browser_name}_05_profile_page")

    upload_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@type='file']")
        )
    )

    take_screenshot(driver, f"{browser_name}_06_upload_input")

    upload_input.send_keys(resume_path)

    time.sleep(4)

    take_screenshot(driver, f"{browser_name}_07_resume_uploaded")

    print("Resume uploaded successfully")


# ==============================
# FUNCTION: RUN ONE BROWSER
# ==============================
def run_browser(driver_factory, browser_name, resume_path):
    driver = driver_factory()
    wait = WebDriverWait(driver, 30)

    try:
        take_screenshot(driver, f"{browser_name}_00_started")

        login_to_naukri(driver, wait, browser_name)

        upload_resume(driver, wait, resume_path, browser_name)

        take_screenshot(driver, f"{browser_name}_08_final")

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
        print("Edge failed:", e)

    try:
        print("Retrying with Chrome...")
        return run_browser(get_chrome_driver, "chrome", resume_path)

    except Exception as e:
        print("Chrome failed:", e)
        raise


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
