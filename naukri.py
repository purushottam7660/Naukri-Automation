#! python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import shutil
import logging
from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ==============================
# PATHS
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCE_RESUME = os.path.join(BASE_DIR, "Purushottam_Kumar_CV.pdf")
DEST_FOLDER = os.path.join(BASE_DIR, "Naukri_resume")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
DUMP_DIR = os.path.join(BASE_DIR, "html_dump")
LOG_FILE = os.path.join(BASE_DIR, "naukri.log")

os.makedirs(DEST_FOLDER, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(DUMP_DIR, exist_ok=True)


# ==============================
# CONFIG
# ==============================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
NAUKRI_PROFILE_URL = "https://www.naukri.com/mnjuser/profile"

RESUME_PREFIX = "Purushottam_Kumar_Resume"

logging.basicConfig(
    level=logging.INFO,
    filename=LOG_FILE,
    format="%(asctime)s : %(message)s",
)


# ==============================
# LOG
# ==============================
def log_msg(msg):
    print(msg)
    logging.info(msg)


def catch(error):
    _, _, exc_tb = sys.exc_info()
    line_no = str(exc_tb.tb_lineno)
    msg = "%s : %s at Line %s." % (type(error), error, line_no)
    print(msg)
    logging.error(msg)


# ==============================
# SCREENSHOT
# ==============================
def take_screenshot(driver, name):
    try:
        path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        driver.save_screenshot(path)
        log_msg(f"[SCREENSHOT] {path}")
    except Exception:
        pass


# ==============================
# HTML
# ==============================
def dump_html(driver, name):
    try:
        path = os.path.join(DUMP_DIR, f"{name}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        log_msg(f"[HTML] {path}")
    except Exception:
        pass


# ==============================
# RESUME
# ==============================
def generate_resume():
    current_date = datetime.now().strftime("%d_%b_%Y")
    new_filename = f"{RESUME_PREFIX}_{current_date}.pdf"
    destination_path = os.path.join(DEST_FOLDER, new_filename)

    if os.path.exists(destination_path):
        os.remove(destination_path)

    shutil.copy2(SOURCE_RESUME, destination_path)

    log_msg(f"Resume ready: {destination_path}")

    return os.path.abspath(destination_path)


# ==============================
# DRIVER
# ==============================
def LoadNaukri():
    options = webdriver.ChromeOptions()

    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-blink-features=AutomationControlled")

    options.add_experimental_option(
        "excludeSwitches",
        ["enable-automation"]
    )

    options.add_experimental_option(
        "useAutomationExtension",
        False
    )

    driver = webdriver.Chrome(
        service=ChromeService(),
        options=options
    )

    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    driver.implicitly_wait(5)

    driver.get(NAUKRI_LOGIN_URL)

    take_screenshot(driver, "01_login_page")

    return driver


# ==============================
# REMOVE OTP
# ==============================
def remove_otp_button(driver):
    try:
        driver.execute_script("""
            let otp = document.querySelector(
                'button.otpButton'
            );
            if (otp) {
                otp.remove();
            }
        """)
        log_msg("OTP button removed")
    except Exception as e:
        log_msg(f"OTP remove skipped: {e}")


# ==============================
# LOGIN
# ==============================
def naukriLogin():
    driver = LoadNaukri()

    try:
        wait = WebDriverWait(driver, 30)

        email = wait.until(
            EC.presence_of_element_located((By.ID, "usernameField"))
        )

        password = wait.until(
            EC.presence_of_element_located((By.ID, "passwordField"))
        )

        email.clear()
        email.send_keys(EMAIL)

        password.clear()
        password.send_keys(PASSWORD)

        take_screenshot(driver, "02_credentials_filled")

        time.sleep(2)

        remove_otp_button(driver)

        # submit form directly (more stable on GitHub)
        driver.execute_script("""
            let form = document.querySelector("#loginForm");
            if (form) {
                form.submit();
            }
        """)

        log_msg("Form submitted via JS")

        take_screenshot(driver, "03_form_submitted")

        # 10 sec gap
        time.sleep(10)

        take_screenshot(driver, "04_after_10sec")

        current_url = driver.current_url.lower()
        log_msg(f"Current URL: {current_url}")

        if (
            "/mnjuser/homepage" in current_url
            or "/mnjuser/profile" in current_url
        ):
            log_msg("Login successful")
            return True, driver

        dump_html(driver, "login_failed")
        log_msg("Login failed")

        return False, driver

    except TimeoutException as e:
        log_msg(f"Timeout: {e}")
        take_screenshot(driver, "timeout")
        dump_html(driver, "timeout")
        return False, driver

    except Exception as e:
        log_msg(f"Login error: {e}")
        take_screenshot(driver, "login_error")
        dump_html(driver, "login_error")
        return False, driver


# ==============================
# UPLOAD
# ==============================
def UploadResume(driver, resume_path):
    driver.get(NAUKRI_PROFILE_URL)

    time.sleep(5)

    take_screenshot(driver, "05_profile_page")

    upload_input = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@type='file']")
        )
    )

    upload_input.send_keys(resume_path)

    time.sleep(5)

    take_screenshot(driver, "06_resume_uploaded")

    log_msg("Resume uploaded successfully")


# ==============================
# TEARDOWN
# ==============================
def tearDown(driver):
    if driver:
        try:
            driver.quit()
        except Exception:
            pass


# ==============================
# MAIN
# ==============================
def main():
    log_msg("===== START =====")

    if not EMAIL or not PASSWORD:
        log_msg("Missing NAUKRI_EMAIL or NAUKRI_PASSWORD")
        raise SystemExit(1)

    if not os.path.exists(SOURCE_RESUME):
        log_msg(f"Resume not found: {SOURCE_RESUME}")
        raise SystemExit(1)

    driver = None

    try:
        resume_path = generate_resume()

        status, driver = naukriLogin()

        if status:
            UploadResume(driver, resume_path)
        else:
            log_msg("Login failed")

    except Exception as e:
        catch(e)

    finally:
        tearDown(driver)

    log_msg("===== DONE =====")


if __name__ == "__main__":
    main()
