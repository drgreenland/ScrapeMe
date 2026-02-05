"""
Scraper for NRL.com official news.
"""
from typing import Optional
from bs4 import BeautifulSoup
from .base import BaseScraper


class NRLOfficialScraper(BaseScraper):
    """Scraper for official NRL.com news."""

    def get_article_urls(self) -> list[dict]:
        """Get article URLs from NRL.com news listing."""
        html = self.fetch_page(self.news_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        articles = []

        # NRL.com uses article cards with various class patterns
        article_selectors = [
            "article a[href*='/news/']",
            ".news-card a",
            ".article-card a",
            "a[href*='/news/'][href*='20']",  # URLs containing year
        ]

        seen_urls = set()
        for selector in article_selectors:
            for link in soup.select(selector):
                url = link.get("href", "")
                if not url or url in seen_urls:
                    continue

                url = self.make_absolute_url(url)
                if "/news/" not in url:
                    continue

                seen_urls.add(url)

                # Try to get title from link text or nearby heading
                title = ""
                heading = link.select_one("h2, h3, h4, .title, .headline")
                if heading:
                    title = self.clean_text(heading.get_text())
                elif link.get_text().strip():
                    title = self.clean_text(link.get_text())

                articles.append({"url": url, "title": title})

        return articles

    def parse_article(self, url: str, html: str) -> Optional[dict]:
        """Parse NRL.com article content."""
        soup = BeautifulSoup(html, "lxml")

        # Title selectors
        title = self.extract_text_content(soup, [
            "h1.article-title",
            "h1.headline",
            "article h1",
            "h1",
        ])

        if not title:
            return None

        # Summary/standfirst
        summary = self.extract_text_content(soup, [
            ".article-standfirst",
            ".article-summary",
            ".standfirst",
            "article p:first-of-type",
        ])

        # Full content
        content_element = soup.select_one(
            ".article-content, .article-body, article .content, .story-content"
        )
        full_text = ""
        if content_element:
            paragraphs = content_element.find_all("p")
            full_text = " ".join(
                self.clean_text(p.get_text()) for p in paragraphs
            )

        # Published date
        published_date = None
        date_element = soup.select_one(
            "time[datetime], .article-date, .published-date, .date"
        )
        if date_element:
            date_str = date_element.get("datetime") or date_element.get_text()
            published_date = self.parse_date(date_str)

        return {
            "title": title,
            "summary": summary,
            "full_text": full_text,
            "published_date": published_date,
        }
