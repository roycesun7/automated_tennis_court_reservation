from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
PARTICIPANT = os.getenv("PARTICIPANT")
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
PREFERRED_HOUR = int(os.getenv("PREFERRED_HOUR", "18"))

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

def add_participant(driver, participant_name):
    try:
        add_participant_div = driver.find_element(By.ID, "addParticipant")
        add_participant_div.click()
        
        time.sleep(1)
        
        guest_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "guest_1"))
        )
        
        guest_input.clear()
        guest_input.send_keys(participant_name)
        
        time.sleep(2)
        
        suggestions = WebDriverWait(driver, 5).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".ui-menu-item"))
        )
        
        if suggestions:
            suggestions[0].click()
            time.sleep(1)
            print(f"✓ Added participant: {participant_name}")
            return True
        else:
            print(f"No suggestions found for: {participant_name}")
            return False
            
    except Exception as e:
        print(f"Error adding participant: {e}")
        return False

def send_email_summary(results):
    if not EMAIL or not EMAIL_PASSWORD:
        print("Email credentials not configured - skipping email")
        return
    
    subject = f"Penn Tennis Reservation Summary - {datetime.now().strftime('%B %d, %Y')}"
    
    body = "Penn Tennis Court Reservation Summary\n"
    body += "="*50 + "\n\n"
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    if successful:
        body += "✓ SUCCESSFULLY BOOKED:\n"
        body += "-"*50 + "\n"
        for r in successful:
            body += f"  {r['date']}: {r['time']} (Outdoor)\n"
        body += "\n"
    
    if failed:
        body += "✗ NO COURTS AVAILABLE:\n"
        body += "-"*50 + "\n"
        for r in failed:
            body += f"  {r['date']}: {r['reason']}\n"
        body += "\n"
    
    body += f"\nTotal: {len(successful)} booked, {len(failed)} unavailable\n"
    body += f"Participant: {PARTICIPANT}\n"
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL
    msg['To'] = EMAIL
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("\n✓ Email summary sent successfully!")
    except Exception as e:
        print(f"\n✗ Failed to send email: {e}")

def reserve_earliest_outdoor_court(driver, target_date):
    date_str = target_date.strftime("%m/%d/%Y")
    
    print(f"\n{'='*60}")
    print(f"Attempting to reserve: {target_date.strftime('%A, %B %d, %Y')}")
    print('='*60)
    
    reserve_link = driver.find_element(By.LINK_TEXT, "Reserve a Court")
    reserve_link.click()
    
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.ID, "date")))
    
    time.sleep(2)
    
    date_input = driver.find_element(By.ID, "date")
    date_input.clear()
    date_input.send_keys(date_str)
    
    participant_added = add_participant(driver, PARTICIPANT)
    if not participant_added:
        print("Failed to add participant - skipping reservation")
        driver.get("https://penntennis.clubautomation.com/member")
        time.sleep(2)
        return {"success": False, "date": target_date.strftime('%A, %B %d'), "reason": "Failed to add participant"}
    
    search_button = driver.find_element(By.CSS_SELECTOR, "button.btn-info")
    search_button.click()
    
    time.sleep(3)
    
    outdoor_cells = driver.find_elements(By.XPATH, "//td[.//b[text()='Outdoor']]")
    
    if not outdoor_cells:
        print("No outdoor courts available - skipping this day")
        driver.get("https://penntennis.clubautomation.com/member")
        time.sleep(2)
        return {"success": False, "date": target_date.strftime('%A, %B %d'), "reason": "No outdoor courts available"}
    
    print(f"Found {len(outdoor_cells)} outdoor court cells")
    
    def time_to_minutes(time_str):
        try:
            time_lower = time_str.lower()
            parts = time_str.replace('am', '').replace('pm', '').replace('AM', '').replace('PM', '').strip().split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            
            if 'pm' in time_lower and hour != 12:
                hour += 12
            elif 'am' in time_lower and hour == 12:
                hour = 0
                
            return hour * 60 + minute
        except:
            return 0
    
    available_times = []
    
    for cell in outdoor_cells:
        cell_text = cell.text
        if 'Indoor' in cell_text:
            print(f"WARNING: Skipping cell that contains 'Indoor': {cell_text[:50]}")
            continue
        
        if 'Outdoor' not in cell_text:
            print(f"WARNING: Cell doesn't contain 'Outdoor': {cell_text[:50]}")
            continue
            
        time_links = cell.find_elements(By.XPATH, ".//a[@t]")
        for link in time_links:
            time_text = link.text.strip()
            if time_text and ('am' in time_text.lower() or 'pm' in time_text.lower()):
                minutes = time_to_minutes(time_text)
                available_times.append((time_text, link, minutes))
    
    if not available_times:
        print("No outdoor times available")
        driver.get("https://penntennis.clubautomation.com/member")
        time.sleep(2)
        return {"success": False, "date": target_date.strftime('%A, %B %d'), "reason": "No times available"}
    
    preferred_minutes = PREFERRED_HOUR * 60
    after_preferred = [t for t in available_times if t[2] >= preferred_minutes]
    
    if after_preferred:
        after_preferred.sort(key=lambda x: x[2])
        selected_time, selected_link, _ = after_preferred[0]
        print(f"Selected earliest time after {PREFERRED_HOUR}:00: {selected_time}")
    else:
        available_times.sort(key=lambda x: x[2], reverse=True)
        selected_time, selected_link, _ = available_times[0]
        print(f"No times after {PREFERRED_HOUR}:00 - selected latest available time: {selected_time}")
    
    print(f"Clicking on outdoor time slot...")
    
    selected_link.click()
    
    time.sleep(3)
    
    time.sleep(2)
    
    confirm_buttons = driver.find_elements(By.XPATH, "//button[contains(text(), 'Confirm') or contains(text(), 'Reserve') or contains(text(), 'Submit')]")
    
    if confirm_buttons:
        print(f"Found confirmation button, clicking to complete reservation...")
        confirm_buttons[0].click()
        time.sleep(3)
        print(f"✓ Reserved outdoor court at {selected_time} on {date_str}")
        success = True
    else:
        print(f"No confirmation button found - reservation may not be complete")
        success = False
    
    time.sleep(2)
    
    driver.get("https://penntennis.clubautomation.com/member")
    time.sleep(2)
    
    return {"success": success, "date": target_date.strftime('%A, %B %d'), "time": selected_time}

driver = webdriver.Chrome()

try:
    login(driver)
    
    results = []
    for day_offset in range(7):
        target_date = datetime.now() + timedelta(days=day_offset)
        result = reserve_earliest_outdoor_court(driver, target_date)
        results.append(result)
    
    print("\n" + "="*60)
    print("Reservation process completed")
    print("="*60)
    
    send_email_summary(results)
    
    time.sleep(5)
    
finally:
    driver.quit()

