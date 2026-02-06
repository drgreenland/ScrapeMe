"""
Scraper for Nine.com.au NRL news.
Checks main NRL page plus Perth Bears and The Mole topic pages.
"""
from typing import Optional
from bs4 import BeautifulSoup
from .base import BaseScraper


class NineScraper(BaseScraper):
    """Scraper for Nine.com.au NRL news."""

    # Additional topic pages to check
    TOPIC_PAGES = [
        "https://www.nine.com.au/topic/perth-bears-6hjh",
        "https://www.nine.com.au/topic/the-mole-26f7",
    ]

    def get_article_urls(self) -> list[dict]:
        """Get article URLs from Nine NRL section and topic pages."""
        # Collect all URL -> title mappings, preferring non-empty titles
        url_titles = {}

        # Check main news URL and topic pages
        urls_to_check = [self.news_url] + self.TOPIC_PAGES

        for page_url in urls_to_check:
            html = self.fetch_page(page_url)
            if not html:
                continue

            soup = BeautifulSoup(html, "lxml")

            # Nine uses article links and h3 links for headlines
            for link in soup.select("article a, h3 a"):
                url = link.get("href", "")
                if not url:
                    continue

                # Make absolute URL
                url = self.make_absolute_url(url)

                # Filter to sport/nrl articles only
                if "/sport/nrl/" not in url:
                    continue

                # Skip live scores and non-article pages
                if any(x in url for x in ["/live-scores/", "/ladder/", "/draw/", "/fixtures/"]):
                    continue

                # Extract title
                title = self.clean_text(link.get_text())

                # Keep this URL if we don't have it yet, or if this has a better title
                if url not in url_titles or (title and len(title) > len(url_titles.get(url, ""))):
                    url_titles[url] = title

        # Convert to list, filtering out entries without titles
        articles = []
        for url, title in url_titles.items():
            if title and len(title) >= 10:
                articles.append({"url": url, "title": title})

        return articles

    def parse_article(self, url: str, html: str) -> Optional[dict]:
        """Parse Nine article content."""
        soup = BeautifulSoup(html, "lxml")

        # Title selectors
        title = self.extract_text_content(soup, [
            "h1.story__headline",
            "h1[data-testid='headline']",
            "article h1",
            ".article-header h1",
            "h1",
        ])

        if not title:
            return None

        # Summary/standfirst
        summary = self.extract_text_content(soup, [
            ".story__abstract",
            "[data-testid='abstract']",
            ".article-standfirst",
            ".lead",
            "article p:first-of-type",
        ])

        # Full content
        content_element = soup.select_one(
            ".story__content, [data-testid='article-content'], "
            ".article-body, .article-content, article .content"
        )

        full_text = ""
        if content_element:
            # Remove unwanted elements
            for unwanted in content_element.select(
                "script, style, .ad, .advertisement, .related, "
                ".social-share, aside, .sidebar, figure, .embed"
            ):
                unwanted.decompose()

            paragraphs = content_element.find_all("p")
            full_text = " ".join(
                self.clean_text(p.get_text()) for p in paragraphs if p.get_text().strip()
            )

        # Published date
        published_date = None
        date_element = soup.select_one(
            "time[datetime], [data-testid='timestamp'], "
            ".story__date, .article-date, .published"
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
