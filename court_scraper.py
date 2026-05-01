"""Court availability checker for Penn Tennis."""

import argparse
import sys
import time
from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import config
from utils import (
    logger, retry_on_failure, save_error_screenshot, create_chrome_driver,
    safe_click, safe_send_keys, print_banner, validate_env_file,
    PerformanceTimer
)


@retry_on_failure(max_attempts=3, delay=2)
def login(driver):
    """Login to Penn Tennis website."""
    logger.info("Logging in...")
    driver.get("https://penntennis.clubautomation.com/member")
    wait = WebDriverWait(driver, config.BROWSER_TIMEOUT)

    username_field = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
    )
    password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")

    safe_send_keys(username_field, config.USERNAME, "username")
    safe_send_keys(password_field, config.PASSWORD, "password")

    login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    safe_click(driver, login_button, "login button")

    time.sleep(3)
    logger.info("Login successful")


def _sort_times(times):
    """Sort time strings chronologically."""
    return sorted(
        set(times),
        key=lambda x: (
            int(x.split(':')[0]) % 12 + (12 if 'pm' in x.lower() else 0),
            int(x.split(':')[1][:2])
        )
    )


def _extract_times(cells):
    """Pull time slot text from court cells."""
    times = []
    for cell in cells:
        for link in cell.find_elements(By.XPATH, ".//a[@t]"):
            text = link.text.strip()
            if text and ('am' in text.lower() or 'pm' in text.lower()):
                times.append(text)
    return _sort_times(times)


def get_available_times(driver, days_ahead=7, show_indoor=True, show_outdoor=True):
    """Scrape available court times for the next N days."""
    reserve_link = driver.find_element(By.LINK_TEXT, "Reserve a Court")
    safe_click(driver, reserve_link, "Reserve a Court link")

    wait = WebDriverWait(driver, config.BROWSER_TIMEOUT)
    wait.until(EC.presence_of_element_located((By.ID, "date")))
    time.sleep(2)

    all_results = []

    for day_offset in range(days_ahead):
        target_date = datetime.now() + timedelta(days=day_offset)
        date_str = target_date.strftime("%m/%d/%Y")

        date_input = driver.find_element(By.ID, "date")
        safe_send_keys(date_input, date_str, "date input")

        search_button = driver.find_element(By.CSS_SELECTOR, "button.btn-info")
        safe_click(driver, search_button, "search button")
        time.sleep(3)

        print_banner(target_date.strftime('%A, %B %d, %Y'))

        if not driver.find_elements(By.TAG_NAME, "table"):
            print("No results found\n")
            continue

        result = {'date': target_date, 'indoor': [], 'outdoor': []}

        if show_indoor:
            cells = driver.find_elements(By.XPATH, "//td[.//b[text()='Indoor']]")
            result['indoor'] = _extract_times(cells)

        if show_outdoor:
            cells = driver.find_elements(By.XPATH, "//td[.//b[text()='Outdoor']]")
            result['outdoor'] = _extract_times(cells)

        if show_indoor:
            if result['indoor']:
                print(f"\n  Indoor ({len(result['indoor'])} slots): {', '.join(result['indoor'])}")
            else:
                print("\n  Indoor: None available")

        if show_outdoor:
            if result['outdoor']:
                print(f"\n  Outdoor ({len(result['outdoor'])} slots): {', '.join(result['outdoor'])}")
            else:
                print("\n  Outdoor: None available")

        total = len(result['indoor']) + len(result['outdoor'])
        print(f"\n  Total: {total} slots\n")

        all_results.append(result)

    return all_results


def print_summary(results):
    """Print overall availability summary."""
    print_banner("Summary", "=")
    total_indoor = sum(len(r['indoor']) for r in results)
    total_outdoor = sum(len(r['outdoor']) for r in results)
    print(f"\n  Days checked: {len(results)}")
    print(f"  Indoor slots: {total_indoor}")
    print(f"  Outdoor slots: {total_outdoor}")
    print(f"  Total: {total_indoor + total_outdoor}\n")


def main(args):
    if not validate_env_file():
        sys.exit(1)

    show_indoor = args.type in ['both', 'indoor']
    show_outdoor = args.type in ['both', 'outdoor']
    days = args.days or config.DAYS_AHEAD

    driver = None

    try:
        with PerformanceTimer("Court availability check"):
            driver = create_chrome_driver(headless=args.headless)
            login(driver)
            results = get_available_times(driver, days_ahead=days,
                                          show_indoor=show_indoor, show_outdoor=show_outdoor)
            print_summary(results)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}")
        if driver:
            save_error_screenshot(driver, "scraper_error")
        sys.exit(1)
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check Penn Tennis court availability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python court_scraper.py                    # Check all courts
  python court_scraper.py --type outdoor     # Only outdoor courts
  python court_scraper.py --days 3           # Check 3 days ahead
  python court_scraper.py --headless         # Run without browser window
        """
    )
    parser.add_argument('--type', choices=['both', 'indoor', 'outdoor'], default='both',
                        help='Court type to check (default: both)')
    parser.add_argument('--days', type=int, help='Days ahead to check (default: from .env)')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    args = parser.parse_args()
    main(args)
