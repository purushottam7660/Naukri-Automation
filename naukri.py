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


# ==============================
# BASE PATHS
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCE_RESUME = os.path.join(BASE_DIR, "Purushottam_Kumar_CV.pdf")
DEST_FOLDER = os.path.join(BASE_DIR, "Naukri_resume")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
LOG_FILE = os.path.join(BASE_DIR, "naukri.log")

os.makedirs(DEST_FOLDER, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# ==============================
# USER CONFIGURATION
# ==============================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

RESUME_PREFIX = "Purushottam_Kumar_Resume"

NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
NAUKRI_PROFILE_URL = "https://www.naukri.com/mnjuser/profile"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0"
)

LOGIN_BUTTON_XPATH = (
    "//button[normalize-space()='Login' or .//*[normalize-space()='Login']]"
)


logging.basicConfig(
    level=logging.INFO,
    filename=LOG_FILE,
    format="%(asctime)s : %(message)s",
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
# CHROME
# ==============================
def LoadNaukri():
    options = webdriver.ChromeOptions()

    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popups")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    # useful for GitHub Actions / Linux
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    options.add_argument(f"--user-agent={USER_AGENT}")

    proxy = os.getenv("HTTP_PROXY")
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

    return driver


# ==============================
# LOGIN HELPERS
# ==============================
def find_login_button(driver):
    buttons = driver.find_elements(By.XPATH, LOGIN_BUTTON_XPATH)

    for btn in buttons:
        try:
            text = btn.text.strip().lower()

            if (
                btn.is_displayed()
                and btn.is_enabled()
                and text == "login"
            ):
                return btn

        except Exception:
            pass

    return None


def login_success(driver):
    time.sleep(5)

    url = driver.current_url.lower()
    log_msg(f"Current URL after login: {url}")

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

        time.sleep(4)
        take_screenshot(driver, "login_page")

        email = driver.find_element(By.ID, "usernameField")
        password = driver.find_element(By.ID, "passwordField")

        email.clear()
        email.send_keys(EMAIL)

        password.clear()
        password.send_keys(PASSWORD)

        take_screenshot(driver, "credentials_filled")

        time.sleep(2)

        login_btn = find_login_button(driver)

        if login_btn:
            log_msg("Login button found")

            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    login_btn
                )
                time.sleep(1)

                driver.execute_script(
                    "arguments[0].click();",
                    login_btn
                )

                log_msg("Clicked Login button")

            except Exception as e:
                log_msg(f"Login button click failed: {e}")
                log_msg("Trying Enter key")
                password.send_keys(Keys.ENTER)

        else:
            log_msg("Login button not found, using Enter key")
            password.send_keys(Keys.ENTER)

        take_screenshot(driver, "after_login_action")

        time.sleep(8)

        if login_success(driver):
            log_msg("Login successful")
            return True, driver

        log_msg("Login failed")
        return False, driver

    except TimeoutException as e:
        log_msg(f"Login timeout: {e}")
        take_screenshot(driver, "login_timeout")
        return False, driver

    except Exception as e:
        log_msg(f"Login error: {e}")
        take_screenshot(driver, "login_error")
        return False, driver


# ==============================
# UPLOAD RESUME
# ==============================
def UploadResume(driver, resume_path):
    driver.get(NAUKRI_PROFILE_URL)

    time.sleep(5)
    take_screenshot(driver, "profile_page")

    upload_input = WebDriverWait(driver, 30).until(
        lambda d: d.find_element(By.XPATH, "//input[@type='file']")
    )

    upload_input.send_keys(resume_path)

    time.sleep(5)
    take_screenshot(driver, "resume_uploaded")

    log_msg("Resume uploaded successfully")


# ==============================
# TEARDOWN
# ==============================
def tearDown(driver):
    if driver is None:
        return

    try:
        driver.quit()
    except Exception:
        pass


# ==============================
# MAIN
# ==============================
def main():
    log_msg("===== Naukri Automation Started =====")

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

    log_msg("===== Process Completed =====")


if __name__ == "__main__":
    main()
