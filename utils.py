"""Utility functions for Penn Tennis Scraper."""

import os
import time
import logging
from datetime import datetime
from functools import wraps
from selenium.webdriver.chrome.options import Options
from selenium import webdriver


def setup_logging(log_file="scraper.log"):
    """Configure logging to both file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


logger = setup_logging()


def retry_on_failure(max_attempts=3, delay=2, exceptions=(Exception,)):
    """Decorator to retry a function on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts >= max_attempts:
                        logger.error(f"Failed after {max_attempts} attempts: {e}")
                        raise
                    logger.warning(f"Attempt {attempts} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
        return wrapper
    return decorator


def save_error_screenshot(driver, prefix="error"):
    """Save a screenshot when an error occurs."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.png"
        driver.save_screenshot(filename)
        logger.info(f"Screenshot saved: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Failed to save screenshot: {e}")
        return None


def save_page_source(driver, prefix="page"):
    """Save page source HTML for debugging."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info(f"Page source saved: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Failed to save page source: {e}")
        return None


def create_chrome_driver(headless=False, timeout=15):
    """Create a Chrome WebDriver with optimal settings."""
    options = Options()

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        logger.info("Running in headless mode")

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(timeout)
        logger.info("Chrome driver created successfully")
        return driver
    except Exception as e:
        logger.error(f"Failed to create Chrome driver: {e}")
        raise


def safe_click(driver, element, description="element"):
    """Click an element with error handling and screenshot on failure."""
    try:
        element.click()
        return True
    except Exception as e:
        logger.error(f"Failed to click {description}: {e}")
        save_error_screenshot(driver, f"click_error_{description}")
        raise


def safe_send_keys(element, text, description="element"):
    """Clear and type into an element with error handling."""
    try:
        element.clear()
        element.send_keys(text)
        return True
    except Exception as e:
        logger.error(f"Failed to send keys to {description}: {e}")
        raise


def print_banner(text, char="="):
    """Print a formatted banner line."""
    width = 60
    print("\n" + char * width)
    print(text.center(width))
    print(char * width)


class PerformanceTimer:
    """Context manager for timing operations."""

    def __init__(self, operation_name):
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = time.time() - self.start_time
        logger.info(f"{self.operation_name} completed in {elapsed:.2f}s")


def validate_env_file():
    """Check if .env file exists and warn if not."""
    if not os.path.exists(".env"):
        logger.error(".env file not found! Run: cp .env.example .env")
        return False
    return True


def print_summary(results):
    """Print a formatted summary of reservation results."""
    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]

    print_banner("Reservation Summary")

    if successful:
        print("\n  Booked:")
        for r in successful:
            print(f"    {r['date']}: {r.get('time', 'N/A')} ({r.get('court_type', 'Outdoor')})")

    if failed:
        print("\n  Unavailable:")
        for r in failed:
            print(f"    {r['date']}: {r.get('reason', 'Unknown error')}")

    print(f"\n  Total: {len(successful)} booked, {len(failed)} unavailable")
    print("=" * 60 + "\n")
