"""
Scraper for NewsNow NRL aggregator (newsnow.com/au/Sport/NRL).
NewsNow aggregates articles from multiple sources.
Links redirect via JavaScript to actual articles when clicked.
"""
import re
from typing import Optional

from bs4 import BeautifulSoup
from .base import BaseScraper


class NewsNowScraper(BaseScraper):
    """Scraper for NewsNow NRL news aggregator."""

    def get_article_urls(self) -> list[dict]:
        """Get article URLs from NewsNow NRL section."""
        html = self.fetch_page(self.news_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        articles = []
        seen_urls = set()

        # NewsNow uses links like href="https://c.newsnow.com/A/..."
        for link in soup.find_all("a", href=re.compile(r"c\.newsnow\.com/A/")):
            newsnow_url = link.get("href", "")
            if not newsnow_url or newsnow_url in seen_urls:
                continue

            seen_urls.add(newsnow_url)

            # Extract title from link text
            title = self.clean_text(link.get_text())
            if not title or len(title) < 10:
                continue

            # Use the NewsNow redirect URL directly - it will redirect when clicked
            articles.append({"url": newsnow_url, "title": title})

        return articles

    def parse_article(self, url: str, html: str) -> Optional[dict]:
        """
        NewsNow links redirect via JavaScript, so we can't parse content.
        Return None to use title-only matching.
        """
        return None

    def scrape(self) -> list[dict]:
        """
        Override scrape to use title-only matching since NewsNow
        uses JavaScript redirects we can't follow.
        """
        self.logger.info(f"Starting scrape for {self.source_name}")
        articles = []

        # Get article URLs from listing
        article_refs = self.get_article_urls()
        self.logger.info(f"Found {len(article_refs)} article URLs")

        for ref in article_refs:
            url = ref["url"]
            title = ref.get("title", "")

            if not title:
                continue

            # Check keywords in title only (can't access full content)
            matched_keywords, relevance = self.check_keywords(title)

            if not matched_keywords:
                continue

            # Build article dict with title-only data
            article = {
                "url": url,
                "title": title,
                "source": self.source_name,
                "summary": None,
                "full_text": None,
                "published_date": None,
                "matched_keywords": matched_keywords,
                "relevance_score": relevance,
            }

            articles.append(article)
            self.logger.info(f"Found relevant article: {title[:60]}...")

        self.logger.info(f"Completed scrape for {self.source_name}: {len(articles)} relevant articles")
        return articles
