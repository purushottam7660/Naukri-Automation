import os
import time
import logging
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================
# CONFIG
# =========================
EMAIL = os.getenv("NAUKRI_EMAIL", "your_email_here")
PASSWORD = os.getenv("NAUKRI_PASSWORD", "your_password_here")

BASE_URL = "https://www.naukri.com/nlogin/login"
SUCCESS_URL = "https://www.naukri.com/mnjuser/"

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# =========================
# SAFE SCREENSHOT (IMPORTANT FIX)
# =========================
def save_screenshot(driver, step):
    try:
        if driver is None:
            return

        filename = f"{step}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(SCREENSHOT_DIR, filename)

        driver.save_screenshot(path)
        logging.info(f"[SCREENSHOT] {path}")

    except Exception as e:
        logging.warning(f"Screenshot failed at {step}: {e}")


# =========================
# DRIVER
# =========================
def get_driver():
    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--remote-debugging-port=9222")

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)

    return driver


# =========================
# HUMAN TYPING
# =========================
def human_type(element, text):
    for c in text:
        element.send_keys(c)
        time.sleep(0.05)


# =========================
# LOGIN WITH FULL SCREENSHOT TRACE
# =========================
def login_until_success(driver, max_attempts=3):
    wait = WebDriverWait(driver, 25)

    login_buttons = [
        "//button[normalize-space()='Login']",
        "//button[contains(.,'Login')]",
        "//a[contains(.,'Login')]"
    ]

    for attempt in range(1, max_attempts + 1):

        logging.info(f"===== ATTEMPT {attempt} =====")

        try:
            # STEP 1 - OPEN PAGE
            driver.get(BASE_URL)
            time.sleep(4)
            save_screenshot(driver, f"attempt_{attempt}_01_open_page")

            # STEP 2 - EMAIL
            email_box = wait.until(
                EC.presence_of_element_located((By.ID, "usernameField"))
            )
            email_box.clear()
            human_type(email_box, EMAIL)
            save_screenshot(driver, f"attempt_{attempt}_02_email_filled")

            # STEP 3 - PASSWORD
            password_box = driver.find_element(By.ID, "passwordField")
            password_box.clear()
            human_type(password_box, PASSWORD)
            save_screenshot(driver, f"attempt_{attempt}_03_password_filled")

            # STEP 4 - CLICK LOGIN
            clicked = False

            for xp in login_buttons:
                try:
                    btn = wait.until(
                        EC.element_to_be_clickable((By.XPATH, xp))
                    )
                    btn.click()
                    clicked = True
                    logging.info(f"Clicked login using {xp}")
                    break
                except:
                    continue

            if not clicked:
                raise Exception("Login button not found")

            save_screenshot(driver, f"attempt_{attempt}_04_login_clicked")

            # STEP 5 - WAIT REDIRECT
            time.sleep(8)
            save_screenshot(driver, f"attempt_{attempt}_05_after_wait")

            current_url = driver.current_url
            logging.info(f"Current URL: {current_url}")

            # STEP 6 - SUCCESS CHECK
            if SUCCESS_URL in current_url:
                save_screenshot(driver, f"attempt_{attempt}_SUCCESS")
                logging.info("LOGIN SUCCESS 🎉")
                return True

            logging.warning("Login failed → retrying...")

        except Exception as e:
            logging.error(f"Attempt {attempt} failed: {e}")
            save_screenshot(driver, f"attempt_{attempt}_ERROR")
            time.sleep(3)

    logging.error("LOGIN FAILED after all attempts")
    return False


# =========================
# MAIN
# =========================
def main():
    logging.info("===== START =====")

    driver = get_driver()

    try:
        success = login_until_success(driver, max_attempts=5)

        if success:
            logging.info("Automation continues after login")
        else:
            logging.error("Stopping due to login failure")

    except Exception as e:
        logging.error(f"Fatal error: {e}")
        save_screenshot(driver, "fatal_error")

    finally:
        try:
            save_screenshot(driver, "final_exit")
        except:
            pass

        try:
            driver.quit()
        except:
            pass

        logging.info("Driver closed safely")


if __name__ == "__main__":
    main()
