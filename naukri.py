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


logging.basicConfig(level=logging.INFO)


# =========================
# SCREENSHOT SAFE
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
    opt = Options()
    opt.add_argument("--headless=new")
    opt.add_argument("--no-sandbox")
    opt.add_argument("--disable-dev-shm-usage")
    opt.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=opt)


# =========================
# CORE LOGIN FLOW
# =========================
def attempt_login(driver, wait, mode):
    """
    mode:
    1-3 => Login button
    4-5 => OTP button
    """

    driver.get(BASE_URL)
    logging.info("Page loaded")
    ss(driver, f"attempt_{mode}_01_load")
    time.sleep(30)

    # EMAIL
    email = wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
    email.clear()
    email.send_keys(EMAIL)

    ss(driver, f"attempt_{mode}_02_email")
    time.sleep(30)

    # PASSWORD
    pwd = driver.find_element(By.ID, "passwordField")
    pwd.clear()
    pwd.send_keys(PASSWORD)

    ss(driver, f"attempt_{mode}_03_password")
    time.sleep(30)

    # CLICK BUTTON BASED ON MODE
    if mode <= 3:
        btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(text(),'Login')]"))
        )
        logging.info("Clicking LOGIN button")
    else:
        btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class,'otpButton')]"))
        )
        logging.info("Clicking OTP button")

    btn.click()

    ss(driver, f"attempt_{mode}_04_clicked")
    time.sleep(30)

    return driver.current_url


# =========================
# MAIN LOOP (5 TRIES)
# =========================
def run():
    driver = get_driver()
    wait = WebDriverWait(driver, 30)

    try:
        for i in range(1, 6):

            logging.info(f"===== ATTEMPT {i} =====")

            url = attempt_login(driver, wait, i)

            logging.info(f"URL after login: {url}")
            ss(driver, f"attempt_{i}_05_final")

            # SUCCESS CHECK
            if SUCCESS_URL in url:
                logging.info("LOGIN SUCCESS 🎉")
                ss(driver, "SUCCESS")
                return

            time.sleep(30)

        logging.error("LOGIN FAILED after 5 attempts")

    finally:
        try:
            driver.quit()
        except:
            pass
        logging.info("Driver closed")


if __name__ == "__main__":
    run()
