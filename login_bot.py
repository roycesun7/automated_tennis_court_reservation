from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import os
import time

load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

driver = webdriver.Chrome()

try:
    driver.get("https://penntennis.clubautomation.com/member")
    
    print("Page loaded. Looking for login elements...")
    time.sleep(3)
    
    print("Page source snippet:")
    print(driver.page_source[:1000])
    
    wait = WebDriverWait(driver, 15)
    
    possible_selectors = [
        (By.ID, "loginUserName"),
        (By.NAME, "username"),
        (By.CSS_SELECTOR, "input[type='text']"),
        (By.XPATH, "//input[contains(@placeholder, 'Username') or contains(@id, 'user')]")
    ]
    
    username_field = None
    for selector_type, selector_value in possible_selectors:
        try:
            username_field = wait.until(
                EC.presence_of_element_located((selector_type, selector_value))
            )
            print(f"Found username field with: {selector_type} = {selector_value}")
            break
        except:
            continue
    
    if not username_field:
        print("Could not find username field. Saving screenshot...")
        driver.save_screenshot("login_page.png")
        raise Exception("Username field not found")
    
    password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    
    print("Entering credentials...")
    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)
    
    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
    login_button.click()
    
    print("Login button clicked. Waiting for page load...")
    time.sleep(5)
    
    print(f"Current URL: {driver.current_url}")
    print(f"Page title: {driver.title}")
    
    print("\n=== Looking for courts/reservation links ===")
    
    all_links = driver.find_elements(By.TAG_NAME, "a")
    print(f"\nFound {len(all_links)} total links")
    
    court_keywords = ['court', 'tennis', 'reserve', 'book', 'schedule']
    relevant_links = []
    
    for link in all_links:
        text = link.text.strip().lower()
        href = link.get_attribute('href')
        if any(keyword in text or (href and keyword in href.lower()) for keyword in court_keywords):
            relevant_links.append((link.text.strip(), href))
            print(f"  - {link.text.strip()} -> {href}")
    
    print("\n=== Saving page source for analysis ===")
    with open("page_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    
    driver.save_screenshot("logged_in_page.png")
    print("Saved page source and screenshot")
    
    time.sleep(20)
    
finally:
    driver.quit()

