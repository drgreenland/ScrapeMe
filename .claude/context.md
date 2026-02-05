# Project: ScrapeMe (Perth Bears News Scraper)

**Created:** 2026-02-05 16:36:31
**Last Updated:** 2026-02-05 16:48:41
**Iterations:** 1
**Repository:** https://github.com/drgreenland/ScrapeMe.git

## Project Overview

A Python web scraper that monitors Australian newspapers for Perth Bears Rugby League news. The Perth Bears are an NRL expansion team joining in 2027, coached by Mal Meninga.

**Key Features:**
- Scrapes multiple Australian news sources (NRL.com, The Roar, PerthNow, The West Australian, Fox Sports, SMH, The Age, CODE Sports)
- Keyword matching with primary/secondary relevance scoring
- SQLite database for article storage with deduplication
- Flask-based web viewer with filtering, pagination, and read/unread tracking
- Mobile-friendly responsive design
- CRON scheduling support for automated scraping

## Current Status

✅ Core scraper implemented with 8 news sources
✅ SQLite database with full CRUD operations
✅ Flask web viewer with article listing and detail pages
✅ Filtering by source, relevance, read status
✅ Notes feature for annotating articles
✅ Rate limiting and retry logic
⚠️ Some sources failing (Fox Sports, CODE Sports - redirect issues)
⚠️ Some sources returning 0 URLs (The West, SMH, The Age - selector issues)

## Development History

### Iteration 1 - 2026-02-05
- **Goal:** Build complete Perth Bears News Scraper from scratch
- **Changes:** 8 source scrapers, SQLite database, Flask web viewer with filtering and notes
- **Outcome:** Fully functional scraper and viewer; some sources need selector fixes
- **Learnings:** macOS uses port 5000 for AirPlay; Perth Bears coverage is sparse pre-2027

## Active Context

### Current Focus
- Initial implementation complete
- Testing and refinement phase

### Open Questions
- Should failing sources be disabled or fixed?
- Add more news sources?
- Implement database-backed notes storage?

### Next Steps
- Fix selectors for sources returning 0 URLs
- Investigate Fox Sports/CODE Sports redirect issues
- Consider adding RSS feed support as alternative
- Test CRON scheduling

## Technical Context

### Dependencies
- Python 3.9+
- requests >= 2.31.0
- beautifulsoup4 >= 4.12.0
- lxml >= 4.9.0
- flask >= 3.0.0
- python-dateutil >= 2.8.0

### File Structure
```
ScrapeMe/
├── config.py              # Keywords, sources, settings
├── requirements.txt       # Dependencies
├── README.md              # Documentation
├── SETUP_GUIDE.md         # Detailed setup instructions
├── setup_cron.sh          # CRON installation script
├── scraper/
│   ├── main.py            # Orchestrator
│   ├── database.py        # SQLite operations
│   └── sources/
│       ├── base.py        # Abstract scraper class
│       ├── nrl_official.py
│       ├── theroar.py
│       ├── thewest.py
│       ├── perthnow.py
│       ├── foxsports.py
│       ├── smh.py
│       ├── theage.py
│       └── codesports.py
├── viewer/
│   ├── server.py          # Flask web server
│   ├── templates/         # HTML templates
│   └── static/            # CSS styles
├── data/                  # SQLite database
└── logs/                  # Scraper logs
```

### Conventions
- Source scrapers extend `BaseScraper` abstract class
- Each source has its own module in `scraper/sources/`
- Rate limiting: 3-5 second delays between requests
- Keywords in config.py with primary (high relevance) and secondary (lower relevance)
- Web viewer runs on port 5050 (avoiding macOS AirPlay on 5000)

### Key Patterns
- Abstract base class pattern for scrapers
- Context managers for database connections
- Template filters for date formatting and text truncation
- Session-based HTTP requests with User-Agent rotation
