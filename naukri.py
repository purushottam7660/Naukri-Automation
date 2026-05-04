import logging
import logging.config
import os
import sys
import time
import shutil
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# =========================================================
# SAFE LOGGING SETUP
# =========================================================
if os.path.exists("logging_config.ini"):
    logging.config.fileConfig("logging_config.ini")
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s : %(levelname)s : %(message)s"
    )

logger = logging.getLogger()


# =========================================================
# ENV (GITHUB SECRETS)
# =========================================================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")


# =========================================================
# PATHS
# =========================================================
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

SOURCE_RESUME = os.path.join(ROOT_DIR, "Purushottam_Kumar_CV.pdf")
DEST_FOLDER = os.path.join(ROOT_DIR, "Naukri_resume")
SCREENSHOT_DIR = os.path.join(ROOT_DIR, "screenshots")

os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# =========================================================
# SCREENSHOT HELPER
# =========================================================
def take_screenshot(driver, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    logger.info(f"[SCREENSHOT] {path}")


# =========================================================
# RESUME GENERATION
# =========================================================
def generate_resume():
    current_date = datetime.now().strftime("%d_%b_%Y")
    new_filename = f"Purushottam_Kumar_Resume_{current_date}.pdf"

    os.makedirs(DEST_FOLDER, exist_ok=True)

    destination_path = os.path.join(DEST_FOLDER, new_filename)

    if os.path.exists(destination_path):
        os.remove(destination_path)

    shutil.copy2(SOURCE_RESUME, destination_path)

    logger.info(f"Resume ready: {destination_path}")

    return os.path.abspath(destination_path)


# =========================================================
# MAIN CLASS
# =========================================================
class NaukriBot:

    def __init__(self, username, password):

        self.username = username
        self.password = password

        self.login_url = "https://www.naukri.com/nlogin/login"
        self.profile_url = "https://www.naukri.com/mnjuser/profile"

        self.driver = self._init_driver()

        self.driver.maximize_window()
        self.driver.get(self.login_url)

        take_screenshot(self.driver, "01_login_page")

        logger.info("Login page opened")

    # -----------------------------------------------------
    # DRIVER INIT
    # -----------------------------------------------------
    def _init_driver(self):

        options = webdriver.ChromeOptions()

        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--headless=new")

        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        )

        return webdriver.Chrome(options=options)

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------
    def login(self):

        if not self.username or not self.password:
            raise Exception("Missing NAUKRI_EMAIL or NAUKRI_PASSWORD")

        wait = WebDriverWait(self.driver, 30)

        try:
            logger.info("Logging in...")

            email = wait.until(
                EC.presence_of_element_located((By.ID, "usernameField"))
            )
            email.send_keys(self.username)
            take_screenshot(self.driver, "02_email_filled")

            password = wait.until(
                EC.presence_of_element_located((By.ID, "passwordField"))
            )
            password.send_keys(self.password)
            take_screenshot(self.driver, "03_password_filled")

            password.send_keys(Keys.ENTER)

            time.sleep(10)

            take_screenshot(self.driver, "04_after_login")

            if "homepage" in self.driver.current_url or "profile" in self.driver.current_url:
                logger.info("Login successful")
                return True

            logger.error("Login failed")
            return False

        except Exception as e:
            logger.exception(f"Login error: {e}")
            take_screenshot(self.driver, "login_error")
            return False

    # -----------------------------------------------------
    # RESUME UPLOAD
    # -----------------------------------------------------
    def upload_resume(self, resume_path):

        try:
            self.driver.get(self.profile_url)
            time.sleep(5)

            take_screenshot(self.driver, "05_profile_page")

            upload = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
            )

            upload.send_keys(resume_path)

            time.sleep(5)

            take_screenshot(self.driver, "06_resume_uploaded")

            logger.info("Resume uploaded successfully")

        except Exception as e:
            logger.exception(f"Resume upload failed: {e}")
            take_screenshot(self.driver, "upload_error")

    # -----------------------------------------------------
    # CLOSE
    # -----------------------------------------------------
    def close(self):
        try:
            self.driver.quit()
        except:
            pass


# =========================================================
# MAIN
# =========================================================
def main():

    try:
        resume_path = generate_resume()

        bot = NaukriBot(EMAIL, PASSWORD)

        status = bot.login()

        if status:
            bot.upload_resume(resume_path)
        else:
            logger.error("Login failed, skipping upload")

    except Exception as e:
        logger.error(
            f"Error at line {sys.exc_info()[-1].tb_lineno} "
            f"{type(e).__name__}: {e}"
        )

    finally:
        time.sleep(5)
        try:
            bot.close()
        except:
            pass


# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":
    print("Starting Naukri automation...")
    main()
