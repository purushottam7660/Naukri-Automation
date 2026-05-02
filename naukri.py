import os
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
# CONFIG
# ==============================
EMAIL = os.getenv("NAUKRI_EMAIL")
PASSWORD = os.getenv("NAUKRI_PASSWORD")
PROXY = os.getenv("PROXY")  # optional

SOURCE_RESUME = "Purushottam_Kumar_CV.pdf"
DEST_FOLDER = "Naukri_resume"
RESUME_PREFIX = "Purushottam_Kumar_Resume"

# ==============================
# UTIL: Human typing
# ==============================
def type_like_human(element, text):
    for ch in text:
        element.send_keys(ch)
        time.sleep(random.uniform(0.05, 0.15))

# ==============================
# GENERATE RESUME
# ==============================
def generate_resume():
    os.makedirs(DEST_FOLDER, exist_ok=True)

    date = datetime.now().strftime("%d_%b_%Y")
    path = os.path.join(DEST_FOLDER, f"{RESUME_PREFIX}_{date}.pdf")

    if os.path.exists(path):
        os.remove(path)

    shutil.copy2(SOURCE_RESUME, path)
    print("✅ Resume ready:", path)

    return os.path.abspath(path)

# ==============================
# DRIVER SETUP
# ==============================
def get_driver():
    options = Options()

    # Headless for GitHub; comment this locally for better success
    options.add_argument("--headless=new")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # UA (Chrome 147)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    )

    # Language & headers hints
    options.add_argument("--lang=en-US,en;q=0.9")

    # Proxy (optional)
    if PROXY:
        print("🌐 Using Proxy:", PROXY)
        options.add_argument(f"--proxy-server={PROXY}")
    else:
        print("🌐 No proxy used")

    # Reduce obvious automation flag
    options.add_argument("--disable-blink-features=AutomationControlled")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Minor webdriver flag reduction
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """
    })

    return driver

# ==============================
# LOGIN
# ==============================
def login(driver, wait):
    print("🌐 Opening login page...")
    driver.get("https://www.naukri.com/nlogin/login")

    time.sleep(4)
    print("📄 Page Title:", driver.title)

    if "Access Denied" in driver.title:
        print("❌ Blocked page")
        driver.save_screenshot("blocked.png")
        return False

    try:
        email = wait.until(EC.element_to_be_clickable((By.ID, "usernameField")))
        password = wait.until(EC.element_to_be_clickable((By.ID, "passwordField")))

        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", email)

        email.clear()
        type_like_human(email, EMAIL)

        time.sleep(random.uniform(0.5, 1.2))

        password.clear()
        type_like_human(password, PASSWORD)

        time.sleep(random.uniform(0.5, 1.2))
        password.send_keys(Keys.RETURN)

    except Exception:
        print("⚠️ Fallback JS input")
        driver.execute_script("""
            document.getElementById('usernameField').value = arguments[0];
            document.getElementById('passwordField').value = arguments[1];
        """, EMAIL, PASSWORD)
        driver.execute_script("document.querySelector('button[type=\"submit\"]').click();")

    print("🔐 Logging in...")

    try:
        wait.until(lambda d: "login" not in d.current_url)
        print("✅ Login success")
        return True
    except:
        print("❌ Login failed")
        driver.save_screenshot("login_error.png")
        return False

# ==============================
# UPLOAD
# ==============================
def upload_resume(driver, wait, resume_path):
    print("📂 Opening profile...")
    driver.get("https://www.naukri.com/mnjuser/profile")

    upload = wait.until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
    )

    time.sleep(random.uniform(1, 2))
    upload.send_keys(resume_path)

    print("🎉 Resume uploaded!")

# ==============================
# MAIN
# ==============================
def main():
    print("===== START =====")

    if not EMAIL or not PASSWORD:
        print("❌ Missing credentials")
        return

    resume_path = generate_resume()
    print("📂 Absolute path:", resume_path)

    driver = get_driver()
    wait = WebDriverWait(driver, 120)

    try:
        for attempt in range(3):
            print(f"🔁 Attempt {attempt+1}")

            if login(driver, wait):
                time.sleep(random.uniform(3, 6))
                upload_resume(driver, wait, resume_path)
                break
            else:
                sleep_time = random.uniform(5, 10)
                print(f"Retrying after {sleep_time:.1f}s...")
                time.sleep(sleep_time)

    except Exception as e:
        print("❌ Error:", e)
        driver.save_screenshot("error.png")

    finally:
        driver.quit()
        print("🧹 Browser closed")
        print("===== DONE =====")

if __name__ == "__main__":
    main()
