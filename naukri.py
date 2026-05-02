import os
import shutil
import time
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


# ==============================
# USER CONFIGURATION
# ==============================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")

SOURCE_RESUME = "Purushottam_Kumar_CV.pdf"
DEST_FOLDER = "Naukri_resume"
RESUME_PREFIX = "Purushottam_Kumar_Resume"

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

MAX_LOGIN_ATTEMPTS = 5


# ==============================
# FUNCTION: SCREENSHOT
# ==============================
def take_screenshot(driver, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    print(f"[SCREENSHOT] {path}")


# ==============================
# FUNCTION: WAIT WITH SCREENSHOT
# ==============================
def sleep_with_screenshot(driver, seconds, prefix):
    take_screenshot(driver, f"{prefix}_before_wait")
    time.sleep(seconds)
    take_screenshot(driver, f"{prefix}_after_wait")


# ==============================
# FUNCTION: Generate Resume
# ==============================
def generate_resume():
    os.makedirs(DEST_FOLDER, exist_ok=True)

    current_date = datetime.now().strftime("%d_%b_%Y")
    new_filename = f"{RESUME_PREFIX}_{current_date}.pdf"
    destination_path = os.path.join(DEST_FOLDER, new_filename)

    if os.path.exists(destination_path):
        os.remove(destination_path)
        print("Old resume replaced")

    shutil.copy2(SOURCE_RESUME, destination_path)

    print(f"Resume ready: {destination_path}")

    return os.path.abspath(destination_path)


# ==============================
# FUNCTION: CHROME DRIVER
# ==============================
def get_driver():
    chrome_options = Options()

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.7778.97 Safari/537.36"
    )

    proxy = os.getenv("HTTP_PROXY")
    if proxy:
        chrome_options.add_argument(f"--proxy-server={proxy}")
        print(f"Using custom proxy: {proxy}")
    else:
        print("Using default network route")

    print("Launching Chrome...")

    driver = webdriver.Chrome(options=chrome_options)

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

    print("Chrome launched successfully")

    return driver


# ==============================
# FUNCTION: FIND LOGIN FIELDS
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
        elems = driver.find_elements(by, value)
        if elems:
            email_field = elems[0]
            break

    for by, value in password_candidates:
        elems = driver.find_elements(by, value)
        if elems:
            password_field = elems[0]
            break

    if not email_field or not password_field:
        raise Exception("Login fields not found")

    return email_field, password_field


# ==============================
# FUNCTION: FIND LOGIN BUTTON
# ==============================
def find_login_button(driver):
    buttons = driver.find_elements(By.XPATH, "//button[@type='submit']")

    for btn in buttons:
        try:
            if btn.text.strip() == "Login":
                return btn
        except Exception:
            continue

    return None


# ==============================
# FUNCTION: CLICK LOGIN
# ==============================
def click_login(driver, login_btn, attempt):
    driver.execute_script(
        "arguments[0].scrollIntoView({block:'center'});",
        login_btn
    )

    take_screenshot(driver, f"attempt_{attempt}_login_button_found")

    time.sleep(1)

    if attempt == 1:
        login_btn.click()

    elif attempt == 2:
        driver.execute_script("arguments[0].click();", login_btn)

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
            login_btn
        )

    elif attempt == 4:
        driver.execute_script(
            """
            arguments[0].focus();
            arguments[0].click();
            """,
            login_btn
        )

    else:
        driver.execute_script("arguments[0].click();", login_btn)

    take_screenshot(driver, f"attempt_{attempt}_login_clicked")


# ==============================
# FUNCTION: CHECK LOGIN SUCCESS
# ==============================
def login_success(driver):
    url = driver.current_url.lower()

    if "login" not in url:
        return True

    if "profile" in url:
        return True

    return False


# ==============================
# FUNCTION: LOGIN WITH RETRIES
# ==============================
def login_to_naukri(driver):
    for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
        print(f"Login attempt {attempt}")

        driver.get("https://www.naukri.com/nlogin/login")

        sleep_with_screenshot(
            driver,
            5,
            f"attempt_{attempt}_page_load"
        )

        try:
            email_field, password_field = find_login_fields(driver)

            take_screenshot(driver, f"attempt_{attempt}_fields_found")

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
                8,
                f"attempt_{attempt}_after_click"
            )

            if login_success(driver):
                take_screenshot(driver, f"attempt_{attempt}_login_success")
                print("Login successful")
                return True

            take_screenshot(driver, f"attempt_{attempt}_login_not_completed")
            print("Login not completed, retrying...")

        except TimeoutException:
            take_screenshot(driver, f"attempt_{attempt}_timeout")
            print("Timeout during login attempt")

        except Exception as e:
            take_screenshot(driver, f"attempt_{attempt}_error")
            print("Login attempt failed:", e)

        sleep_with_screenshot(
            driver,
            3,
            f"attempt_{attempt}_retry_wait"
        )

    raise Exception("Unable to login after retries")


# ==============================
# FUNCTION: UPLOAD RESUME
# ==============================
def upload_resume(driver, resume_path):
    print("Opening profile page...")

    driver.get("https://www.naukri.com/mnjuser/profile")

    sleep_with_screenshot(
        driver,
        4,
        "profile_page_load"
    )

    wait = WebDriverWait(driver, 30)

    upload_input = wait.until(
        EC.presence_of_element_located(
            (By.XPATH, "//input[@type='file']")
        )
    )

    take_screenshot(driver, "upload_input_found")

    upload_input.send_keys(resume_path)

    sleep_with_screenshot(
        driver,
        4,
        "after_resume_upload"
    )

    take_screenshot(driver, "resume_uploaded")

    print("Resume uploaded successfully")


# ==============================
# FUNCTION: MAIN FLOW
# ==============================
def upload_to_naukri(resume_path):
    driver = get_driver()

    try:
        take_screenshot(driver, "00_browser_started")

        login_to_naukri(driver)

        upload_resume(driver, resume_path)

        take_screenshot(driver, "final_state")

    finally:
        driver.quit()
        print("Browser closed")


# ==============================
# MAIN
# ==============================
if __name__ == "__main__":
    print("===== Naukri Automation Started =====")

    if not EMAIL or not PASSWORD:
        print("Missing NAUKRI_EMAIL or NAUKRI_PASSWORD")
        raise SystemExit(1)

    resume_path = generate_resume()

    upload_to_naukri(resume_path)

    print("===== Process Completed =====")
