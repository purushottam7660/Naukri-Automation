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
# PATHS
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

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s : %(message)s"
)


# =========================================================
# LOGGING
# =========================================================
def log_msg(message):
    print(message)
    logging.info(message)


def catch(error):
    _, _, exc_tb = sys.exc_info()
    line_no = exc_tb.tb_lineno if exc_tb else "?"
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
    filename = f"{RESUME_PREFIX}_{current_date}.pdf"
    destination = os.path.join(DEST_FOLDER, filename)

    if os.path.exists(destination):
        os.remove(destination)

    shutil.copy2(SOURCE_RESUME, destination)

    log_msg(f"Resume ready: {destination}")
    return os.path.abspath(destination)


# =========================================================
# CHROME
# =========================================================
def LoadNaukri():
    options = webdriver.ChromeOptions()

    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
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

    driver = webdriver.Chrome(
        service=ChromeService(),
        options=options
    )

    driver.implicitly_wait(5)

    driver.get(NAUKRI_LOGIN_URL)

    take_screenshot(driver, "01_page_loaded")

    return driver


# =========================================================
# LOGIN SUCCESS
# =========================================================
def login_success(driver):
    url = driver.current_url.lower()

    if "/mnjuser/homepage" in url:
        return True

    if "/mnjuser/profile" in url:
        return True

    if "/mnjuser" in url:
        return True

    return False


# =========================================================
# LOGIN BUTTON
# IMPORTANT:
# Select ONLY the password login button
# NOT the "Use OTP to Login" button
# =========================================================
def find_login_button(driver):
    xpath = (
        "//form[@id='loginForm']"
        "//button[normalize-space()='Login' and not(contains(@class,'otpButton'))]"
    )

    buttons = driver.find_elements(By.XPATH, xpath)

    for btn in buttons:
        try:
            if btn.is_displayed() and btn.is_enabled():
                return btn
        except Exception:
            pass

    return None


# =========================================================
# LOGIN
# =========================================================
def naukriLogin():
    driver = LoadNaukri()

    try:
        log_msg("Login started")

        wait = WebDriverWait(driver, 25)

        email = wait.until(
            EC.visibility_of_element_located((By.ID, "usernameField"))
        )

        password = wait.until(
            EC.visibility_of_element_located((By.ID, "passwordField"))
        )

        email.clear()
        email.send_keys(EMAIL)
        take_screenshot(driver, "02_email_filled")

        password.clear()
        password.send_keys(PASSWORD)
        take_screenshot(driver, "03_password_filled")

        time.sleep(2)

        login_btn = find_login_button(driver)

        if not login_btn:
            log_msg("Login button not found")
            take_screenshot(driver, "04_login_button_not_found")
            dump_html(driver, "login_button_not_found")
            return False, driver

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            login_btn
        )

        time.sleep(1)

        try:
            wait.until(lambda d: login_btn.is_displayed() and login_btn.is_enabled())
            login_btn.click()
            log_msg("Login button clicked")
        except Exception:
            driver.execute_script("arguments[0].click();", login_btn)
            log_msg("JS click used")

        take_screenshot(driver, "05_login_clicked")

        time.sleep(12)

        if NAUKRI_LOGIN_URL in driver.current_url:
            log_msg("Still on login page. Trying ENTER.")
            password.send_keys(Keys.ENTER)
            take_screenshot(driver, "06_enter_pressed")
            time.sleep(10)

        take_screenshot(driver, "07_after_login")

        if login_success(driver):
            log_msg("Login successful")
            return True, driver

        take_screenshot(driver, "08_login_failed")
        dump_html(driver, "login_failed")

        log_msg("Login failed")
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
    log_msg("Opening profile page")

    driver.get(NAUKRI_PROFILE_URL)

    wait = WebDriverWait(driver, 30)

    upload_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@type='file']")
        )
    )

    take_screenshot(driver, "09_profile_loaded")

    upload_input.send_keys(resume_path)

    time.sleep(8)

    take_screenshot(driver, "10_resume_uploaded")

    log_msg("Resume uploaded successfully")


# =========================================================
# TEARDOWN
# =========================================================
def tearDown(driver):
    if driver is None:
        return

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
        log_msg(f"Resume not found: {SOURCE_RESUME}")
        raise SystemExit(1)

    driver = None

    try:
        resume_path = generate_resume()

        status, driver = naukriLogin()

        if status:
            UploadResume(driver, resume_path)
        else:
            log_msg("Login failed. Upload skipped.")

    except Exception as e:
        catch(e)

    finally:
        tearDown(driver)

    log_msg("===== END =====")


if __name__ == "__main__":
    main()
