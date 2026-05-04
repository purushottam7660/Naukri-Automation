import os
import time
import logging
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================
# CONFIG
# =========================
EMAIL = os.getenv("NAUKRI_EMAIL", "your_email_here")
PASSWORD = os.getenv("NAUKRI_PASSWORD", "your_password_here")

BASE_URL = "https://www.naukri.com/nlogin/login"
SUCCESS_URL = "https://www.naukri.com/mnjuser/"

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# =========================
# SAFE SCREENSHOT
# =========================
def ss(driver, name):
    try:
        path = os.path.join(
            SCREENSHOT_DIR,
            f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        driver.save_screenshot(path)
        logging.info(f"[SS] {path}")
    except:
        pass


# =========================
# DRIVER
# =========================
def get_driver():
    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)

    return driver


# =========================
# SAFE PAGE LOAD
# =========================
def open_login_page(driver):
    driver.get(BASE_URL)
    time.sleep(30)
    ss(driver, "01_page_loaded")

    # validate correct page
    if "nlogin" not in driver.current_url:
        raise Exception(f"Wrong page loaded: {driver.current_url}")


# =========================
# WAIT FOR FORM
# =========================
def wait_for_form(driver, wait):
    try:
        wait.until(EC.presence_of_element_located((By.ID, "loginForm")))
        wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
        return True
    except:
        ss(driver, "form_not_found")
        return False


# =========================
# LOGIN ATTEMPT
# =========================
def login_attempt(driver, wait, attempt):
    logging.info(f"===== ATTEMPT {attempt} =====")

    # STEP 1 - OPEN PAGE
    open_login_page(driver)

    ok = wait_for_form(driver, wait)
    if not ok:
        raise Exception("Login form not loaded (possible captcha/block)")

    time.sleep(30)

    # STEP 2 - EMAIL
    email = wait.until(
        EC.presence_of_element_located((By.ID, "usernameField"))
    )
    email.clear()
    email.send_keys(EMAIL)

    ss(driver, f"attempt_{attempt}_email")
    time.sleep(30)

    # STEP 3 - PASSWORD
    pwd = driver.find_element(By.ID, "passwordField")
    pwd.clear()
    pwd.send_keys(PASSWORD)

    ss(driver, f"attempt_{attempt}_password")
    time.sleep(30)

    # STEP 4 - CLICK LOGIN
    btn = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Login')]"))
    )
    btn.click()

    ss(driver, f"attempt_{attempt}_clicked")
    time.sleep(30)

    return driver.current_url


# =========================
# MAIN LOOP (5 RETRIES)
# =========================
def run():
    driver = get_driver()
    wait = WebDriverWait(driver, 30)

    try:
        for i in range(1, 6):

            try:
                url = login_attempt(driver, wait, i)

                logging.info(f"URL: {url}")
                ss(driver, f"attempt_{i}_final")

                if SUCCESS_URL in url:
                    logging.info("LOGIN SUCCESS 🎉")
                    ss(driver, "SUCCESS")
                    return

            except Exception as e:
                logging.error(f"Attempt {i} failed: {e}")
                ss(driver, f"attempt_{i}_error")

            time.sleep(30)

        logging.error("LOGIN FAILED after 5 attempts")

    finally:
        try:
            driver.quit()
        except:
            pass

        logging.info("Driver closed")


# =========================
# START
# =========================
if __name__ == "__main__":
    run()
