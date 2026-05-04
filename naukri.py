import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# =========================
# CONFIG
# =========================
EMAIL = os.getenv("NAUKRI_EMAIL", "your_email@example.com")
PASSWORD = os.getenv("NAUKRI_PASSWORD", "your_password")

RESUME_PATH = os.path.abspath(
    "Naukri_resume/Purushottam_Kumar_Resume_04_May_2026.pdf"
)

LOGIN_URL = "https://www.naukri.com/nlogin/login"

# =========================
# DRIVER SETUP (FIREFOX)
# =========================
def start_driver():
    print("[INFO] Launching Firefox...")

    options = Options()
    options.add_argument("--start-maximized")

    service = Service()  # geckodriver must be in PATH
    driver = webdriver.Firefox(service=service, options=options)

    driver.implicitly_wait(5)
    return driver


# =========================
# LOGIN FUNCTION
# =========================
def login(driver):
    wait = WebDriverWait(driver, 20)

    print("[STEP] Opening login page")
    driver.get(LOGIN_URL)

    # Email input
    email_box = wait.until(
        EC.presence_of_element_located((By.ID, "usernameField"))
    )
    email_box.clear()
    email_box.send_keys(EMAIL)

    # Password input
    pass_box = driver.find_element(By.ID, "passwordField")
    pass_box.clear()
    pass_box.send_keys(PASSWORD)

    print("[INFO] Credentials entered")

    # =========================
    # LOGIN BUTTON FIX (your selector included)
    # =========================
    try:
        login_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[class='btn-primary loginButton']")
            )
        )
        print("[INFO] Using primary login button selector")
    except:
        print("[WARN] Primary login button not found, trying fallback")

        login_btn = wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.waves-effect, button[type='submit']")
            )
        )

    driver.execute_script("arguments[0].click();", login_btn)
    print("[SUCCESS] Login button clicked")

    time.sleep(5)


# =========================
# AVOID OTP SCREEN
# =========================
def handle_otp_or_skip(driver):
    try:
        if "otp" in driver.page_source.lower():
            print("[INFO] OTP page detected — please complete manually")
            input("Press ENTER after completing OTP...")
    except:
        pass


# =========================
# RESUME UPLOAD (BASIC FLOW)
# =========================
def upload_resume(driver):
    wait = WebDriverWait(driver, 20)

    print("[STEP] Navigating to profile")

    driver.get("https://www.naukri.com/mnjuser/profile")

    try:
        upload_btn = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@type='file']")
            )
        )

        upload_btn.send_keys(RESUME_PATH)
        print("[SUCCESS] Resume uploaded")

    except Exception as e:
        print("[ERROR] Resume upload failed:", e)


# =========================
# SCREENSHOT HELPER
# =========================
def screenshot(driver, name):
    os.makedirs("screenshots", exist_ok=True)
    path = f"screenshots/{name}.png"
    driver.save_screenshot(path)
    print(f"[SS] Saved: {path}")


# =========================
# MAIN RUNNER
# =========================
def run():
    print("===== START =====")

    driver = start_driver()

    try:
        screenshot(driver, "login_page")

        login(driver)
        screenshot(driver, "after_login")

        handle_otp_or_skip(driver)

        upload_resume(driver)
        screenshot(driver, "final")

        print("[DONE] Automation complete")

    except Exception as e:
        print("[FATAL ERROR]", e)
        screenshot(driver, "error")

    finally:
        print("[EXIT] Closing driver")
        time.sleep(3)
        driver.quit()


if __name__ == "__main__":
    run()
