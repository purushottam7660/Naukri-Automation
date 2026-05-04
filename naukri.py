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


# ==========================================
# PATHS
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCE_RESUME = os.path.join(BASE_DIR, "Purushottam_Kumar_CV.pdf")
DEST_FOLDER = os.path.join(BASE_DIR, "Naukri_resume")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")
DUMP_DIR = os.path.join(BASE_DIR, "html_dump")
LOG_FILE = os.path.join(BASE_DIR, "naukri.log")

os.makedirs(DEST_FOLDER, exist_ok=True)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
os.makedirs(DUMP_DIR, exist_ok=True)


# ==========================================
# CONFIG
# ==========================================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

NAUKRI_LOGIN_URL = "https://www.naukri.com/nlogin/login"
NAUKRI_PROFILE_URL = "https://www.naukri.com/mnjuser/profile"

RESUME_PREFIX = "Purushottam_Kumar_Resume"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/147.0.0.0 Safari/537.36"
)

LOGIN_BUTTON_XPATH = (
    "//button[@class='waves-effect waves-light btn-large btn-block btn-bold blue-btn textTransform']"
)

OTP_BUTTON_XPATH = (
    "//button[@class='waves-effect waves-light btn-large btn-block btn-bold otpButton textTransform']"
)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s : %(message)s"
)


# ==========================================
# LOGGING
# ==========================================
def log_msg(message):
    print(message)
    logging.info(message)


def catch(error):
    _, _, exc_tb = sys.exc_info()
    line_no = str(exc_tb.tb_lineno)
    msg = "%s : %s at Line %s." % (type(error), error, line_no)
    print(msg)
    logging.error(msg)


# ==========================================
# DEBUG
# ==========================================
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
        log_msg(f"[HTML DUMP] {path}")
    except Exception as e:
        log_msg(f"HTML dump failed: {e}")


# ==========================================
# RESUME
# ==========================================
def generate_resume():
    current_date = datetime.now().strftime("%d_%b_%Y")
    new_filename = f"{RESUME_PREFIX}_{current_date}.pdf"

    destination_path = os.path.join(DEST_FOLDER, new_filename)

    if os.path.exists(destination_path):
        os.remove(destination_path)

    shutil.copy2(SOURCE_RESUME, destination_path)

    log_msg(f"Resume ready: {destination_path}")

    return os.path.abspath(destination_path)


# ==========================================
# CHROME
# ==========================================
def LoadNaukri():
    options = webdriver.ChromeOptions()

    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")

    # github actions friendly
    options.add_argument("--headless=new")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    options.add_argument(f"--user-agent={USER_AGENT}")

    driver = webdriver.Chrome(
        service=ChromeService(),
        options=options
    )

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });

                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4]
                });

                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """
        },
    )

    driver.implicitly_wait(5)
    driver.get(NAUKRI_LOGIN_URL)

    take_screenshot(driver, "01_login_page")

    return driver


# ==========================================
# LOGIN SUCCESS
# ==========================================
def login_success(driver):
    url = driver.current_url.lower()

    if "/mnjuser/homepage" in url:
        return True

    if "/mnjuser/profile" in url:
        return True

    return False


# ==========================================
# LOGIN
# ==========================================
def naukriLogin():
    driver = LoadNaukri()

    try:
        wait = WebDriverWait(driver, 30)

        log_msg("Waiting for login page...")

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

        # remove OTP button
        driver.execute_script("""
            const otp = document.evaluate(
                arguments[0],
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue;

            if (otp) {
                otp.remove();
            }
        """, OTP_BUTTON_XPATH)

        log_msg("OTP button removed")
        take_screenshot(driver, "03_otp_removed")

        time.sleep(2)

        login_btn = wait.until(
            EC.presence_of_element_located((By.XPATH, LOGIN_BUTTON_XPATH))
        )

        driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            login_btn
        )

        time.sleep(1)

        # click login
        driver.execute_script("arguments[0].click();", login_btn)

        log_msg("Login button clicked")

        take_screenshot(driver, "04_login_clicked")

        # mandatory 10 sec gap
        time.sleep(10)

        if NAUKRI_LOGIN_URL in driver.current_url:
            log_msg("Still on login page, submitting form")

            password.send_keys(Keys.ENTER)

            take_screenshot(driver, "05_enter_pressed")

            time.sleep(10)

        take_screenshot(driver, "06_after_login")

        if login_success(driver):
            log_msg("Login successful")
            return True, driver

        dump_html(driver, "login_failed")
        log_msg(f"Login failed. Current URL: {driver.current_url}")

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


# ==========================================
# RESUME UPLOAD
# ==========================================
def UploadResume(driver, resume_path):
    driver.get(NAUKRI_PROFILE_URL)

    time.sleep(5)

    take_screenshot(driver, "07_profile_page")

    upload_input = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )

    upload_input.send_keys(resume_path)

    time.sleep(5)

    take_screenshot(driver, "08_resume_uploaded")

    log_msg("Resume uploaded successfully")


# ==========================================
# TEARDOWN
# ==========================================
def tearDown(driver):
    if driver:
        try:
            driver.quit()
        except Exception:
            pass


# ==========================================
# MAIN
# ==========================================
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

    log_msg("===== END =====")


if __name__ == "__main__":
    main()
