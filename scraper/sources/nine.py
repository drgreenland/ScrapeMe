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
        "https://www.nine.com.au/topic/the-mole-26f7",
    ]

    # Perth Bears topic page - articles here are auto-included
    PERTH_BEARS_PAGE = "https://www.nine.com.au/topic/perth-bears-6hjh"

    def get_article_urls(self) -> list[dict]:
        """Get article URLs from Nine NRL section and topic pages."""
        # Collect all URL -> title mappings, preferring non-empty titles
        url_titles = {}
        # Track URLs from Perth Bears page for auto-inclusion
        perth_bears_urls = set()

        # Check main news URL, topic pages, and Perth Bears page
        urls_to_check = [self.news_url] + self.TOPIC_PAGES + [self.PERTH_BEARS_PAGE]

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

                # Track if this URL came from Perth Bears page
                if page_url == self.PERTH_BEARS_PAGE:
                    perth_bears_urls.add(url)

        # Convert to list, filtering out entries without titles
        articles = []
        for url, title in url_titles.items():
            if title and len(title) >= 10:
                articles.append({
                    "url": url,
                    "title": title,
                    "from_perth_bears_page": url in perth_bears_urls,
                })

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

    def scrape(self) -> list[dict]:
        """
        Override scrape to auto-include articles from Perth Bears topic page.
        """
        self.logger.info(f"Starting scrape for {self.source_name}")
        articles = []

        # Get article URLs from listing
        article_refs = self.get_article_urls()
        self.logger.info(f"Found {len(article_refs)} article URLs")

        for ref in article_refs:
            url = ref["url"]
            preliminary_title = ref.get("title", "")
            from_perth_bears = ref.get("from_perth_bears_page", False)

            # Check keywords in title first (quick filter)
            matched_keywords, relevance = self.check_keywords(preliminary_title)

            # Auto-include articles from Perth Bears page
            if from_perth_bears and not matched_keywords:
                matched_keywords = ["Perth Bears (topic)"]
                relevance = 2  # Primary relevance

            # If no match in title and not from Perth Bears page, skip
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

            # Check keywords in full content (unless already matched from Perth Bears page)
            if not from_perth_bears:
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
