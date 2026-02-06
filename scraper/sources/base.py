"""
Base scraper class with common functionality.
"""
import logging
import random
import re
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config import (
    USER_AGENTS,
    REQUEST_TIMEOUT,
    MIN_DELAY_BETWEEN_REQUESTS,
    MAX_DELAY_BETWEEN_REQUESTS,
    MAX_RETRIES,
    KEYWORDS,
)


class BaseScraper(ABC):
    """Abstract base class for news scrapers."""

    def __init__(self, source_config: dict):
        self.source_name = source_config["name"]
        self.base_url = source_config["base_url"]
        self.news_url = source_config["news_url"]
        self.priority = source_config.get("priority", 2)
        self.session = requests.Session()
        self.logger = logging.getLogger(f"scraper.{self.__class__.__name__}")
        self._last_request_time = 0

    def _get_headers(self) -> dict:
        """Get request headers with rotated User-Agent."""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-AU,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def _rate_limit(self):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request_time
        delay = random.uniform(MIN_DELAY_BETWEEN_REQUESTS, MAX_DELAY_BETWEEN_REQUESTS)
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_request_time = time.time()

    def fetch_page(self, url: str, retries: int = MAX_RETRIES) -> Optional[str]:
        """
        Fetch a page with retry logic and rate limiting.
        Returns HTML content or None on failure.
        """
        self._rate_limit()

        for attempt in range(retries):
            try:
                self.logger.debug(f"Fetching: {url} (attempt {attempt + 1})")
                response = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True,
                )
                response.raise_for_status()
                return response.text

            except requests.RequestException as e:
                self.logger.warning(f"Request failed for {url}: {e}")
                if attempt < retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    self.logger.info(f"Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)

        self.logger.error(f"Failed to fetch {url} after {retries} attempts")
        return None

    def make_absolute_url(self, url: str) -> str:
        """Convert relative URL to absolute."""
        if url.startswith("http"):
            return url
        return urljoin(self.base_url, url)

    # Minimum word length for partial keyword matching
    # Words shorter than this won't match individually (e.g., "Mal", "NRL", "WA")
    MIN_PARTIAL_WORD_LENGTH = 5

    def _check_keyword(self, keyword: str, text_lower: str) -> bool:
        """
        Check if a keyword matches the text.
        For multi-word keywords, also matches if any individual word (5+ chars) is found.
        """
        keyword_lower = keyword.lower()

        # Check exact phrase match first
        if keyword_lower in text_lower:
            return True

        # For multi-word keywords, check individual words
        words = keyword_lower.split()
        if len(words) > 1:
            for word in words:
                if len(word) >= self.MIN_PARTIAL_WORD_LENGTH and word in text_lower:
                    return True

        return False

    def check_keywords(self, text: str) -> tuple[list[str], int]:
        """
        Check text against configured keywords.
        Returns (matched_keywords, relevance_score).
        Score: 2 for primary match, 1 for secondary only.

        For multi-word keywords like "Mal Meninga", also matches individual
        words if they're 5+ characters (e.g., "Meninga" matches).
        """
        if not text:
            return [], 0

        text_lower = text.lower()
        matched = []

        # Check primary keywords first
        for keyword in KEYWORDS["primary"]:
            if self._check_keyword(keyword, text_lower):
                matched.append(keyword)

        has_primary = len(matched) > 0

        # Check secondary keywords
        for keyword in KEYWORDS["secondary"]:
            if self._check_keyword(keyword, text_lower):
                matched.append(keyword)

        if not matched:
            return [], 0

        relevance = 2 if has_primary else 1
        return matched, relevance

    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def extract_text_content(self, soup: BeautifulSoup, selectors: list[str]) -> Optional[str]:
        """Extract text from first matching selector."""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return self.clean_text(element.get_text())
        return None

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats. Override in subclass for site-specific formats."""
        from dateutil import parser
        if not date_str:
            return None
        try:
            return parser.parse(date_str, fuzzy=True)
        except (ValueError, TypeError):
            self.logger.debug(f"Could not parse date: {date_str}")
            return None

    @abstractmethod
    def get_article_urls(self) -> list[dict]:
        """
        Get list of article URLs from news listing page.
        Returns list of dicts with at least 'url' key, optionally 'title'.
        """
        pass

    @abstractmethod
    def parse_article(self, url: str, html: str) -> Optional[dict]:
        """
        Parse article content from HTML.
        Returns dict with keys: title, summary, full_text, published_date
        Or None if parsing fails.
        """
        pass

    def scrape(self) -> list[dict]:
        """
        Main scraping method.
        Returns list of article dicts ready for database insertion.
        """
        self.logger.info(f"Starting scrape for {self.source_name}")
        articles = []

        # Get article URLs from listing
        article_refs = self.get_article_urls()
        self.logger.info(f"Found {len(article_refs)} article URLs")

        for ref in article_refs:
            url = ref["url"]
            preliminary_title = ref.get("title", "")

            # Check keywords in title first (quick filter)
            matched_keywords, relevance = self.check_keywords(preliminary_title)

            # If no match in title, we need to fetch and check content
            # But only if we have a preliminary title to check
            if not matched_keywords and preliminary_title:
                self.logger.debug(f"Skipping (no keyword match in title): {preliminary_title}")
                continue

            # Fetch full article
            html = self.fetch_page(url)
            if not html:
                continue

            # Parse article content
            article_data = self.parse_article(url, html)
            if not article_data:
                self.logger.warning(f"Failed to parse article: {url}")
                continue

            # Check keywords in full content
            full_text = f"{article_data.get('title', '')} {article_data.get('summary', '')} {article_data.get('full_text', '')}"
            matched_keywords, relevance = self.check_keywords(full_text)

            if not matched_keywords:
                self.logger.debug(f"Skipping (no keyword match in content): {url}")
                continue

            # Build final article dict
            article = {
                "url": url,
                "title": article_data.get("title", preliminary_title),
                "source": self.source_name,
                "summary": article_data.get("summary"),
                "full_text": article_data.get("full_text"),
                "published_date": article_data.get("published_date"),
                "matched_keywords": matched_keywords,
                "relevance_score": relevance,
            }

            articles.append(article)
            self.logger.info(f"Found relevant article: {article['title'][:60]}...")

        self.logger.info(f"Completed scrape for {self.source_name}: {len(articles)} relevant articles")
        return articles
