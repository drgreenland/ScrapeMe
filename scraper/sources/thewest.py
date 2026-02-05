"""
Scraper for The West Australian (thewest.com.au).
"""
from typing import Optional
from bs4 import BeautifulSoup
from .base import BaseScraper


class TheWestScraper(BaseScraper):
    """Scraper for The West Australian newspaper."""

    def get_article_urls(self) -> list[dict]:
        """Get article URLs from The West Australian sport/rugby-league section."""
        html = self.fetch_page(self.news_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        articles = []
        seen_urls = set()

        # The West uses various article card patterns
        selectors = [
            "article a[href*='/sport/']",
            ".story-card a",
            ".article-card a",
            "a[data-testid='story-link']",
            ".headline a",
        ]

        for selector in selectors:
            for link in soup.select(selector):
                url = link.get("href", "")
                if not url or url in seen_urls:
                    continue

                url = self.make_absolute_url(url)

                # Filter out non-article URLs
                if any(x in url for x in ["/author/", "/video/", "/gallery/", "#"]):
                    continue

                seen_urls.add(url)

                # Extract title
                title = ""
                heading = link.select_one("h1, h2, h3, h4, .headline, .title")
                if heading:
                    title = self.clean_text(heading.get_text())
                elif link.get("title"):
                    title = self.clean_text(link.get("title"))
                elif link.get_text().strip():
                    title = self.clean_text(link.get_text())

                if title:
                    articles.append({"url": url, "title": title})

        return articles

    def parse_article(self, url: str, html: str) -> Optional[dict]:
        """Parse The West Australian article content."""
        soup = BeautifulSoup(html, "lxml")

        # Title
        title = self.extract_text_content(soup, [
            "h1[data-testid='headline']",
            "h1.story-headline",
            "h1.article-title",
            "article h1",
            "h1",
        ])

        if not title:
            return None

        # Summary/standfirst
        summary = self.extract_text_content(soup, [
            "[data-testid='standfirst']",
            ".story-standfirst",
            ".article-standfirst",
            ".standfirst",
            "article p.lead",
        ])

        # Full content - The West may have paywall
        # We'll get what's freely available
        content_element = soup.select_one(
            "[data-testid='article-body'], .story-content, .article-body, article .content"
        )
        full_text = ""
        if content_element:
            # Remove unwanted elements
            for unwanted in content_element.select("script, style, .ad, .paywall-prompt, aside"):
                unwanted.decompose()

            paragraphs = content_element.find_all("p")
            full_text = " ".join(
                self.clean_text(p.get_text()) for p in paragraphs
            )

        # Published date
        published_date = None
        date_element = soup.select_one(
            "time[datetime], [data-testid='publish-date'], .publish-date, .article-date"
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
