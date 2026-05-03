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

LOGIN_BUTTON_XPATH = "//button[normalize-space()='Login']"

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
# HELPERS
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


def take_screenshot(driver, name):
    try:
        path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        driver.save_screenshot(path)
        log_msg(f"[SCREENSHOT] {path}")
    except Exception:
        pass


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

    driver.implicitly_wait(5)
    driver.get(NAUKRI_LOGIN_URL)

    take_screenshot(driver, "01_page_loaded")

    return driver


# ==============================
# OTP REMOVE
# ==============================
def remove_otp_buttons(driver):
    driver.execute_script(
        """
        const buttons = Array.from(document.querySelectorAll("button"));
        buttons.forEach(btn => {
            const txt = (btn.innerText || "").trim().toLowerCase();
            if (txt.includes("otp")) {
                btn.remove();
            }
        });
        """
    )


# ==============================
# LOGIN BUTTON
# ==============================
def get_real_login_button(driver):
    buttons = driver.find_elements(By.TAG_NAME, "button")

    for btn in buttons:
        try:
            text = btn.text.strip().lower()

            if (
                text == "login"
                and btn.is_displayed()
                and btn.is_enabled()
            ):
                return btn
        except Exception:
            pass

    return None


# ==============================
# LOGIN CHECK
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
        wait = WebDriverWait(driver, 30)

        username = wait.until(
            EC.presence_of_element_located((By.ID, "usernameField"))
        )

        password = wait.until(
            EC.presence_of_element_located((By.ID, "passwordField"))
        )

        username.clear()
        username.send_keys(EMAIL)

        password.clear()
        password.send_keys(PASSWORD)

        take_screenshot(driver, "02_credentials_filled")

        remove_otp_buttons(driver)

        time.sleep(2)

        remove_otp_buttons(driver)

        take_screenshot(driver, "03_otp_removed")

        login_btn = get_real_login_button(driver)

        if not login_btn:
            raise Exception("Login button not found")

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            login_btn
        )

        time.sleep(1)

        take_screenshot(driver, "04_before_login_click")

        driver.execute_script("arguments[0].click();", login_btn)

        log_msg("Login clicked")

        take_screenshot(driver, "05_after_login_click")

        time.sleep(10)

        take_screenshot(driver, "06_after_10_sec")

        if login_success(driver):
            log_msg("Login successful")
            return True, driver

        dump_html(driver, "login_failed")
        log_msg("Login failed")
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
# UPLOAD
# ==============================
def UploadResume(driver, resume_path):
    driver.get(NAUKRI_PROFILE_URL)

    time.sleep(5)

    take_screenshot(driver, "07_profile_page")

    upload = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )

    upload.send_keys(resume_path)

    time.sleep(5)

    take_screenshot(driver, "08_resume_uploaded")

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
        log_msg("Missing credentials")
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

    except Exception as e:
        catch(e)

    finally:
        tearDown(driver)

    log_msg("===== END =====")


if __name__ == "__main__":
    main()
