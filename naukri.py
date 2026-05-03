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

LOGIN_BUTTON_XPATH = (
    '//button[@class="waves-effect waves-light btn-large btn-block btn-bold blue-btn textTransform"]'
)

OTP_BUTTON_XPATH = (
    '//button[@class="waves-effect waves-light btn-large btn-block btn-bold otpButton textTransform"]'
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/147.0.0.0 Safari/537.36"
)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s : %(message)s"
)


# ==============================
# LOGGING
# ==============================
def log_msg(message):
    print(message)
    logging.info(message)


def catch(error):
    _, _, exc_tb = sys.exc_info()
    line_no = str(exc_tb.tb_lineno)
    msg = f"{type(error)} : {error} at line {line_no}"
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
# HTML DUMP
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
    filename = f"{RESUME_PREFIX}_{current_date}.pdf"
    dest = os.path.join(DEST_FOLDER, filename)

    if os.path.exists(dest):
        os.remove(dest)

    shutil.copy2(SOURCE_RESUME, dest)

    log_msg(f"Resume ready: {dest}")
    return os.path.abspath(dest)


# ==============================
# CHROME
# ==============================
def LoadNaukri():
    options = webdriver.ChromeOptions()

    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"--user-agent={USER_AGENT}")

    driver = webdriver.Chrome(
        service=ChromeService(),
        options=options
    )

    driver.execute_cdp_cmd("Network.enable", {})

    driver.execute_cdp_cmd(
        "Network.setExtraHTTPHeaders",
        {
            "headers": {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Cache-Control": "max-age=0",
                "Pragma": "no-cache",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1"
            }
        }
    )

    driver.implicitly_wait(5)

    driver.get(NAUKRI_LOGIN_URL)

    take_screenshot(driver, "01_page_loaded")

    return driver


# ==============================
# LOGIN SUCCESS
# ==============================
def login_success(driver):
    url = driver.current_url.lower()

    if "/mnjuser/homepage" in url:
        return True

    if "/mnjuser/profile" in url:
        return True

    return False


# ==============================
# LOGIN
# ==============================
def naukriLogin():
    driver = LoadNaukri()

    try:
        log_msg("Login started")

        wait = WebDriverWait(driver, 30)

        username = wait.until(
            EC.presence_of_element_located((By.ID, "usernameField"))
        )

        password = wait.until(
            EC.presence_of_element_located((By.ID, "passwordField"))
        )

        driver.execute_script(
            """
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', {bubbles:true}));
            arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
            """,
            username,
            EMAIL
        )

        driver.execute_script(
            """
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', {bubbles:true}));
            arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
            """,
            password,
            PASSWORD
        )

        take_screenshot(driver, "02_credentials_filled")

        # remove otp button
        driver.execute_script(
            """
            let otp = document.querySelector(
                'button.waves-effect.waves-light.btn-large.btn-block.btn-bold.otpButton.textTransform'
            );
            if (otp) {
                otp.remove();
            }
            """
        )

        log_msg("OTP button removed")

        time.sleep(2)

        login_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, LOGIN_BUTTON_XPATH))
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            login_btn
        )

        take_screenshot(driver, "03_before_login_click")

        driver.execute_script("arguments[0].click();", login_btn)

        log_msg("Login clicked")

        take_screenshot(driver, "04_after_login_click")

        log_msg("Waiting 10 seconds")
        time.sleep(10)

        take_screenshot(driver, "05_after_10_sec")

        if login_success(driver):
            log_msg("Login successful")
            return True, driver

        log_msg("Login failed")
        dump_html(driver, "login_failed")
        return False, driver

    except TimeoutException as e:
        log_msg(f"Timeout: {e}")
        dump_html(driver, "timeout")
        return False, driver

    except Exception as e:
        log_msg(f"Login error: {e}")
        dump_html(driver, "login_error")
        return False, driver


# ==============================
# UPLOAD RESUME
# ==============================
def UploadResume(driver, resume_path):
    driver.get(NAUKRI_PROFILE_URL)

    time.sleep(5)

    take_screenshot(driver, "06_profile_page")

    upload = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )

    upload.send_keys(resume_path)

    time.sleep(5)

    take_screenshot(driver, "07_resume_uploaded")

    log_msg("Resume uploaded")


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
            log_msg("Login unsuccessful")

    except Exception as e:
        catch(e)

    finally:
        tearDown(driver)

    log_msg("===== END =====")


if __name__ == "__main__":
    main()
