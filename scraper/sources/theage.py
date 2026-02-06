"""
Scraper for The Age (theage.com.au).
https://www.theage.com.au/sport/nrl
"""
from typing import Optional
from bs4 import BeautifulSoup
from .base import BaseScraper


class TheAgeScraper(BaseScraper):
    """Scraper for The Age NRL news."""

    def get_article_urls(self) -> list[dict]:
        """Get article URLs from The Age NRL section."""
        html = self.fetch_page(self.news_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        articles = []
        seen_urls = set()

        # The Age uses Nine network patterns (similar to SMH)
        selectors = [
            "article a[href*='/sport/nrl/']",
            "[data-testid='article-card'] a",
            ".story-block a",
            "a[href*='/article/']",
            ".headline a",
        ]

        for selector in selectors:
            for link in soup.select(selector):
                url = link.get("href", "")
                if not url or url in seen_urls:
                    continue

                url = self.make_absolute_url(url)

                # Filter to sport/NRL articles
                if "/sport/" not in url:
                    continue

                # Filter out non-article URLs
                if any(x in url for x in ["/video/", "/live/", "/gallery/", "#"]):
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
        """Parse The Age article content."""
        soup = BeautifulSoup(html, "lxml")

        # Title
        title = self.extract_text_content(soup, [
            "h1[data-testid='headline']",
            "h1.article-title",
            "h1[itemprop='headline']",
            "article h1",
            "h1",
        ])

        if not title:
            return None

        # Summary/standfirst
        summary = self.extract_text_content(soup, [
            "[data-testid='standfirst']",
            ".article-standfirst",
            ".standfirst",
            "[itemprop='description']",
            "article p.lead",
        ])

        # Full content - may be limited by paywall
        content_element = soup.select_one(
            "[data-testid='article-body'], .article-body, [itemprop='articleBody'], article .content"
        )
        full_text = ""
        if content_element:
            # Remove unwanted elements
            for unwanted in content_element.select("script, style, .ad, .paywall, aside, .related, figure"):
                unwanted.decompose()

            paragraphs = content_element.find_all("p")
            full_text = " ".join(
                self.clean_text(p.get_text()) for p in paragraphs
            )

        # Published date
        published_date = None
        date_element = soup.select_one(
            "time[datetime], [data-testid='publish-date'], .publish-date, [itemprop='datePublished']"
        )
        if date_element:
            date_str = date_element.get("datetime") or date_element.get("content") or date_element.get_text()
            published_date = self.parse_date(date_str)

        return {
            "title": title,
            "summary": summary,
            "full_text": full_text,
            "published_date": published_date,
        }
