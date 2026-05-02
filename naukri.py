#! python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import shutil
import logging
from datetime import datetime

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from cookies import NAUKRI_COOKIES


# ==============================
# USER CONFIGURATION
# ==============================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

SOURCE_RESUME = "Purushottam_Kumar_CV.pdf"
DEST_FOLDER = "Naukri_resume"
RESUME_PREFIX = "Purushottam_Kumar_Resume"

NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
NAUKRI_PROFILE_URL = "https://www.naukri.com/mnjuser/profile"

SCREENSHOT_DIR = "screenshots"
MAX_LOGIN_ATTEMPTS = 6

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    filename="naukri.log",
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
    os.makedirs(DEST_FOLDER, exist_ok=True)

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

    options.add_argument("--incognito")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popups")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    )

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
# COOKIE LOGIN
# ==============================
def apply_login_cookies(driver):
    try:
        log_msg("Trying login using cookies")

        driver.get("https://www.naukri.com")
        time.sleep(3)

        for name, value in NAUKRI_COOKIES.items():
            try:
                driver.add_cookie({
                    "name": name,
                    "value": value,
                    "domain": ".naukri.com",
                    "path": "/"
                })
                log_msg(f"cookie added: {name}")
            except Exception as e:
                log_msg(f"cookie failed: {name} -> {e}")

        driver.get("https://www.naukri.com/mnjuser/homepage")

        time.sleep(5)

        take_screenshot(driver, "cookie_login_result")

        log_msg(f"After cookie URL: {driver.current_url}")

        if "homepage" in driver.current_url.lower():
            log_msg("Cookie login successful")
            return True

    except Exception as e:
        log_msg(f"Cookie login failed: {e}")

    return False


# ==============================
# LOGIN HELPERS
# ==============================
LOGIN_BUTTON_XPATH = (
    "//button[contains(@class,'blue-btn') and normalize-space()='Login']"
)


def find_login_button(driver):
    buttons = driver.find_elements(By.XPATH, LOGIN_BUTTON_XPATH)

    for btn in buttons:
        if btn.is_displayed() and btn.is_enabled():
            return btn

    return None


def print_button_info(button):
    try:
        print("\n========== BUTTON DEBUG ==========")
        print("Selector:", LOGIN_BUTTON_XPATH)
        print("Text:", button.text)
        print("HTML:")
        print(button.get_attribute("outerHTML"))
        print("==================================\n")
    except Exception:
        pass


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

    if apply_login_cookies(driver):
        return True, driver

    for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
        log_msg(f"Login attempt {attempt}")

        try:
            driver.get(NAUKRI_LOGIN_URL)

            time.sleep(4)

            take_screenshot(driver, f"attempt_{attempt}_login_page")

            email = driver.find_element(By.ID, "usernameField")
            password = driver.find_element(By.ID, "passwordField")

            email.clear()
            email.send_keys(EMAIL)

            take_screenshot(driver, f"attempt_{attempt}_email")

            password.clear()
            password.send_keys(PASSWORD)

            take_screenshot(driver, f"attempt_{attempt}_password")

            time.sleep(2)

            login_btn = find_login_button(driver)

            if not login_btn:
                raise Exception("Login button not found")

            print_button_info(login_btn)

            driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                login_btn
            )

            time.sleep(1)

            login_btn.click()

            take_screenshot(driver, f"attempt_{attempt}_clicked")

            time.sleep(8)

            log_msg(f"Current URL: {driver.current_url}")

            if login_success(driver):
                log_msg("Login successful")
                return True, driver

            log_msg("Login not completed, retrying...")

        except (
            TimeoutException,
            StaleElementReferenceException
        ) as e:
            log_msg(f"Attempt timeout: {e}")
            take_screenshot(driver, f"attempt_{attempt}_timeout")

        except Exception as e:
            log_msg(f"Attempt failed: {e}")
            take_screenshot(driver, f"attempt_{attempt}_error")

        time.sleep(4)

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

    driver = None

    try:
        resume_path = generate_resume()

        status, driver = naukriLogin()

        if status:
            UploadResume(driver, resume_path)
        else:
            log_msg("Login failed after all retries")

    except Exception as e:
        catch(e)

    finally:
        tearDown(driver)

    log_msg("===== Process Completed =====")


if __name__ == "__main__":
    main()
