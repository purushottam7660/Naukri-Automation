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
    "Chrome/147.0.0.0 Safari/537.36"
)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s : %(message)s"
)


# =========================================================
# LOGGING
# =========================================================
def log(msg):
    print(msg)
    logging.info(msg)


def catch(err):
    _, _, tb = sys.exc_info()
    line = tb.tb_lineno if tb else "?"
    log(f"{type(err).__name__}: {err} at line {line}")


# =========================================================
# SCREENSHOT
# =========================================================
def screenshot(driver, name):
    try:
        path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        driver.save_screenshot(path)
        log(f"[SCREENSHOT] {path}")
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
        log(f"[HTML] {path}")
    except Exception:
        pass


# =========================================================
# RESUME
# =========================================================
def generate_resume():
    today = datetime.now().strftime("%d_%b_%Y")
    filename = f"{RESUME_PREFIX}_{today}.pdf"
    dest = os.path.join(DEST_FOLDER, filename)

    if os.path.exists(dest):
        os.remove(dest)

    shutil.copy2(SOURCE_RESUME, dest)
    log(f"Resume ready: {dest}")

    return os.path.abspath(dest)


# =========================================================
# CHROME
# =========================================================
def load_driver():
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

    screenshot(driver, "01_login_page")

    return driver


# =========================================================
# FIND REAL LOGIN BUTTON
# =========================================================
def get_real_login_button(driver):
    form = driver.find_element(By.ID, "loginForm")

    buttons = form.find_elements(By.TAG_NAME, "button")

    for btn in buttons:
        try:
            text = btn.text.strip().lower()

            if (
                text == "login"
                and "otp" not in text
                and btn.is_displayed()
                and btn.is_enabled()
            ):
                return btn

        except Exception:
            pass

    return None


# =========================================================
# CHECK LOGIN
# =========================================================
def login_success(driver):
    url = driver.current_url.lower()

    log(f"Current URL: {url}")

    if "/mnjuser/" in url:
        return True

    return False


# =========================================================
# LOGIN
# =========================================================
def naukri_login():
    driver = load_driver()

    try:
        wait = WebDriverWait(driver, 25)

        email = wait.until(
            EC.visibility_of_element_located((By.ID, "usernameField"))
        )

        password = wait.until(
            EC.visibility_of_element_located((By.ID, "passwordField"))
        )

        email.clear()
        email.send_keys(EMAIL)

        password.clear()
        password.send_keys(PASSWORD)

        screenshot(driver, "02_credentials_filled")

        time.sleep(2)

        login_btn = get_real_login_button(driver)

        if not login_btn:
            screenshot(driver, "03_login_button_missing")
            dump_html(driver, "login_button_missing")
            raise Exception("Real login button not found")

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            login_btn
        )

        time.sleep(1)

        screenshot(driver, "04_before_click")

        driver.execute_script("arguments[0].click();", login_btn)

        log("Clicked real Login button")

        screenshot(driver, "05_after_click")

        time.sleep(12)

        if login_success(driver):
            log("Login successful")
            return True, driver

        if "login" in driver.current_url.lower():
            log("Still on login page")
            screenshot(driver, "06_still_login_page")
            dump_html(driver, "still_login_page")

        return False, driver

    except Exception as e:
        catch(e)
        screenshot(driver, "login_exception")
        dump_html(driver, "login_exception")
        return False, driver


# =========================================================
# UPLOAD RESUME
# =========================================================
def upload_resume(driver, resume_path):
    driver.get(NAUKRI_PROFILE_URL)

    wait = WebDriverWait(driver, 30)

    upload = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@type='file']")
        )
    )

    upload.send_keys(resume_path)

    time.sleep(6)

    screenshot(driver, "resume_uploaded")

    log("Resume uploaded successfully")


# =========================================================
# CLOSE
# =========================================================
def teardown(driver):
    if driver:
        try:
            driver.quit()
        except Exception:
            pass


# =========================================================
# MAIN
# =========================================================
def main():
    log("===== START =====")

    if not EMAIL or not PASSWORD:
        log("Missing NAUKRI_EMAIL or NAUKRI_PASSWORD")
        sys.exit(1)

    if not os.path.exists(SOURCE_RESUME):
        log(f"Resume missing: {SOURCE_RESUME}")
        sys.exit(1)

    driver = None

    try:
        resume_path = generate_resume()

        status, driver = naukri_login()

        if status:
            upload_resume(driver, resume_path)
        else:
            log("Login failed")

    except Exception as e:
        catch(e)

    finally:
        teardown(driver)

    log("===== END =====")


if __name__ == "__main__":
    main()
