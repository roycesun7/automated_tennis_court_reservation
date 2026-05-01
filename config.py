"""Configuration management and validation for Penn Tennis Scraper."""

import os
from dotenv import load_dotenv
import sys

load_dotenv()

class Config:
    """Configuration class with validation."""
    
    def __init__(self):
        """Initialize and validate configuration."""
        self.load_config()
        self.validate()
    
    def load_config(self):
        """Load configuration from environment variables."""
        # Required credentials
        self.USERNAME = os.getenv("USERNAME")
        self.PASSWORD = os.getenv("PASSWORD")
        
        # Optional settings with defaults
        self.PARTICIPANT = os.getenv("PARTICIPANT", "")
        self.PREFERRED_HOUR = int(os.getenv("PREFERRED_HOUR", "18"))
        self.MIN_HOUR = int(os.getenv("MIN_HOUR", "0"))
        self.MAX_HOUR = int(os.getenv("MAX_HOUR", "23"))
        self.COURT_TYPE = os.getenv("COURT_TYPE", "outdoor").lower()  # outdoor, indoor, both
        self.DAYS_AHEAD = int(os.getenv("DAYS_AHEAD", "7"))
        self.HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
        
        # Email settings (optional)
        self.EMAIL = os.getenv("EMAIL", "")
        self.EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
        
        # Browser settings
        self.BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "15"))
        self.RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", "3"))
        self.RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))
    
    def validate(self):
        """Validate configuration values."""
        errors = []
        
        # Check required fields
        if not self.USERNAME:
            errors.append("USERNAME is required in .env file")
        if not self.PASSWORD:
            errors.append("PASSWORD is required in .env file")
        
        # Validate hour ranges
        if not 0 <= self.PREFERRED_HOUR <= 23:
            errors.append(f"PREFERRED_HOUR must be between 0-23, got {self.PREFERRED_HOUR}")
        if not 0 <= self.MIN_HOUR <= 23:
            errors.append(f"MIN_HOUR must be between 0-23, got {self.MIN_HOUR}")
        if not 0 <= self.MAX_HOUR <= 23:
            errors.append(f"MAX_HOUR must be between 0-23, got {self.MAX_HOUR}")
        if self.MIN_HOUR > self.MAX_HOUR:
            errors.append(f"MIN_HOUR ({self.MIN_HOUR}) cannot be greater than MAX_HOUR ({self.MAX_HOUR})")
        
        # Validate court type
        if self.COURT_TYPE not in ['outdoor', 'indoor', 'both']:
            errors.append(f"COURT_TYPE must be 'outdoor', 'indoor', or 'both', got '{self.COURT_TYPE}'")
        
        # Validate days ahead
        if not 1 <= self.DAYS_AHEAD <= 14:
            errors.append(f"DAYS_AHEAD must be between 1-14, got {self.DAYS_AHEAD}")
        
        # Validate retry settings
        if self.RETRY_ATTEMPTS < 1:
            errors.append(f"RETRY_ATTEMPTS must be at least 1, got {self.RETRY_ATTEMPTS}")
        
        if errors:
            print("❌ Configuration Errors:")
            for error in errors:
                print(f"  - {error}")
            print("\nPlease check your .env file and fix the errors above.")
            sys.exit(1)
    
    def print_config(self):
        """Print current configuration (without sensitive data)."""
        print("\n" + "="*60)
        print("Configuration Settings")
        print("="*60)
        masked = self.USERNAME[:2] + "***" if self.USERNAME and len(self.USERNAME) > 2 else "***"
        print(f"Username: {masked}")
        print(f"Participant: {self.PARTICIPANT or 'Not set'}")
        print(f"Preferred Hour: {self.PREFERRED_HOUR}:00")
        print(f"Time Range: {self.MIN_HOUR}:00 - {self.MAX_HOUR}:00")
        print(f"Court Type: {self.COURT_TYPE}")
        print(f"Days Ahead: {self.DAYS_AHEAD}")
        print(f"Headless Mode: {self.HEADLESS}")
        print(f"Email Notifications: {'Enabled' if self.EMAIL else 'Disabled'}")
        print(f"Browser Timeout: {self.BROWSER_TIMEOUT}s")
        print(f"Retry Attempts: {self.RETRY_ATTEMPTS}")
        print("="*60 + "\n")


# Global config instance
config = Config()


