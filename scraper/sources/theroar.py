"""
Scraper for The Roar (theroar.com.au).
"""
from typing import Optional
from bs4 import BeautifulSoup
from .base import BaseScraper


class TheRoarScraper(BaseScraper):
    """Scraper for The Roar rugby league news."""

    def get_article_urls(self) -> list[dict]:
        """Get article URLs from The Roar rugby league section."""
        html = self.fetch_page(self.news_url)
        if not html:
            return []

        soup = BeautifulSoup(html, "lxml")
        articles = []
        seen_urls = set()

        # The Roar article link patterns
        for link in soup.select("article a, .article-card a, a.article-link, .post-item a"):
            url = link.get("href", "")
            if not url or url in seen_urls:
                continue

            url = self.make_absolute_url(url)

            # Filter out non-article URLs
            if any(x in url for x in ["/author/", "/tag/", "/category/", "#"]):
                continue

            seen_urls.add(url)

            # Extract title
            title = ""
            heading = link.select_one("h2, h3, h4, .title")
            if heading:
                title = self.clean_text(heading.get_text())
            elif link.get_text().strip():
                title = self.clean_text(link.get_text())

            if title:
                articles.append({"url": url, "title": title})

        return articles

    def parse_article(self, url: str, html: str) -> Optional[dict]:
        """Parse The Roar article content."""
        soup = BeautifulSoup(html, "lxml")

        # Title
        title = self.extract_text_content(soup, [
            "h1.entry-title",
            "h1.article-title",
            "article h1",
            ".post-title",
            "h1",
        ])

        if not title:
            return None

        # Summary - The Roar often uses a lead paragraph
        summary = self.extract_text_content(soup, [
            ".article-standfirst",
            ".entry-content > p:first-of-type",
            ".lead",
            "article p:first-of-type",
        ])

        # Full content
        content_element = soup.select_one(
            ".entry-content, .article-content, .post-content, article .content"
        )
        full_text = ""
        if content_element:
            # Remove unwanted elements
            for unwanted in content_element.select("script, style, .ad, .advertisement, .related-posts"):
                unwanted.decompose()

            paragraphs = content_element.find_all("p")
            full_text = " ".join(
                self.clean_text(p.get_text()) for p in paragraphs
            )

        # Published date
        published_date = None
        date_element = soup.select_one(
            "time[datetime], .entry-date, .post-date, .published"
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
