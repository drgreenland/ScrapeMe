#!/usr/bin/env python3
"""
Perth Bears News Viewer - Web interface for viewing scraped articles.
"""
import sys
import threading
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template, request, redirect, url_for, jsonify
from config import VIEWER_HOST, VIEWER_PORT, ARTICLES_PER_PAGE
from scraper.database import (
    get_articles,
    get_article_by_id,
    mark_as_read,
    mark_as_unread,
    get_article_count,
    get_sources,
    get_stats,
    get_last_checked,
)

app = Flask(__name__)

# Scraper status tracking
scraper_status = {
    "running": False,
    "last_result": None,
    "last_run": None,
}


@app.route("/")
def index():
    """Main article listing page."""
    # Get query parameters
    page = request.args.get("page", 1, type=int)
    source = request.args.get("source", None)
    unread_only = request.args.get("unread", "false").lower() == "true"
    min_relevance = request.args.get("relevance", None, type=int)

    # Calculate offset
    offset = (page - 1) * ARTICLES_PER_PAGE

    # Get articles
    articles = get_articles(
        limit=ARTICLES_PER_PAGE,
        offset=offset,
        source=source,
        unread_only=unread_only,
        min_relevance=min_relevance,
    )

    # Get total count for pagination
    total_count = get_article_count(source=source, unread_only=unread_only)
    total_pages = (total_count + ARTICLES_PER_PAGE - 1) // ARTICLES_PER_PAGE

    # Get available sources for filter
    sources = get_sources()

    # Get stats
    stats = get_stats()
    last_checked = get_last_checked()

    return render_template(
        "index.html",
        articles=articles,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
        sources=sources,
        current_source=source,
        unread_only=unread_only,
        min_relevance=min_relevance,
        stats=stats,
        last_checked=last_checked,
    )


@app.route("/article/<int:article_id>")
def view_article(article_id):
    """View a single article and mark as read."""
    article = get_article_by_id(article_id)
    if not article:
        return "Article not found", 404

    # Mark as read when viewed
    mark_as_read(article_id)

    return render_template("article.html", article=article)


@app.route("/api/mark-read/<int:article_id>", methods=["POST"])
def api_mark_read(article_id):
    """API endpoint to mark article as read."""
    success = mark_as_read(article_id)
    return jsonify({"success": success})


@app.route("/api/mark-unread/<int:article_id>", methods=["POST"])
def api_mark_unread(article_id):
    """API endpoint to mark article as unread."""
    success = mark_as_unread(article_id)
    return jsonify({"success": success})


@app.route("/api/stats")
def api_stats():
    """API endpoint for database statistics."""
    return jsonify(get_stats())


@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    """API endpoint to trigger a manual scrape."""
    if scraper_status["running"]:
        return jsonify({"success": False, "message": "Scraper already running"})

    def run_scraper():
        scraper_status["running"] = True
        scraper_status["last_result"] = None
        from datetime import datetime
        try:
            # Import and run scraper directly
            from scraper.main import main as run_main_scraper
            exit_code = run_main_scraper()

            scraper_status["last_result"] = {
                "success": exit_code == 0,
                "output": "Scraper completed",
                "error": "" if exit_code == 0 else f"Exit code: {exit_code}",
            }
        except Exception as e:
            scraper_status["last_result"] = {
                "success": False,
                "output": "",
                "error": str(e),
            }
        finally:
            scraper_status["running"] = False
            scraper_status["last_run"] = datetime.now().isoformat()

    thread = threading.Thread(target=run_scraper, daemon=True)
    thread.start()

    return jsonify({"success": True, "message": "Scraper started"})


@app.route("/api/scrape/status")
def api_scrape_status():
    """API endpoint to check scraper status."""
    return jsonify(scraper_status)


@app.template_filter("format_date")
def format_date(value):
    """Format datetime for display."""
    if not value:
        return "Unknown"
    if isinstance(value, str):
        from dateutil import parser
        try:
            value = parser.parse(value)
        except (ValueError, TypeError):
            return value
    return value.strftime("%d %b %Y, %H:%M")


@app.template_filter("truncate_text")
def truncate_text(value, length=200):
    """Truncate text to specified length."""
    if not value:
        return ""
    if len(value) <= length:
        return value
    return value[:length].rsplit(" ", 1)[0] + "..."


def main():
    """Run the Flask development server."""
    print(f"Starting Perth Bears News Viewer at http://{VIEWER_HOST}:{VIEWER_PORT}")
    app.run(host=VIEWER_HOST, port=VIEWER_PORT, debug=True, use_reloader=False)


if __name__ == "__main__":
    main()
