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
def save_screenshot(driver, name):
    try:
        if driver is None:
            return

        path = os.path.join(
            SCREENSHOT_DIR,
            f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )

        driver.save_screenshot(path)
        logging.info(f"[SCREENSHOT] {path}")

    except Exception as e:
        logging.warning(f"Screenshot skipped: {e}")


# =========================
# DRIVER SETUP (STEALTH)
# =========================
def get_driver():
    options = Options()

    # 🔥 CRITICAL FIX FOR DETECTION
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # 🔥 anti automation flags
    options.add_argument("--disable-blink-features=AutomationControlled")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # User agent
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)

    # hide webdriver flag
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver


# =========================
# HUMAN TYPING
# =========================
def human_type(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(0.1)


# =========================
# LOGIN FUNCTION
# =========================
def login(driver):
    wait = WebDriverWait(driver, 30)

    driver.get(BASE_URL)
    time.sleep(5)
    save_screenshot(driver, "login_page")

    # EMAIL
    email_box = wait.until(
        EC.presence_of_element_located((By.ID, "usernameField"))
    )
    email_box.clear()
    human_type(email_box, EMAIL)
    time.sleep(2)

    # PASSWORD
    password_box = driver.find_element(By.ID, "passwordField")
    password_box.clear()
    human_type(password_box, PASSWORD)
    time.sleep(2)

    save_screenshot(driver, "filled_credentials")

    # LOGIN CLICK
    try:
        login_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,'Login')]"))
        )
        login_btn.click()

    except Exception:
        login_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Login']"))
        )
        login_btn.click()

    time.sleep(8)
    save_screenshot(driver, "after_login")

    logging.info("Login attempt completed")


# =========================
# MAIN
# =========================
def main():
    logging.info("===== START =====")

    driver = get_driver()

    try:
        login(driver)

        time.sleep(5)
        logging.info("Automation completed successfully")

        save_screenshot(driver, "success")

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        save_screenshot(driver, "error")

    finally:
        try:
            save_screenshot(driver, "before_close")
        except:
            pass

        try:
            driver.quit()
        except:
            pass

        logging.info("Driver closed safely")


if __name__ == "__main__":
    main()
