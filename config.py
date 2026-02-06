"""
Perth Bears News Scraper - Configuration
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Database
DATABASE_PATH = DATA_DIR / "articles.db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# HTTP Settings
REQUEST_TIMEOUT = 30  # seconds
MIN_DELAY_BETWEEN_REQUESTS = 3  # seconds
MAX_DELAY_BETWEEN_REQUESTS = 5  # seconds
MAX_RETRIES = 3

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
]

# Keywords configuration
KEYWORDS = {
    # Primary keywords - must match for article to be scraped
    "primary": [
        "Perth Bears",
        "Mal Meninga",
        "NRL",  # TEMP: Remove after testing - too broad
    ],
    # Secondary keywords - lower relevance score
    "secondary": [
        "NRL expansion",
        "Western Australia NRL",
        "WA NRL",
        "Mal Meninga",
        "North Sydney Bears",
        "Perth NRL",
    ],
}

# News sources configuration
SOURCES = {
    "nrl_official": {
        "name": "NRL.com",
        "base_url": "https://www.nrl.com",
        "news_url": "https://www.nrl.com/news/",
        "enabled": True,
        "priority": 2,  # Major NRL coverage
    },
    "theroar": {
        "name": "The Roar",
        "base_url": "https://www.theroar.com.au",
        "news_url": "https://www.theroar.com.au/rugby-league/",
        "enabled": True,
        "priority": 2,
    },
    "thewest": {
        "name": "The West Australian",
        "base_url": "https://thewest.com.au",
        "news_url": "https://thewest.com.au/sport/rugby-league",
        "enabled": True,
        "priority": 1,  # Perth-focused
    },
    "perthnow": {
        "name": "PerthNow",
        "base_url": "https://www.perthnow.com.au",
        "news_url": "https://www.perthnow.com.au/sport/rugby-league",
        "enabled": True,
        "priority": 1,
    },
    "foxsports": {
        "name": "Fox Sports",
        "base_url": "https://www.foxsports.com.au",
        "news_url": "https://www.foxsports.com.au/nrl",
        "enabled": True,
        "priority": 2,
    },
    "smh": {
        "name": "Sydney Morning Herald",
        "base_url": "https://www.smh.com.au",
        "news_url": "https://www.smh.com.au/sport/nrl",
        "enabled": True,
        "priority": 3,  # National
    },
    "theage": {
        "name": "The Age",
        "base_url": "https://www.theage.com.au",
        "news_url": "https://www.theage.com.au/sport/nrl",
        "enabled": True,
        "priority": 3,
    },
    "codesports": {
        "name": "CODE Sports",
        "base_url": "https://www.codesports.com.au",
        "news_url": "https://www.codesports.com.au/nrl",
        "enabled": True,
        "priority": 2,
    },
}

# Logging configuration
LOG_FILE = LOGS_DIR / "scraper.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = "INFO"

# Web viewer settings
VIEWER_HOST = "0.0.0.0"  # Bind to all interfaces
VIEWER_PORT = 5050       # Avoid 5000 (used by macOS AirPlay)
ARTICLES_PER_PAGE = 20
