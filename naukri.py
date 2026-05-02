import os
import sys
import shutil
import time
import random
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager

# ==============================
# UTF-8 FIX
# ==============================
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding='utf-8')

# ==============================
# CONFIG
# ==============================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")
PROXY = os.getenv("PROXY")

SOURCE_RESUME = "Purushottam_Kumar_CV.pdf"
DEST_FOLDER = "Naukri_resume"
RESUME_PREFIX = "Purushottam_Kumar_Resume"

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# ==============================
# SCREENSHOT
# ==============================
def snap(driver, name):
    path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
    driver.save_screenshot(path)
    print("[SCREENSHOT]", path)

# ==============================
# HUMAN TYPING
# ==============================
def type_like_human(element, text):
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.05, 0.15))

# ==============================
# RESUME GENERATION
# ==============================
def generate_resume():
    os.makedirs(DEST_FOLDER, exist_ok=True)

    date = datetime.now().strftime("%d_%b_%Y")
    path = os.path.join(DEST_FOLDER, f"{RESUME_PREFIX}_{date}.pdf")

    if os.path.exists(path):
        os.remove(path)

    shutil.copy2(SOURCE_RESUME, path)

    print("[SUCCESS] Resume ready:", path)
    return os.path.abspath(path)

# ==============================
# DRIVER SETUP
# ==============================
def get_driver():
    options = Options()

    # ==========================
    # CORE SETTINGS
    # ==========================
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # ==========================
    # FORCE CLEAN SESSION
    # ==========================
    options.add_argument("--incognito")  # ✅ no cookies stored
    options.add_argument("--disable-application-cache")
    options.add_argument("--disable-cache")
    options.add_argument("--disk-cache-size=0")

    # ==========================
    # USER AGENT
    # ==========================
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    )

    options.add_argument("--lang=en-US,en;q=0.9")

    # ==========================
    # PROXY (if any)
    # ==========================
    if PROXY:
        print("[INFO] Proxy:", PROXY)
        options.add_argument(f"--proxy-server={PROXY}")

    # ==========================
    # DRIVER INIT
    # ==========================
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # ==========================
    # EXTRA CLEAN BROWSER STATE
    # ==========================
    try:
        driver.execute_cdp_cmd("Network.enable", {})
        driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
        driver.execute_cdp_cmd("Network.clearBrowserCache", {})
    except:
        pass

    # ==========================
    # REMOVE AUTOMATION FLAGS
    # ==========================
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            window.chrome = { runtime: {} };

            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """
    })

    return driver

# ==============================
# LOGIN (FULL FIXED VERSION)
# ==============================
def login(driver, wait):
    print("[INFO] Opening login page")
    driver.get("https://www.naukri.com/nlogin/login")
    time.sleep(4)
    snap(driver, "1_login_page")

    try:
        email = wait.until(EC.element_to_be_clickable((By.ID, "usernameField")))
        password = wait.until(EC.element_to_be_clickable((By.ID, "passwordField")))

        email.clear()
        type_like_human(email, EMAIL)
        snap(driver, "2_email_filled")

        password.clear()
        type_like_human(password, PASSWORD)
        snap(driver, "3_password_filled")

        # ==========================================
        # ✅ MULTI-FALLBACK LOGIN BUTTON CLICK
        # ==========================================

        login_btn = None

        # ==========================
        # 1st: Blue UI login button (latest UI)
        # ==========================
        try:
            login_btn = driver.find_element(
                By.CSS_SELECTOR,
                "button.waves-effect.waves-light.btn-large.btn-block.btn-bold.blue-btn.textTransform"
            )
            print("[INFO] Found blue UI login button")
        except:
            print("[WARN] Blue UI login button not found")
        
        # ==========================
        # 2nd: Text-based fallback
        # ==========================
        if not login_btn:
            try:
                login_btn = driver.find_element(
                    By.XPATH,
                    "//button[contains(text(),'Login') or contains(.,'Login')]"
                )
                print("[INFO] Found text-based login button")
            except:
                print("[WARN] Text-based login button not found")
        
        # ==========================
        # 3rd: Primary selector (old UI)
        # ==========================
        if not login_btn:
            try:
                login_btn = driver.find_element(
                    By.CSS_SELECTOR,
                    "button.btn-primary.loginButton"
                )
                print("[INFO] Found primary login button")
            except:
                print("[WARN] Primary login button not found")

# ==========================
# CLICK SAFELY
# ==========================
if login_btn:
    try:
        # driver.execute_script("arguments[0].scrollIntoView(true);", login_btn)
        login_btn.click()
        print("[SUCCESS] Login button clicked")
    except:
        print("[WARN] Normal click failed, trying JS click")
        driver.execute_script("arguments[0].click();", login_btn)
else:
    print("[ERROR] No login button found in any selector")

        # CLICK SAFELY
        if login_btn:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", login_btn)
                time.sleep(1)
                login_btn.click()
                print("[SUCCESS] Login button clicked")
            except:
                print("[WARN] Normal click failed, using JS click")
                driver.execute_script("arguments[0].click();", login_btn)
        else:
            print("[FATAL] Login button not found")
            return False

    except Exception as e:
        print("[ERROR] Login flow failed:", e)
        snap(driver, "login_error")
        return False

    time.sleep(6)
    snap(driver, "4_after_login")

    if "login" not in driver.current_url:
        print("[SUCCESS] Login successful")
        return True
    else:
        print("[ERROR] Login failed / OTP triggered")
        snap(driver, "login_failed")
        return False

# ==============================
# RESUME UPLOAD
# ==============================
def upload_resume(driver, wait, resume_path):
    print("[INFO] Opening profile page")

    driver.get("https://www.naukri.com/mnjuser/profile")
    time.sleep(5)
    snap(driver, "5_profile")

    try:
        update_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//span[contains(text(),'Update resume')]"))
        )
        update_btn.click()

        time.sleep(2)
        snap(driver, "6_popup")

        upload = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
        )

        upload.send_keys(resume_path)
        time.sleep(3)

        snap(driver, "7_uploaded")
        print("[SUCCESS] Resume uploaded")

    except Exception as e:
        print("[ERROR] Upload failed:", e)
        snap(driver, "upload_error")

# ==============================
# MAIN
# ==============================
def main():
    print("===== START =====")

    if not EMAIL or not PASSWORD:
        print("[ERROR] Missing credentials")
        return

    resume_path = generate_resume()

    driver = get_driver()
    wait = WebDriverWait(driver, 120)

    try:
        snap(driver, "start")

        for i in range(3):
            print("[INFO] Attempt", i + 1)

            if login(driver, wait):
                time.sleep(3)
                upload_resume(driver, wait, resume_path)
                snap(driver, "success")
                break
            else:
                time.sleep(5)

    except Exception as e:
        print("[ERROR]", e)
        snap(driver, "fatal_error")

    finally:
        driver.quit()
        print("===== DONE =====")

if __name__ == "__main__":
    main()
