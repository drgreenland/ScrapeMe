"""
Scraper for PerthNow (perthnow.com.au).
https://www.perthnow.com.au/sport/rugby-league
"""
from typing import Optional
from bs4 import BeautifulSoup
from .base import BaseScraper


class PerthNowScraper(BaseScraper):
    """Scraper for PerthNow news portal."""

    def get_article_urls(self) -> list[dict]:
        """Get article URLs from PerthNow sport/rugby-league section."""
        html = self.fetch_page(self.news_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        articles = []
        seen_urls = set()

        # PerthNow article patterns
        selectors = [
            "article a[href*='/sport/']",
            ".story-block a",
            ".article-card a",
            "a.story-link",
            ".headline a",
        ]

        for selector in selectors:
            for link in soup.select(selector):
                url = link.get("href", "")
                if not url or url in seen_urls:
                    continue

                url = self.make_absolute_url(url)

                # Filter out non-article URLs
                if any(x in url for x in ["/author/", "/video/", "/gallery/", "#", "/tag/"]):
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
        """Parse PerthNow article content."""
        soup = BeautifulSoup(html, "lxml")

        # Title
        title = self.extract_text_content(soup, [
            "h1.story-headline",
            "h1.article-title",
            "h1[itemprop='headline']",
            "article h1",
            "h1",
        ])

        if not title:
            return None

        # Summary/standfirst
        summary = self.extract_text_content(soup, [
            ".story-standfirst",
            ".article-standfirst",
            ".standfirst",
            "[itemprop='description']",
            "article p.lead",
        ])

        # Full content
        content_element = soup.select_one(
            ".story-content, .article-body, [itemprop='articleBody'], article .content"
        )
        full_text = ""
        if content_element:
            # Remove unwanted elements
            for unwanted in content_element.select("script, style, .ad, .paywall, aside, .related"):
                unwanted.decompose()

            paragraphs = content_element.find_all("p")
            full_text = " ".join(
                self.clean_text(p.get_text()) for p in paragraphs
            )

        # Published date
        published_date = None
        date_element = soup.select_one(
            "time[datetime], .publish-date, .article-date, [itemprop='datePublished']"
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
