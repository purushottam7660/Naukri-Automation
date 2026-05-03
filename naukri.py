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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================================================
# BASE PATHS
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCE_RESUME = os.path.join(BASE_DIR, "Purushottam_Kumar_CV.pdf")
DEST_FOLDER = os.path.join(BASE_DIR, "Naukri_resume")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
DUMP_DIR = os.path.join(BASE_DIR, "html_dump")
LOG_FILE = os.path.join(BASE_DIR, "naukri.log")

os.makedirs(DEST_FOLDER, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(DUMP_DIR, exist_ok=True)


# =========================================================
# USER CONFIG
# =========================================================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

RESUME_PREFIX = "Purushottam_Kumar_Resume"

NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
NAUKRI_PROFILE_URL = "https://www.naukri.com/mnjuser/profile"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0"
)

LOGIN_XPATH = (
    '//button[@class="waves-effect waves-light btn-large btn-block btn-bold blue-btn textTransform"]'
)

OTP_XPATH = (
    '//button[@class="waves-effect waves-light btn-large btn-block btn-bold otpButton textTransform"]'
)

logging.basicConfig(
    level=logging.INFO,
    filename=LOG_FILE,
    format="%(asctime)s : %(message)s",
)


# =========================================================
# LOGGING
# =========================================================
def log_msg(message):
    print(message)
    logging.info(message)


def catch(error):
    _, _, exc_tb = sys.exc_info()
    line_no = str(exc_tb.tb_lineno)
    msg = f"{type(error)} : {error} at Line {line_no}"
    print(msg)
    logging.error(msg)


# =========================================================
# SCREENSHOT
# =========================================================
def take_screenshot(driver, name):
    try:
        path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        driver.save_screenshot(path)
        log_msg(f"[SCREENSHOT] {path}")
    except Exception:
        pass


# =========================================================
# HTML DUMP
# =========================================================
def dump_html(driver, name):
    try:
        path = os.path.join(DUMP_DIR, f"{name}.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        log_msg(f"[HTML DUMP] {path}")
    except Exception as e:
        log_msg(f"HTML dump failed: {e}")


# =========================================================
# RESUME
# =========================================================
def generate_resume():
    current_date = datetime.now().strftime("%d_%b_%Y")
    new_filename = f"{RESUME_PREFIX}_{current_date}.pdf"
    destination_path = os.path.join(DEST_FOLDER, new_filename)

    if os.path.exists(destination_path):
        os.remove(destination_path)

    shutil.copy2(SOURCE_RESUME, destination_path)

    log_msg(f"Resume ready: {destination_path}")
    return os.path.abspath(destination_path)


# =========================================================
# CHROME
# =========================================================
def LoadNaukri():
    options = webdriver.ChromeOptions()

    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popups")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    options.add_argument(f"--user-agent={USER_AGENT}")

    proxy = (
        os.getenv("HTTPS_PROXY")
        or os.getenv("HTTP_PROXY")
        or os.getenv("https_proxy")
        or os.getenv("http_proxy")
    )

    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
        log_msg(f"Using proxy: {proxy}")
    else:
        log_msg("Using default proxy")

    driver = webdriver.Chrome(
        service=ChromeService(),
        options=options
    )

    driver.implicitly_wait(5)

    driver.get(NAUKRI_LOGIN_URL)

    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.ID, "usernameField"))
    )

    take_screenshot(driver, "01_page_loaded")

    return driver


# =========================================================
# REMOVE OTP BUTTON
# =========================================================
def remove_otp_button(driver):
    try:
        otp_buttons = driver.find_elements(By.XPATH, OTP_XPATH)

        for otp in otp_buttons:
            driver.execute_script(
                """
                if (arguments[0] && arguments[0].parentNode) {
                    arguments[0].parentNode.removeChild(arguments[0]);
                }
                """,
                otp
            )

        log_msg("OTP button removed")
        take_screenshot(driver, "02_otp_removed")

    except Exception as e:
        log_msg(f"OTP removal skipped: {e}")


# =========================================================
# LOGIN SUCCESS CHECK
# =========================================================
def login_success(driver):
    url = driver.current_url.lower()
    log_msg(f"Current URL: {url}")

    if "/mnjuser/" in url:
        return True

    return False


# =========================================================
# LOGIN
# =========================================================
def naukriLogin():
    driver = LoadNaukri()

    try:
        log_msg("Login started")

        email = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "usernameField"))
        )

        password = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.ID, "passwordField"))
        )

        email.clear()
        email.send_keys(EMAIL)
        take_screenshot(driver, "03_email_filled")

        password.clear()
        password.send_keys(PASSWORD)
        take_screenshot(driver, "04_password_filled")

        time.sleep(2)

        # REMOVE OTP BUTTON
        remove_otp_button(driver)

        # WAIT 10 SEC BEFORE CLICK
        log_msg("Waiting 10 seconds before click")
        time.sleep(10)

        login_btn = WebDriverWait(driver, 100).until(
            EC.element_to_be_clickable((By.XPATH, LOGIN_XPATH))
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            login_btn
        )

        time.sleep(1)

        driver.execute_script("arguments[0].click();", login_btn)

        log_msg("Login button clicked")
        take_screenshot(driver, "05_login_clicked")

        # WAIT 10 SEC AFTER CLICK
        log_msg("Waiting 10 seconds after click")
        time.sleep(10)

        take_screenshot(driver, "06_after_click")

        if login_success(driver):
            log_msg("Login successful")
            return True, driver

        if NAUKRI_LOGIN_URL in driver.current_url:
            log_msg("Still on login page")
            take_screenshot(driver, "07_login_failed")
            dump_html(driver, "login_failed")

        return False, driver

    except TimeoutException as e:
        log_msg(f"Login timeout: {e}")
        take_screenshot(driver, "login_timeout")
        dump_html(driver, "login_timeout")
        return False, driver

    except Exception as e:
        log_msg(f"Login error: {e}")
        take_screenshot(driver, "login_error")
        dump_html(driver, "login_error")
        return False, driver


# =========================================================
# UPLOAD RESUME
# =========================================================
def UploadResume(driver, resume_path):
    driver.get(NAUKRI_PROFILE_URL)

    time.sleep(5)
    take_screenshot(driver, "08_profile_page")

    upload_input = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )

    upload_input.send_keys(resume_path)

    time.sleep(5)
    take_screenshot(driver, "09_resume_uploaded")

    log_msg("Resume uploaded successfully")


# =========================================================
# TEARDOWN
# =========================================================
def tearDown(driver):
    if driver:
        try:
            driver.quit()
        except Exception:
            pass


# =========================================================
# MAIN
# =========================================================
def main():
    log_msg("===== START =====")

    if not EMAIL or not PASSWORD:
        log_msg("Missing NAUKRI_EMAIL or NAUKRI_PASSWORD")
        raise SystemExit(1)

    if not os.path.exists(SOURCE_RESUME):
        log_msg(f"Resume file not found: {SOURCE_RESUME}")
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

    log_msg("===== END =====")


if __name__ == "__main__":
    main()
