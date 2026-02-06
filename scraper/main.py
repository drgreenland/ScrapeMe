#!/usr/bin/env python3
"""
Perth Bears News Scraper - Main orchestrator.

Runs all configured scrapers and stores articles in the database.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SOURCES, LOG_FILE, LOG_FORMAT, LOG_LEVEL
from scraper.database import insert_article, get_stats, init_database, set_last_checked
from scraper.sources import (
    NRLOfficialScraper,
    TheRoarScraper,
    TheWestScraper,
    PerthNowScraper,
    FoxSportsScraper,
    SMHScraper,
    TheAgeScraper,
    CodeSportsScraper,
    NewsNowScraper,
)


# Mapping of source keys to scraper classes
SCRAPER_CLASSES = {
    "nrl_official": NRLOfficialScraper,
    "theroar": TheRoarScraper,
    "thewest": TheWestScraper,
    "perthnow": PerthNowScraper,
    "foxsports": FoxSportsScraper,
    "smh": SMHScraper,
    "theage": TheAgeScraper,
    "codesports": CodeSportsScraper,
    "newsnow": NewsNowScraper,
}


def setup_logging():
    """Configure logging for the scraper."""
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout),
        ]
    )
    return logging.getLogger("scraper.main")


def run_scraper(source_key: str, source_config: dict, logger: logging.Logger) -> tuple[int, int]:
    """
    Run a single scraper.
    Returns (articles_found, articles_saved) tuple.
    """
    scraper_class = SCRAPER_CLASSES.get(source_key)
    if not scraper_class:
        logger.warning(f"No scraper class for source: {source_key}")
        return 0, 0

    try:
        scraper = scraper_class(source_config)
        articles = scraper.scrape()

        saved_count = 0
        for article in articles:
            article_id = insert_article(
                url=article["url"],
                title=article["title"],
                source=article["source"],
                summary=article.get("summary"),
                full_text=article.get("full_text"),
                published_date=article.get("published_date"),
                matched_keywords=article.get("matched_keywords"),
                relevance_score=article.get("relevance_score", 1),
            )
            if article_id:
                saved_count += 1
                logger.info(f"Saved new article: {article['title'][:50]}...")

        return len(articles), saved_count

    except Exception as e:
        logger.error(f"Error running scraper for {source_key}: {e}", exc_info=True)
        return 0, 0


def main():
    """Main entry point for the scraper."""
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info(f"Perth Bears News Scraper starting at {datetime.now()}")
    logger.info("=" * 60)

    # Initialize database
    init_database()

    # Track results
    total_found = 0
    total_saved = 0
    errors = []

    # Run each enabled scraper
    for source_key, source_config in SOURCES.items():
        if not source_config.get("enabled", True):
            logger.info(f"Skipping disabled source: {source_config['name']}")
            continue

        logger.info(f"Processing source: {source_config['name']}")

        try:
            found, saved = run_scraper(source_key, source_config, logger)
            total_found += found
            total_saved += saved
            logger.info(f"  Found: {found}, Saved: {saved}")

        except Exception as e:
            error_msg = f"Failed to process {source_config['name']}: {e}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)

    # Log summary
    logger.info("=" * 60)
    logger.info("Scrape complete!")
    logger.info(f"  Total articles found: {total_found}")
    logger.info(f"  New articles saved: {total_saved}")
    logger.info(f"  Duplicates skipped: {total_found - total_saved}")

    if errors:
        logger.warning(f"  Errors encountered: {len(errors)}")
        for error in errors:
            logger.warning(f"    - {error}")

    # Log database stats
    stats = get_stats()
    logger.info(f"  Database total: {stats['total']} articles ({stats['unread']} unread)")
    logger.info("=" * 60)

    # Record that we checked for updates
    set_last_checked()

    # Return exit code (0 = success, 1 = partial failure, 2 = complete failure)
    if errors and total_saved == 0:
        return 2
    elif errors:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
