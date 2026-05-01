# Penn Tennis Court Scraper

Automated court reservation and availability checker for [Penn Tennis](https://penntennis.clubautomation.com). Uses Selenium to log in, find open courts, and book them based on your time preferences.

## Setup

```bash
pip install -r requirements.txt
brew install chromedriver
xattr -d com.apple.quarantine $(which chromedriver)
cp .env.example .env
```

Edit `.env` with your credentials (see `.env.example` for all options):

```bash
USERNAME=your_penntennis_username
PASSWORD=your_penntennis_password
PARTICIPANT=First Last              # must match a name in the Penn Tennis member database
PREFERRED_HOUR=18                   # 6 PM, 24-hour format
COURT_TYPE=outdoor                  # outdoor, indoor, or both
```

## Usage

**Check availability:**

```bash
python court_scraper.py
python court_scraper.py --type outdoor --days 3 --headless
```

**Book courts:**

```bash
python reserve_courts.py
python reserve_courts.py --headless --days 5 --participant "First Last"
```

Run `--help` on either script for all options.

## Automation (cron)

```bash
crontab -e
# Add: 20 2 * * * /path/to/penntennisscraper/run_daily.sh
```

Logs go to `cron.log` in the project directory.

## Files

| File | Purpose |
|------|---------|
| `court_scraper.py` | Check court availability (read-only) |
| `reserve_courts.py` | Book courts automatically |
| `config.py` | Config loading and validation |
| `utils.py` | Shared helpers (driver setup, logging, retries) |
| `run_daily.sh` | Shell wrapper for cron |
