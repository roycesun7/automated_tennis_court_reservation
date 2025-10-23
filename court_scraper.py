from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
import time

load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

def login(driver):
    driver.get("https://penntennis.clubautomation.com/member")
    wait = WebDriverWait(driver, 15)
    
    username_field = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
    )
    password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    
    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)
    
    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    login_button.click()
    
    time.sleep(3)

def get_available_times(driver, days_ahead=7):
    reserve_link = driver.find_element(By.LINK_TEXT, "Reserve a Court")
    reserve_link.click()
    
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "date")))
    
    time.sleep(2)
    
    for day_offset in range(days_ahead):
        target_date = datetime.now() + timedelta(days=day_offset)
        date_str = target_date.strftime("%m/%d/%Y")
        
        date_input = driver.find_element(By.ID, "date")
        date_input.clear()
        date_input.send_keys(date_str)
        
        search_button = driver.find_element(By.CSS_SELECTOR, "button.btn-info")
        search_button.click()
        
        time.sleep(3)
        
        print(f"\n{'='*60}")
        print(f"{target_date.strftime('%A, %B %d, %Y')}")
        print('='*60)
        
        table = driver.find_elements(By.TAG_NAME, "table")
        if not table:
            print("\nNo results found")
            continue
        
        indoor_cells = driver.find_elements(By.XPATH, "//td[.//b[text()='Indoor']]")
        outdoor_cells = driver.find_elements(By.XPATH, "//td[.//b[text()='Outdoor']]")
        
        indoor_times = []
        outdoor_times = []
        
        for cell in indoor_cells:
            time_links = cell.find_elements(By.XPATH, ".//a[@t]")
            for link in time_links:
                time_text = link.text.strip()
                if time_text and ('am' in time_text.lower() or 'pm' in time_text.lower()):
                    indoor_times.append(time_text)
        
        for cell in outdoor_cells:
            time_links = cell.find_elements(By.XPATH, ".//a[@t]")
            for link in time_links:
                time_text = link.text.strip()
                if time_text and ('am' in time_text.lower() or 'pm' in time_text.lower()):
                    outdoor_times.append(time_text)
        
        indoor_times = sorted(set(indoor_times), key=lambda x: (int(x.split(':')[0]) % 12 + (12 if 'pm' in x.lower() else 0), int(x.split(':')[1][:2])))
        outdoor_times = sorted(set(outdoor_times), key=lambda x: (int(x.split(':')[0]) % 12 + (12 if 'pm' in x.lower() else 0), int(x.split(':')[1][:2])))
        
        if indoor_times:
            print("\nIndoor:")
            print(f"  {', '.join(indoor_times)}")
        else:
            print("\nIndoor: None")
        
        if outdoor_times:
            print("\nOutdoor:")
            print(f"  {', '.join(outdoor_times)}")
        else:
            print("\nOutdoor: None")

driver = webdriver.Chrome()

try:
    login(driver)
    get_available_times(driver)
    
finally:
    driver.quit()

