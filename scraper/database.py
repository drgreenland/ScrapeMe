"""
Database operations for article storage.
"""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize the database schema."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                summary TEXT,
                full_text TEXT,
                published_date DATETIME,
                scraped_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                matched_keywords TEXT,
                relevance_score INTEGER,
                is_read INTEGER DEFAULT 0
            );

            CREATE INDEX IF NOT EXISTS idx_scraped_date ON articles(scraped_date DESC);
            CREATE INDEX IF NOT EXISTS idx_source ON articles(source);
            CREATE INDEX IF NOT EXISTS idx_relevance ON articles(relevance_score DESC);
            CREATE INDEX IF NOT EXISTS idx_is_read ON articles(is_read);
        """)


def article_exists(url: str) -> bool:
    """Check if an article URL already exists in the database."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT 1 FROM articles WHERE url = ?", (url,)
        )
        return cursor.fetchone() is not None


def insert_article(
    url: str,
    title: str,
    source: str,
    summary: Optional[str] = None,
    full_text: Optional[str] = None,
    published_date: Optional[datetime] = None,
    matched_keywords: Optional[list] = None,
    relevance_score: int = 1,
) -> Optional[int]:
    """
    Insert a new article into the database.
    Returns the article ID if inserted, None if URL already exists.
    """
    if article_exists(url):
        return None

    keywords_json = json.dumps(matched_keywords) if matched_keywords else None
    pub_date_str = published_date.isoformat() if published_date else None

    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO articles
            (url, title, source, summary, full_text, published_date, matched_keywords, relevance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (url, title, source, summary, full_text, pub_date_str, keywords_json, relevance_score)
        )
        return cursor.lastrowid


def get_articles(
    limit: int = 20,
    offset: int = 0,
    source: Optional[str] = None,
    unread_only: bool = False,
    min_relevance: Optional[int] = None,
) -> list[dict]:
    """
    Get articles with optional filtering.
    Returns list of article dictionaries.
    """
    query = "SELECT * FROM articles WHERE 1=1"
    params = []

    if source:
        query += " AND source = ?"
        params.append(source)

    if unread_only:
        query += " AND is_read = 0"

    if min_relevance:
        query += " AND relevance_score >= ?"
        params.append(min_relevance)

    query += " ORDER BY scraped_date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with get_db() as conn:
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()

    articles = []
    for row in rows:
        article = dict(row)
        if article.get("matched_keywords"):
            article["matched_keywords"] = json.loads(article["matched_keywords"])
        articles.append(article)

    return articles


def get_article_by_id(article_id: int) -> Optional[dict]:
    """Get a single article by ID."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT * FROM articles WHERE id = ?", (article_id,)
        )
        row = cursor.fetchone()

    if row:
        article = dict(row)
        if article.get("matched_keywords"):
            article["matched_keywords"] = json.loads(article["matched_keywords"])
        return article
    return None


def mark_as_read(article_id: int) -> bool:
    """Mark an article as read."""
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE articles SET is_read = 1 WHERE id = ?", (article_id,)
        )
        return cursor.rowcount > 0


def mark_as_unread(article_id: int) -> bool:
    """Mark an article as unread."""
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE articles SET is_read = 0 WHERE id = ?", (article_id,)
        )
        return cursor.rowcount > 0


def get_article_count(
    source: Optional[str] = None,
    unread_only: bool = False,
) -> int:
    """Get total article count with optional filtering."""
    query = "SELECT COUNT(*) FROM articles WHERE 1=1"
    params = []

    if source:
        query += " AND source = ?"
        params.append(source)

    if unread_only:
        query += " AND is_read = 0"

    with get_db() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchone()[0]


def get_sources() -> list[str]:
    """Get list of all sources that have articles."""
    with get_db() as conn:
        cursor = conn.execute(
            "SELECT DISTINCT source FROM articles ORDER BY source"
        )
        return [row[0] for row in cursor.fetchall()]


def get_stats() -> dict:
    """Get database statistics."""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
        unread = conn.execute("SELECT COUNT(*) FROM articles WHERE is_read = 0").fetchone()[0]

        sources_cursor = conn.execute(
            "SELECT source, COUNT(*) as count FROM articles GROUP BY source ORDER BY count DESC"
        )
        by_source = {row[0]: row[1] for row in sources_cursor.fetchall()}

    return {
        "total": total,
        "unread": unread,
        "read": total - unread,
        "by_source": by_source,
    }


# Initialize database when module is imported
init_database()
