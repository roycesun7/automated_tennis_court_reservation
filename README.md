## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install ChromeDriver:
```bash
brew install chromedriver
xattr -d com.apple.quarantine $(which chromedriver)
```

3. Configure credentials:
   - Edit `.env` file
   - Add your credentials:
```
USERNAME=your_username
PASSWORD=your_password
PARTICIPANT=Suraj Neelamajam
PREFERRED_HOUR=18
EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

**Configuration Notes:**
- `PREFERRED_HOUR`: Hour in 24-hour format (1-24). Example: 18 = 6 PM, 14 = 2 PM
- For Gmail, you need to use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password
- The email will be sent to the same address you configure
- Email notifications are optional - script works without them

## Usage

### Court Scraper
Shows available indoor and outdoor court times for the next week:
```bash
python court_scraper.py
```

Output shows available times for each day:
- Indoor court availability
- Outdoor court availability

### Court Reservation Bot (Main Tool)
Automatically reserves the earliest available outdoor court for the next 7 days:
```bash
python reserve_courts.py
```

Features:
- Reserves ONLY outdoor courts (never indoor)
- Prioritizes times from PREFERRED_HOUR onwards (earliest time >= preferred hour)
- Falls back to latest available time if no times after preferred hour
- Automatically adds participant from PARTICIPANT env variable
- Skips days with no outdoor availability
- Shows confirmation for each successful reservation
- Sends email summary after completion (if configured)

### Login Bot (Testing)
Basic login test script:
```bash
python login_bot.py
```

## Automated Daily Execution

The script is configured to run automatically every day at 2:20 AM via cron.

**Setup:**
The cron job is already configured. You can verify it with:
```bash
crontab -l
```

**Logs:**
Check execution logs at:
```bash
tail -f cron.log
```

**To disable automatic execution:**
```bash
crontab -r
```

**To re-enable or modify the schedule:**
```bash
crontab -e
# Edit the time: 20 2 * * * means 2:20 AM daily
# Format: minute hour day month weekday
```

