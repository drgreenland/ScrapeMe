# Perth Bears News Scraper

A Python web scraper that monitors Australian newspapers for Perth Bears Rugby League news, stores articles in SQLite, and displays them via a local web interface.

**Target:** Perth Bears - NRL expansion team (joining 2027), coached by Mal Meninga

## Features

- Scrapes multiple Australian news sources for Perth Bears coverage
- Keyword matching with primary/secondary relevance scoring
- SQLite storage with deduplication
- Mobile-friendly web interface
- CRON-based scheduled scraping
- Read/unread tracking

## News Sources

### Priority 1: Perth-Focused
- The West Australian (thewest.com.au)
- PerthNow (perthnow.com.au)

### Priority 2: Major NRL Coverage
- NRL.com (official)
- Fox Sports
- The Roar
- CODE Sports

### Priority 3: National Newspapers
- Sydney Morning Herald
- The Age

## Installation

### 1. Clone and Setup

```bash
cd /path/to/ScrapeMe
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Initial Scrape

```bash
python scraper/main.py
```

### 3. Start Web Viewer

```bash
python viewer/server.py
```

Then open http://127.0.0.1:5050 in your browser.

### 4. Setup Scheduled Scraping (Optional)

```bash
./setup_cron.sh
```

This configures the scraper to run every 4 hours from 6am to 10pm.

## Project Structure

```
ScrapeMe/
├── scraper/
│   ├── main.py              # Orchestrates all scrapers
│   ├── database.py          # SQLite operations
│   └── sources/             # One module per news source
│       ├── base.py          # Abstract base scraper
│       ├── nrl_official.py
│       ├── theroar.py
│       ├── thewest.py
│       └── ...
├── viewer/
│   ├── server.py            # Flask web server
│   ├── templates/           # HTML templates
│   └── static/              # CSS styles
├── data/
│   └── articles.db          # SQLite database
├── logs/
│   └── scraper.log          # Scraper logs
├── config.py                # Configuration
├── requirements.txt
├── setup_cron.sh
└── README.md
```

## Configuration

Edit `config.py` to customize:

- **Keywords**: Primary and secondary search terms
- **Sources**: Enable/disable news sources
- **Rate limiting**: Request delays and retries
- **Viewer settings**: Host, port, articles per page

### Keywords

```python
KEYWORDS = {
    "primary": [
        "Perth Bears",
        "Mal Meninga",
    ],
    "secondary": [
        "NRL expansion",
        "Western Australia NRL",
        "Toby Sexton",
        "Harry Newman",
        # ...
    ],
}
```

## Usage

### Manual Scrape

```bash
source venv/bin/activate
python scraper/main.py
```

### Web Viewer

```bash
source venv/bin/activate
python viewer/server.py
```

Access at http://127.0.0.1:5000

### View Logs

```bash
tail -f logs/scraper.log
```

## Web Interface Features

- **Article list**: Sorted by scrape date
- **Filtering**: By source, relevance, read status
- **Pagination**: Navigate through articles
- **Read tracking**: Mark articles as read/unread
- **Keywords**: See which terms matched

## Database Schema

```sql
CREATE TABLE articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    summary TEXT,
    full_text TEXT,
    published_date DATETIME,
    scraped_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    matched_keywords TEXT,  -- JSON array
    relevance_score INTEGER,
    is_read INTEGER DEFAULT 0
);
```

## Notes

- This scraper is for **personal use only**
- Respects rate limiting (3-5 second delays between requests)
- Some sites may have paywalls; the scraper extracts freely available content
- Check site terms of service before extensive use

## Troubleshooting

### No articles found
- Check if keywords match current news
- Verify source websites are accessible
- Check `logs/scraper.log` for errors

### Scraper blocked
- Increase delay settings in `config.py`
- Some sites may require additional handling

### Database issues
- Delete `data/articles.db` to reset
- Database is auto-created on first run

## License

For personal use only.
