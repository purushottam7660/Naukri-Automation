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

USE_PROXY = False
PROXY = "http://your-proxy:port"   # if needed

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


def save_screenshot(driver, name):
    path = os.path.join(
        SCREENSHOT_DIR,
        f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    )
    driver.save_screenshot(path)
    logging.info(f"[SCREENSHOT] {path}")


# =========================
# DRIVER SETUP
# =========================
def get_driver():
    options = Options()

    # Reduce "access denied"
    # options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--user-data-dir=/tmp/chrome-profile")

    options.add_argument("--start-maximized")
    # options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # User-Agent spoof
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    if USE_PROXY:
        options.add_argument(f"--proxy-server={PROXY}")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)

    return driver


# =========================
# LOGIN FUNCTION
# =========================
def login(driver):
    wait = WebDriverWait(driver, 20)

    driver.get(BASE_URL)
    time.sleep(3)
    save_screenshot(driver, "login_page")

    # Enter email
    email_box = wait.until(
        EC.presence_of_element_located((By.ID, "usernameField"))
    )
    email_box.clear()
    email_box.send_keys(EMAIL)
    time.sleep(2)

    # Enter password
    password_box = driver.find_element(By.ID, "passwordField")
    password_box.clear()
    password_box.send_keys(PASSWORD)
    time.sleep(2)

    save_screenshot(driver, "filled_credentials")

    # Click Login button (robust selector)
    try:
        login_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[normalize-space()='Login']")
            )
        )
        login_btn.click()

    except Exception:
        # fallback (sometimes span/button changes)
        login_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(.,'Login')]")
            )
        )
        login_btn.click()

    time.sleep(5)
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

        # Example: post-login wait check
        time.sleep(5)

        logging.info("Automation completed successfully")

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        save_screenshot(driver, "error")

    finally:
        driver.quit()
        logging.info("Driver closed")


if __name__ == "__main__":
    main()
