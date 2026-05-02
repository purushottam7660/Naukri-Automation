#! python3
# -*- coding: utf-8 -*-
"""Naukri Daily update - Using Chrome"""

import io
import logging
import os
import sys
import time
import shutil
from datetime import datetime
from random import choice, randint
from string import ascii_uppercase, digits

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait


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

updatePDF = False
headless = True

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    filename="naukri.log",
    format="%(asctime)s    : %(message)s",
)


# ==============================
# LOGGING
# ==============================
def log_msg(message):
    print(message)
    logging.info(message)


def catch(error):
    _, _, exc_tb = sys.exc_info()
    lineNo = str(exc_tb.tb_lineno)
    msg = "%s : %s at Line %s." % (type(error), error, lineNo)
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


def sleep_with_screenshot(driver, seconds, prefix):
    take_screenshot(driver, f"{prefix}_before_wait")
    time.sleep(seconds)
    take_screenshot(driver, f"{prefix}_after_wait")


# ==============================
# RESUME GENERATOR
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
# SELENIUM HELPERS
# ==============================
def is_element_present(driver, how, what):
    try:
        driver.find_element(by=how, value=what)
    except NoSuchElementException:
        return False
    return True


def randomText():
    return "".join(choice(ascii_uppercase + digits) for _ in range(randint(1, 5)))


# ==============================
# CHROME
# ==============================
def LoadNaukri(headless):
    options = webdriver.ChromeOptions()

    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popups")
    options.add_argument("--disable-gpu")
    options.add_argument("--incognito")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")

    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.7778.97 Safari/537.36"
    )

    proxy = os.getenv("HTTP_PROXY")
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
        log_msg(f"Using custom proxy: {proxy}")
    else:
        log_msg("Using default network route")

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(
        options=options,
        service=ChromeService()
    )

    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        },
    )

    driver.implicitly_wait(5)

    log_msg("Google Chrome Launched!")

    driver.get(NAUKRI_LOGIN_URL)

    return driver


# ==============================
# LOGIN HELPERS
# ==============================
def find_login_fields(driver):
    wait = WebDriverWait(driver, 25)

    wait.until(
        lambda d: (
            len(d.find_elements(By.ID, "usernameField")) > 0
            or len(d.find_elements(By.XPATH, "//input[@type='email']")) > 0
        )
    )

    email_field = None
    password_field = None

    email_candidates = [
        (By.ID, "usernameField"),
        (By.XPATH, "//input[@type='email']")
    ]

    password_candidates = [
        (By.ID, "passwordField"),
        (By.XPATH, "//input[@type='password']")
    ]

    for by, value in email_candidates:
        els = driver.find_elements(by, value)
        if els:
            email_field = els[0]
            break

    for by, value in password_candidates:
        els = driver.find_elements(by, value)
        if els:
            password_field = els[0]
            break

    return email_field, password_field


def find_login_button(driver):
    candidates = [
        "//button[contains(@class,'blue-btn') and normalize-space()='Login']",
        "//button[normalize-space()='Login']",
        "//button[contains(.,'Login') and not(contains(.,'OTP'))]"
    ]

    for xpath in candidates:
        try:
            buttons = driver.find_elements(By.XPATH, xpath)
            for btn in buttons:
                if btn.is_displayed() and btn.is_enabled():
                    return btn
        except Exception:
            continue

    return None


def click_login(driver, btn, attempt):
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        btn
    )

    take_screenshot(driver, f"attempt_{attempt}_login_button_found")

    time.sleep(1)

    if attempt == 1:
        btn.click()

    elif attempt == 2:
        driver.execute_script("arguments[0].click();", btn)

    elif attempt == 3:
        driver.execute_script(
            """
            var btn = arguments[0];
            btn.dispatchEvent(new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window
            }));
            """,
            btn
        )

    elif attempt == 4:
        btn.send_keys(Keys.ENTER)

    elif attempt == 5:
        driver.execute_script(
            """
            arguments[0].focus();
            arguments[0].click();
            """,
            btn
        )

    else:
        driver.execute_script("arguments[0].click();", btn)

    take_screenshot(driver, f"attempt_{attempt}_login_clicked")


def login_success(driver):
    time.sleep(3)

    url = driver.current_url.lower()

    if "profile" in url:
        return True

    if "mnjuser" in url:
        return True

    if "login" not in url:
        return True

    return False


# ==============================
# LOGIN
# ==============================
def naukriLogin(headless=False):
    status = False
    driver = None

    try:
        driver = LoadNaukri(headless)

        for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
            log_msg(f"Login attempt {attempt}")

            driver.get(NAUKRI_LOGIN_URL)

            sleep_with_screenshot(
                driver,
                5,
                f"attempt_{attempt}_page_load"
            )

            try:
                email_field, password_field = find_login_fields(driver)

                if not email_field or not password_field:
                    raise Exception("Login fields not found")

                email_field.clear()
                email_field.send_keys(EMAIL)

                take_screenshot(driver, f"attempt_{attempt}_email_entered")

                password_field.clear()
                password_field.send_keys(PASSWORD)

                take_screenshot(driver, f"attempt_{attempt}_password_entered")

                sleep_with_screenshot(
                    driver,
                    2,
                    f"attempt_{attempt}_before_click"
                )

                login_btn = find_login_button(driver)

                if not login_btn:
                    raise Exception("Login button not found")

                click_login(driver, login_btn, attempt)

                sleep_with_screenshot(
                    driver,
                    10,
                    f"attempt_{attempt}_after_click"
                )

                log_msg(f"Current URL: {driver.current_url}")

                if login_success(driver):
                    log_msg("Naukri Login Successful")
                    status = True
                    return status, driver

                log_msg("Login not completed, retrying...")

            except (
                TimeoutException,
                StaleElementReferenceException
            ) as e:
                take_screenshot(driver, f"attempt_{attempt}_timeout")
                log_msg(f"Attempt timeout: {e}")

            except Exception as e:
                take_screenshot(driver, f"attempt_{attempt}_error")
                log_msg(f"Attempt failed: {e}")

            sleep_with_screenshot(
                driver,
                4,
                f"attempt_{attempt}_retry_wait"
            )

    except Exception as e:
        catch(e)

    return status, driver


# ==============================
# UPDATE RESUME
# ==============================
def UpdateResume():
    try:
        txt = randomText()
        xloc = randint(700, 1000)
        fsize = randint(1, 10)

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        can.setFont("Helvetica", fsize)
        can.drawString(xloc, 100, txt)
        can.save()

        packet.seek(0)
        new_pdf = PdfReader(packet)

        with open(SOURCE_RESUME, "rb") as f:
            existing_pdf = PdfReader(f)
            pagecount = len(existing_pdf.pages)

            output = PdfWriter()

            for pageNum in range(pagecount - 1):
                output.add_page(existing_pdf.pages[pageNum])

            page = existing_pdf.pages[pagecount - 1]
            page.merge_page(new_pdf.pages[0])
            output.add_page(page)

            temp_path = os.path.join(DEST_FOLDER, "temp_resume.pdf")

            with open(temp_path, "wb") as outputStream:
                output.write(outputStream)

            return os.path.abspath(temp_path)

    except Exception as e:
        catch(e)

    return os.path.abspath(SOURCE_RESUME)


# ==============================
# UPLOAD RESUME
# ==============================
def UploadResume(driver, resumePath):
    try:
        driver.get(NAUKRI_PROFILE_URL)

        sleep_with_screenshot(driver, 4, "profile_page_load")

        wait = WebDriverWait(driver, 30)

        upload_input = wait.until(
            lambda d: d.find_element(By.XPATH, "//input[@type='file']")
        )

        take_screenshot(driver, "upload_input_found")

        upload_input.send_keys(os.path.abspath(resumePath))

        sleep_with_screenshot(driver, 4, "after_resume_upload")

        take_screenshot(driver, "resume_uploaded")

        log_msg("Resume uploaded successfully")

    except Exception as e:
        catch(e)


# ==============================
# LOGOUT
# ==============================
def Logout(driver):
    try:
        driver.delete_all_cookies()
    except Exception:
        pass


# ==============================
# TEARDOWN
# ==============================
def tearDown(driver):
    if driver is None:
        return

    try:
        driver.close()
    except Exception:
        pass

    try:
        driver.quit()
    except Exception:
        pass


# ==============================
# MAIN
# ==============================
def main():
    log_msg("-----Naukri.py Script Run Begin-----")

    driver = None

    try:
        if not EMAIL or not PASSWORD:
            log_msg("Missing NAUKRI_EMAIL or NAUKRI_PASSWORD")
            raise SystemExit(1)

        resume_path = generate_resume()

        status, driver = naukriLogin(headless)

        if status:
            if updatePDF:
                resume_path = UpdateResume()

            UploadResume(driver, resume_path)

    except Exception as e:
        catch(e)

    finally:
        if driver is not None:
            try:
                Logout(driver)
            except Exception:
                pass

        tearDown(driver)

    log_msg("-----Naukri.py Script Run Ended-----\n")


if __name__ == "__main__":
    main()
