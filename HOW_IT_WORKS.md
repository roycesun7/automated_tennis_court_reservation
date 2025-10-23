# How Penn Tennis Scraper Works - Complete Technical Guide

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Penn Tennis Website                       │
│         https://penntennis.clubautomation.com                │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ HTTP Requests
                              │ (via Selenium + Chrome)
                              │
┌─────────────────────────────┴─────────────────────────────┐
│                    Selenium WebDriver                       │
│  (Automates Chrome browser to interact with the website)   │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ court_       │    │ reserve_     │    │ login_       │
│ scraper.py   │    │ courts.py    │    │ bot.py       │
│              │    │              │    │              │
│ (Read only)  │    │ (Books       │    │ (Debug       │
│              │    │  courts)     │    │  tool)       │
└──────────────┘    └──────────────┘    └──────────────┘
                            │
                            │ Triggered by
                            ▼
                    ┌──────────────┐
                    │ run_daily.sh │
                    │              │
                    │ (Cron job    │
                    │  at 2:20 AM) │
                    └──────────────┘
```

---

## 🔧 Core Technology: Selenium WebDriver

### What is Selenium?
Selenium is a **browser automation framework** that:
- **Controls a real browser** (Chrome, Firefox, Safari, etc.)
- **Simulates human actions**: clicking buttons, typing text, scrolling
- **Reads page content**: extracts data from HTML elements
- **Works with JavaScript-heavy sites**: waits for dynamic content to load

### Why Use Selenium for This Project?
Penn Tennis website likely uses:
- JavaScript to load court availability dynamically
- AJAX requests to fetch data without page reloads
- Complex DOM structures requiring interaction

A simple HTTP scraper (like `requests` + `BeautifulSoup`) wouldn't work because:
1. The page content loads dynamically via JavaScript
2. You need to click buttons and interact with forms
3. The site may have anti-bot protections that check for real browser behavior

---

## 📁 File-by-File Breakdown

### 1️⃣ `court_scraper.py` - Read-Only Availability Checker

**Purpose:** View what courts are available without making reservations

**Step-by-Step Execution:**

```python
# STEP 1: Initialize and Login
driver = webdriver.Chrome()  # Opens Chrome window
login(driver)  # Authenticates with credentials

# STEP 2: Navigate to Reservation Page
reserve_link = driver.find_element(By.LINK_TEXT, "Reserve a Court")
reserve_link.click()  # Clicks the link

# STEP 3: Loop Through 7 Days
for day_offset in range(7):
    target_date = datetime.now() + timedelta(days=day_offset)
    
    # STEP 4: Enter Date
    date_input = driver.find_element(By.ID, "date")
    date_input.clear()
    date_input.send_keys("10/28/2025")  # Types date
    
    # STEP 5: Search
    search_button = driver.find_element(By.CSS_SELECTOR, "button.btn-info")
    search_button.click()
    
    # STEP 6: Extract Court Times
    # Uses XPath to find cells containing "Indoor" or "Outdoor"
    indoor_cells = driver.find_elements(By.XPATH, "//td[.//b[text()='Indoor']]")
    
    # STEP 7: Get All Time Links
    for cell in indoor_cells:
        time_links = cell.find_elements(By.XPATH, ".//a[@t]")
        # Extracts text like "3:00 PM", "4:30 PM"
```

**Key Selenium Techniques:**

| Method | Purpose | Example |
|--------|---------|---------|
| `find_element(By.ID, "date")` | Find element by HTML id | `<input id="date">` |
| `find_element(By.LINK_TEXT, "text")` | Find link by exact text | `<a>Reserve a Court</a>` |
| `find_elements(By.XPATH, "xpath")` | Find multiple elements | All cells with "Indoor" |
| `element.click()` | Simulate mouse click | Click button |
| `element.send_keys("text")` | Type text into input | Type date |
| `element.clear()` | Clear input field | Remove old date |

**XPath Explained:**
```python
"//td[.//b[text()='Indoor']]"
```
Translation: "Find all `<td>` (table cell) elements that contain a `<b>` (bold) tag with the exact text 'Indoor'"

Example HTML it matches:
```html
<td>
  <b>Indoor</b>
  <a href="#" t="slot1">3:00 PM</a>
  <a href="#" t="slot2">4:00 PM</a>
</td>
```

---

### 2️⃣ `reserve_courts.py` - Automated Booking Bot

**Purpose:** Automatically book outdoor courts for next 7 days

**Complete Workflow:**

```
START
  ↓
Load .env credentials
  ↓
Open Chrome
  ↓
Login to Penn Tennis
  ↓
Initialize results array = []
  ↓
FOR each day (0 to 6):
  ↓
  Navigate to "Reserve a Court"
  ↓
  Enter date (today + day_offset)
  ↓
  Add participant from PARTICIPANT env var
  ↓
  Click search
  ↓
  Find all outdoor court cells
  ↓
  Extract available time slots
  ↓
  Apply time preference logic:
    - Filter times >= PREFERRED_HOUR
    - Sort by earliest
    - If none, pick latest available
  ↓
  Click selected time slot
  ↓
  Click "Confirm" button
  ↓
  Save result (success/failure)
  ↓
  Go back to main page
  ↓
NEXT day
  ↓
Send email summary
  ↓
Close browser
  ↓
END
```

**Intelligent Time Selection Algorithm:**

```python
# Example: PREFERRED_HOUR = 18 (6:00 PM)
# Available times: ["10:00 AM", "2:00 PM", "6:30 PM", "8:00 PM"]

def time_to_minutes(time_str):
    # "6:30 PM" → 1110 minutes (6*60 + 30 + 12*60)
    # "10:00 AM" → 600 minutes (10*60)
    hour = extract_hour(time_str)
    minute = extract_minute(time_str)
    if is_pm(time_str) and hour != 12:
        hour += 12
    return hour * 60 + minute

# Convert all times to minutes
available_times = [
    ("10:00 AM", link1, 600),
    ("2:00 PM", link2, 840),
    ("6:30 PM", link3, 1110),
    ("8:00 PM", link4, 1200)
]

preferred_minutes = 18 * 60  # 1080 minutes

# Filter times >= preferred
after_preferred = [
    ("6:30 PM", link3, 1110),
    ("8:00 PM", link4, 1200)
]

# Pick earliest
selected = "6:30 PM"

# If after_preferred is empty, pick LATEST available
# This maximizes court time in the evening
```

**Participant Addition Logic:**

```python
def add_participant(driver, participant_name):
    # 1. Click "Add Participant" div
    add_participant_div = driver.find_element(By.ID, "addParticipant")
    add_participant_div.click()
    
    # 2. Wait for input field to appear
    guest_input = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, "guest_1"))
    )
    
    # 3. Type participant name
    guest_input.send_keys("Suraj Neelamajam")
    
    # 4. Wait for autocomplete dropdown
    time.sleep(2)  # Let dropdown populate
    
    # 5. Find suggestions
    suggestions = driver.find_elements(By.CSS_SELECTOR, ".ui-menu-item")
    
    # 6. Click first match
    suggestions[0].click()
```

**HTML Structure:**
```html
<div id="addParticipant">+ Add Participant</div>

<!-- After clicking, this appears: -->
<input id="guest_1" type="text" autocomplete="off">

<!-- As you type, this dropdown appears: -->
<ul class="ui-menu">
  <li class="ui-menu-item">
    <div class="ui-menu-item-wrapper">Suraj Neelamajam</div>
  </li>
  <li class="ui-menu-item">
    <div class="ui-menu-item-wrapper">Suraj Smith</div>
  </li>
</ul>
```

**Email Summary (Gmail SMTP):**

```python
def send_email_summary(results):
    # Connect to Gmail SMTP server
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()  # Enable TLS encryption
    
    # Login with app password
    server.login(EMAIL, EMAIL_PASSWORD)
    
    # Create email body
    body = "✓ Successfully booked:\n"
    for r in successful:
        body += f"  {r['date']}: {r['time']} (Outdoor)\n"
    
    # Send email
    server.send_message(msg)
    server.quit()
```

---

### 3️⃣ `login_bot.py` - Debugging Tool

**Purpose:** Test login and explore site structure

**What It Does:**
1. **Tries multiple selectors** to find login fields
2. **Saves screenshot** of login page
3. **Saves HTML source code** for analysis
4. **Lists all links** that mention courts/tennis/reserve
5. **Prints page title and URL** after login

**When to Use:**
- Website structure changes (elements have new IDs)
- Login fails unexpectedly
- Need to find new element selectors
- Exploring new features to automate

**Output Files:**
- `login_page.png` - Screenshot of login page
- `logged_in_page.png` - Screenshot after login
- `page_source.html` - Full HTML of the page

---

## ⏰ Automation with Cron

### How `run_daily.sh` Works

```bash
#!/bin/bash

# Change to project directory
cd /Users/yashsamtani2/penntennisscraper

# Run Python script and append output to log
/Users/yashsamtani2/anaconda3/bin/python reserve_courts.py >> cron.log 2>&1

# Add timestamp
echo "Run completed at $(date)" >> cron.log
```

**Explanation:**
- `>>` - Append output to file (doesn't overwrite)
- `2>&1` - Redirect errors to same log file
- `$(date)` - Current timestamp

### Setting Up Cron

**View current cron jobs:**
```bash
crontab -l
```

**Edit cron schedule:**
```bash
crontab -e
```

**Add this line:**
```bash
20 2 * * * /Users/kzoyce/Downloads/Code_Projects/penntennisscraper-main/run_daily.sh
```

**Cron Schedule Format:**
```
  ┌─── Minute (0-59)
  │ ┌─── Hour (0-23)
  │ │ ┌─── Day of month (1-31)
  │ │ │ ┌─── Month (1-12)
  │ │ │ │ ┌─── Day of week (0-7, Sunday=0 or 7)
  │ │ │ │ │
  * * * * * command

Examples:
0  9 * * *     → 9:00 AM daily
30 18 * * 1-5  → 6:30 PM weekdays
0  0 1 * *     → Midnight on 1st of month
*/15 * * * *   → Every 15 minutes
```

**Check logs:**
```bash
tail -f /Users/kzoyce/Downloads/Code_Projects/penntennisscraper-main/cron.log
```

---

## 🔐 Environment Variables (`.env` file)

```bash
# Login credentials
USERNAME=your_penntennis_username
PASSWORD=your_penntennis_password

# Reservation settings
PARTICIPANT=Partner Name         # Added to each reservation
PREFERRED_HOUR=18               # 6 PM in 24-hour format

# Email notifications (optional)
EMAIL=youremail@gmail.com
EMAIL_PASSWORD=app_password     # Not your regular password!
```

**Gmail App Password Setup:**
1. Go to https://myaccount.google.com/apppasswords
2. Create app password for "Mail"
3. Use generated password (16 characters) in `.env`

---

## 🧪 Testing & Running

### Test 1: Check Availability (Read-Only)
```bash
cd /Users/kzoyce/Downloads/Code_Projects/penntennisscraper-main
python court_scraper.py
```

**Expected Output:**
```
============================================================
Monday, October 28, 2025
============================================================

Indoor:
  9:00 AM, 10:30 AM, 2:00 PM, 4:00 PM

Outdoor:
  10:00 AM, 6:00 PM, 7:30 PM

============================================================
Tuesday, October 29, 2025
...
```

### Test 2: Book Courts (Automated)
```bash
python reserve_courts.py
```

**Expected Output:**
```
============================================================
Attempting to reserve: Monday, October 28, 2025
============================================================
Found 3 outdoor court cells
✓ Added participant: Suraj Neelamajam
Selected earliest time after 18:00: 6:30 PM
Clicking on outdoor time slot...
Found confirmation button, clicking to complete reservation...
✓ Reserved outdoor court at 6:30 PM on 10/28/2025

============================================================
Attempting to reserve: Tuesday, October 29, 2025
============================================================
No outdoor courts available - skipping this day

...

✓ Email summary sent successfully!
```

### Test 3: Debug Login Issues
```bash
python login_bot.py
```

**Check output:**
```bash
open login_page.png
open logged_in_page.png
open page_source.html
```

---

## 🐛 Common Issues & Solutions

### Issue 1: ChromeDriver Blocked by macOS
**Error:** `Killed: 9`

**Solution:**
```bash
xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver
```

Or manually allow in System Settings → Privacy & Security

### Issue 2: Element Not Found
**Error:** `NoSuchElementException`

**Cause:** Website structure changed

**Solution:**
1. Run `login_bot.py` to see current structure
2. Update selectors in `court_scraper.py` or `reserve_courts.py`
3. Use browser DevTools (F12) to inspect elements

### Issue 3: Timeout Waiting for Elements
**Error:** `TimeoutException`

**Cause:** Page loading slowly or element doesn't exist

**Solution:**
```python
# Increase wait time
wait = WebDriverWait(driver, 30)  # Changed from 10 to 30

# Or add explicit sleep
time.sleep(5)
```

### Issue 4: Email Not Sending
**Error:** `SMTPAuthenticationError`

**Cause:** Using regular Gmail password instead of app password

**Solution:**
1. Generate app password: https://myaccount.google.com/apppasswords
2. Update `.env` with 16-character app password

### Issue 5: No Courts Available
**Message:** `No outdoor courts available - skipping this day`

**Cause:** Penn Tennis doesn't open reservations 7 days in advance

**Solution:** This is expected behavior. The script will skip those days.

---

## 📊 Data Flow Diagram

```
┌─────────────┐
│  .env File  │
│  (Config)   │
└──────┬──────┘
       │
       ├─→ USERNAME
       ├─→ PASSWORD
       ├─→ PARTICIPANT
       ├─→ PREFERRED_HOUR
       └─→ EMAIL credentials
              ↓
┌──────────────────────────────────────┐
│     reserve_courts.py                │
├──────────────────────────────────────┤
│ 1. login(driver)                     │
│    └─→ Navigate to login page        │
│    └─→ Enter USERNAME & PASSWORD     │
│    └─→ Click login button            │
│                                      │
│ 2. FOR each day (0-6):               │
│    └─→ reserve_earliest_outdoor()    │
│        ├─→ Set date                  │
│        ├─→ Add PARTICIPANT           │
│        ├─→ Search courts             │
│        ├─→ Filter outdoor only       │
│        ├─→ Apply PREFERRED_HOUR      │
│        ├─→ Click time slot           │
│        ├─→ Confirm booking           │
│        └─→ Return result             │
│                                      │
│ 3. send_email_summary(results)       │
│    └─→ Connect to Gmail SMTP         │
│    └─→ Format email body             │
│    └─→ Send to EMAIL                 │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│        Results Array                 │
├──────────────────────────────────────┤
│ [                                    │
│   {success: true,  date: "Mon Oct 28", time: "6:30 PM"},
│   {success: false, date: "Tue Oct 29", reason: "No courts"},
│   {success: true,  date: "Wed Oct 30", time: "7:00 PM"},
│   ...                                │
│ ]                                    │
└──────────────────────────────────────┘
              ↓
┌──────────────────────────────────────┐
│         Email Summary                │
├──────────────────────────────────────┤
│ ✓ SUCCESSFULLY BOOKED:               │
│   Mon Oct 28: 6:30 PM (Outdoor)      │
│   Wed Oct 30: 7:00 PM (Outdoor)      │
│                                      │
│ ✗ NO COURTS AVAILABLE:               │
│   Tue Oct 29: No outdoor courts      │
│                                      │
│ Total: 2 booked, 1 unavailable       │
└──────────────────────────────────────┘
```

---

## 🎯 Key Takeaways

1. **Selenium simulates a real browser** - necessary for JavaScript-heavy sites
2. **WebDriverWait is crucial** - ensures elements load before interacting
3. **XPath provides powerful element selection** - can find complex nested elements
4. **Time selection uses smart logic** - prioritizes preferred hours
5. **Error handling is essential** - skips days with no availability
6. **Cron enables automation** - runs daily without manual intervention
7. **Email provides confirmation** - know what was booked without checking manually

---

## 🚀 Next Steps

1. **Create your `.env` file:**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your credentials
   ```

2. **Fix ChromeDriver permissions:**
   ```bash
   xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver
   ```

3. **Test availability check:**
   ```bash
   python court_scraper.py
   ```

4. **Test booking (careful - this makes real reservations!):**
   ```bash
   python reserve_courts.py
   ```

5. **Set up cron for automation:**
   ```bash
   crontab -e
   # Add: 20 2 * * * /path/to/run_daily.sh
   ```

---

## 📚 Additional Resources

- **Selenium Documentation:** https://selenium-python.readthedocs.io/
- **XPath Tutorial:** https://www.w3schools.com/xml/xpath_syntax.asp
- **Cron Expression Generator:** https://crontab.guru/
- **Gmail App Passwords:** https://myaccount.google.com/apppasswords

---

*Happy court booking! 🎾*

