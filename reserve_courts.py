"""Automated court reservation bot for Penn Tennis."""

import argparse
import sys
import time
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import config
from utils import (
    logger, retry_on_failure, save_error_screenshot, save_page_source,
    create_chrome_driver, safe_click, safe_send_keys, print_banner,
    print_summary, validate_env_file, PerformanceTimer
)


@retry_on_failure(max_attempts=3, delay=2, exceptions=(TimeoutException,))
def login(driver):
    """Login to Penn Tennis website."""
    logger.info("Attempting to login...")
    try:
        driver.get("https://penntennis.clubautomation.com/member")
        wait = WebDriverWait(driver, config.BROWSER_TIMEOUT)

        username_field = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
        )
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")

        safe_send_keys(username_field, config.USERNAME, "username field")
        safe_send_keys(password_field, config.PASSWORD, "password field")

        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        safe_click(driver, login_button, "login button")

        time.sleep(3)
        logger.info("Login successful")
        return True
    except Exception as e:
        logger.error(f"Login failed: {e}")
        save_error_screenshot(driver, "login_error")
        save_page_source(driver, "login_error")
        raise


def add_participant(driver, participant_name):
    """Add a participant to the reservation."""
    if not participant_name:
        logger.info("No participant specified, skipping")
        return True

    try:
        add_participant_div = driver.find_element(By.ID, "addParticipant")
        safe_click(driver, add_participant_div, "add participant button")
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
            logger.info(f"Added participant: {participant_name}")
            return True
        else:
            logger.warning(f"No suggestions found for: {participant_name}")
            return False
    except Exception as e:
        logger.error(f"Error adding participant: {e}")
        save_error_screenshot(driver, "participant_error")
        return False


def time_to_minutes(time_str):
    """Convert time string like '6:30 PM' to minutes since midnight."""
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
    except Exception as e:
        logger.error(f"Error converting time '{time_str}': {e}")
        return 0


def select_best_time(available_times, preferred_hour, min_hour, max_hour):
    """Pick the best time slot: earliest after preferred, or latest in range."""
    if not available_times:
        return None

    min_minutes = min_hour * 60
    max_minutes = max_hour * 60
    valid_times = [t for t in available_times if min_minutes <= t[2] <= max_minutes]

    if not valid_times:
        logger.info(f"No times in range {min_hour}:00-{max_hour}:00")
        return None

    preferred_minutes = preferred_hour * 60
    after_preferred = [t for t in valid_times if t[2] >= preferred_minutes]

    if after_preferred:
        after_preferred.sort(key=lambda x: x[2])
        selected = after_preferred[0]
        logger.info(f"Selected earliest time after {preferred_hour}:00: {selected[0]}")
    else:
        valid_times.sort(key=lambda x: x[2], reverse=True)
        selected = valid_times[0]
        logger.info(f"No times after {preferred_hour}:00, selected latest: {selected[0]}")

    return selected


def get_courts_by_type(driver, court_type):
    """Find court cells matching the configured type (outdoor/indoor/both)."""
    cells = []

    if court_type in ['outdoor', 'both']:
        outdoor_cells = driver.find_elements(By.XPATH, "//td[.//b[text()='Outdoor']]")
        cells.extend([('Outdoor', cell) for cell in outdoor_cells])
        logger.info(f"Found {len(outdoor_cells)} outdoor court cells")

    if court_type in ['indoor', 'both']:
        indoor_cells = driver.find_elements(By.XPATH, "//td[.//b[text()='Indoor']]")
        cells.extend([('Indoor', cell) for cell in indoor_cells])
        logger.info(f"Found {len(indoor_cells)} indoor court cells")

    return cells


def _go_home(driver):
    driver.get("https://penntennis.clubautomation.com/member")
    time.sleep(2)


@retry_on_failure(max_attempts=2, delay=3, exceptions=(TimeoutException,))
def reserve_court(driver, target_date):
    """Reserve a court for the given date."""
    date_str = target_date.strftime("%m/%d/%Y")
    print_banner(f"Attempting: {target_date.strftime('%A, %B %d, %Y')}", "=")

    try:
        reserve_link = driver.find_element(By.LINK_TEXT, "Reserve a Court")
        safe_click(driver, reserve_link, "Reserve a Court link")

        wait = WebDriverWait(driver, config.BROWSER_TIMEOUT)
        wait.until(EC.presence_of_element_located((By.ID, "date")))
        time.sleep(2)

        date_input = driver.find_element(By.ID, "date")
        safe_send_keys(date_input, date_str, "date input")

        participant_added = add_participant(driver, config.PARTICIPANT)
        if not participant_added and config.PARTICIPANT:
            logger.warning("Failed to add participant, continuing anyway...")

        search_button = driver.find_element(By.CSS_SELECTOR, "button.btn-info")
        safe_click(driver, search_button, "search button")
        time.sleep(3)

        court_cells = get_courts_by_type(driver, config.COURT_TYPE)
        if not court_cells:
            logger.info(f"No {config.COURT_TYPE} courts available")
            _go_home(driver)
            return {"success": False, "date": target_date.strftime('%A, %B %d'),
                    "reason": f"No {config.COURT_TYPE} courts available"}

        available_times = []
        for court_type, cell in court_cells:
            time_links = cell.find_elements(By.XPATH, ".//a[@t]")
            for link in time_links:
                time_text = link.text.strip()
                if time_text and ('am' in time_text.lower() or 'pm' in time_text.lower()):
                    available_times.append((time_text, link, time_to_minutes(time_text), court_type))

        if not available_times:
            logger.info("No time slots available")
            _go_home(driver)
            return {"success": False, "date": target_date.strftime('%A, %B %d'),
                    "reason": "No times available"}

        selected = select_best_time(
            available_times, config.PREFERRED_HOUR, config.MIN_HOUR, config.MAX_HOUR
        )
        if not selected:
            logger.info("No suitable times in preferred range")
            _go_home(driver)
            return {"success": False, "date": target_date.strftime('%A, %B %d'),
                    "reason": f"No times in range {config.MIN_HOUR}:00-{config.MAX_HOUR}:00"}

        selected_time, selected_link, _, selected_court_type = selected
        logger.info(f"Clicking on {selected_court_type} court at {selected_time}...")
        safe_click(driver, selected_link, f"{selected_court_type} time slot")
        time.sleep(3)

        confirm_buttons = driver.find_elements(
            By.XPATH,
            "//button[contains(text(), 'Confirm') or contains(text(), 'Reserve') or contains(text(), 'Submit')]"
        )

        if confirm_buttons:
            logger.info("Clicking confirmation button...")
            safe_click(driver, confirm_buttons[0], "confirm button")
            time.sleep(3)
            logger.info(f"Reserved {selected_court_type} court at {selected_time}")
            success = True
        else:
            logger.warning("No confirmation button found")
            success = False

        _go_home(driver)
        return {"success": success, "date": target_date.strftime('%A, %B %d'),
                "time": selected_time, "court_type": selected_court_type}

    except Exception as e:
        logger.error(f"Error reserving court: {e}")
        save_error_screenshot(driver, f"reservation_error_{date_str}")
        _go_home(driver)
        return {"success": False, "date": target_date.strftime('%A, %B %d'),
                "reason": f"Error: {str(e)[:50]}"}


def send_email_summary(results):
    """Send an email summary of reservation results via Gmail SMTP."""
    if not config.EMAIL or not config.EMAIL_PASSWORD:
        logger.info("Email credentials not configured - skipping email")
        return

    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]

    body = "Penn Tennis Court Reservation Summary\n" + "=" * 50 + "\n\n"

    if successful:
        body += "SUCCESSFULLY BOOKED:\n" + "-" * 50 + "\n"
        for r in successful:
            body += f"  {r['date']}: {r.get('time', 'N/A')} ({r.get('court_type', 'Outdoor')})\n"
        body += "\n"

    if failed:
        body += "UNAVAILABLE:\n" + "-" * 50 + "\n"
        for r in failed:
            body += f"  {r['date']}: {r.get('reason', 'Unknown')}\n"
        body += "\n"

    body += f"\nTotal: {len(successful)} booked, {len(failed)} unavailable\n"
    if config.PARTICIPANT:
        body += f"Participant: {config.PARTICIPANT}\n"

    msg = MIMEMultipart()
    msg['From'] = config.EMAIL
    msg['To'] = config.EMAIL
    msg['Subject'] = f"Penn Tennis Reservation Summary - {datetime.now().strftime('%B %d, %Y')}"
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(config.EMAIL, config.EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info("Email summary sent successfully")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")


def main(args):
    if not validate_env_file():
        sys.exit(1)

    if args.headless:
        config.HEADLESS = True
    if args.participant is not None:
        config.PARTICIPANT = args.participant
    if args.days:
        config.DAYS_AHEAD = args.days

    config.print_config()
    driver = None

    try:
        with PerformanceTimer("Total execution"):
            driver = create_chrome_driver(headless=config.HEADLESS, timeout=config.BROWSER_TIMEOUT)
            login(driver)

            results = []
            for day_offset in range(config.DAYS_AHEAD):
                target_date = datetime.now() + timedelta(days=day_offset)
                results.append(reserve_court(driver, target_date))

            print_summary(results)
            send_email_summary(results)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if driver:
            save_error_screenshot(driver, "fatal_error")
            save_page_source(driver, "fatal_error")
        sys.exit(1)
    finally:
        if driver:
            driver.quit()
            logger.info("Browser closed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Penn Tennis Court Reservation Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python reserve_courts.py                          # Use .env settings
  python reserve_courts.py --headless               # Run without visible browser
  python reserve_courts.py --days 3                 # Only book 3 days ahead
  python reserve_courts.py --participant "Jane Doe" # Override participant
        """
    )
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    parser.add_argument('--days', type=int, help='Days ahead to book (overrides .env)')
    parser.add_argument('--participant', type=str, help='Participant name (overrides .env)')
    args = parser.parse_args()
    main(args)
