# Perth Bears News Scraper - Setup & Usage Guide

A Python application that monitors Australian news sources for Perth Bears Rugby League coverage, stores articles in a local database, and provides a web interface for reading them.

---

## Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Running the Scraper](#running-the-scraper)
4. [Using the Web Viewer](#using-the-web-viewer)
5. [Scheduling Automatic Scrapes](#scheduling-automatic-scrapes)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)

---

## Requirements

- macOS (tested on macOS Monterey+)
- Python 3.9 or higher
- Internet connection

---

## Installation

### Step 1: Navigate to the Project

```bash
cd "/Users/m4/Development/Claude Stuff/ScrapeMe"
```

### Step 2: Create Virtual Environment (if not already done)

```bash
python3 -m venv venv
```

### Step 3: Activate Virtual Environment

```bash
source venv/bin/activate
```

You'll see `(venv)` appear at the start of your terminal prompt.

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `requests` - HTTP library for fetching web pages
- `beautifulsoup4` - HTML parsing
- `lxml` - Fast XML/HTML parser
- `flask` - Web framework for the viewer
- `python-dateutil` - Date parsing utilities

---

## Running the Scraper

The scraper fetches articles from news sources and saves matching ones to the database.

### Basic Usage

```bash
cd "/Users/m4/Development/Claude Stuff/ScrapeMe"
source venv/bin/activate
python scraper/main.py
```

### What It Does

1. Connects to each enabled news source (NRL.com, The West, Fox Sports, etc.)
2. Finds article links on their news pages
3. Checks article titles/content for keywords like "Perth Bears" or "Mal Meninga"
4. Saves matching articles to the SQLite database
5. Skips articles already in the database (no duplicates)

### Expected Output

```
============================================================
Perth Bears News Scraper starting at 2026-02-04 18:45:00
============================================================
Processing source: NRL.com
  Found: 2, Saved: 2
Processing source: The Roar
  Found: 0, Saved: 0
Processing source: The West Australian
  Found: 1, Saved: 1
...
============================================================
Scrape complete!
  Total articles found: 5
  New articles saved: 5
  Duplicates skipped: 0
  Database total: 5 articles (5 unread)
============================================================
```

### Runtime

- Takes 3-5 minutes due to rate limiting (3-5 second delays between requests)
- This is intentional to avoid being blocked by news sites

---

## Using the Web Viewer

The web viewer displays saved articles in a browser interface.

### Starting the Server

```bash
cd "/Users/m4/Development/Claude Stuff/ScrapeMe"
source venv/bin/activate
python viewer/server.py
```

### Accessing the Viewer

Open your browser and go to:

```
http://localhost:5050
```

### Features

#### Article List
- Articles sorted by scrape date (newest first)
- Shows source, date, relevance badge, and matched keywords
- Click article title to open original source in new tab

#### Filtering
- **Source**: Filter by specific news source
- **Relevance**:
  - "Primary Only" = matches "Perth Bears" or "Mal Meninga"
  - "Any Match" = includes secondary keywords like "NRL expansion"
- **Unread only**: Hide articles you've already read

#### Read Tracking
- Articles automatically marked as read when you click "View Details"
- Use "Mark Read" / "Mark Unread" buttons to manually toggle

#### Pagination
- 20 articles per page
- Use Previous/Next links to navigate

### Stopping the Server

Press `Ctrl+C` in the terminal where it's running.

---

## Scheduling Automatic Scrapes

You can set up the scraper to run automatically using macOS cron.

### Option 1: Use the Setup Script

```bash
cd "/Users/m4/Development/Claude Stuff/ScrapeMe"
./setup_cron.sh
```

This schedules scrapes at 6am, 10am, 2pm, 6pm, and 10pm daily.

### Option 2: Manual Setup

1. Open your crontab:
   ```bash
   crontab -e
   ```

2. Add this line (adjust paths if needed):
   ```
   0 6,10,14,18,22 * * * /Users/m4/Development/Claude\ Stuff/ScrapeMe/venv/bin/python /Users/m4/Development/Claude\ Stuff/ScrapeMe/scraper/main.py >> /Users/m4/Development/Claude\ Stuff/ScrapeMe/logs/cron.log 2>&1
   ```

3. Save and exit (`:wq` in vim)

### Verify Cron Job

```bash
crontab -l
```

### Remove Cron Job

```bash
crontab -e
# Delete the line containing scraper/main.py
# Save and exit
```

---

## Configuration

Edit `config.py` to customize the scraper.

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
        # Add more keywords here
    ],
}
```

- **Primary**: High relevance - these are the main search terms
- **Secondary**: Lower relevance - broader NRL expansion news

### Enable/Disable Sources

In the `SOURCES` dictionary, set `"enabled": False` to skip a source:

```python
"foxsports": {
    "name": "Fox Sports",
    "base_url": "https://www.foxsports.com.au",
    "news_url": "https://www.foxsports.com.au/nrl",
    "enabled": False,  # Skip this source
    "priority": 2,
},
```

### Rate Limiting

Adjust delays between requests:

```python
MIN_DELAY_BETWEEN_REQUESTS = 3  # seconds
MAX_DELAY_BETWEEN_REQUESTS = 5  # seconds
```

Increase these if you're getting blocked by sites.

### Viewer Settings

```python
VIEWER_HOST = "0.0.0.0"   # Accept connections from any interface
VIEWER_PORT = 5050        # Port number
ARTICLES_PER_PAGE = 20    # Articles shown per page
```

---

## Troubleshooting

### "No articles found"

1. **Run the scraper first**: The viewer only displays what's in the database
   ```bash
   python scraper/main.py
   ```

2. **Check keywords match current news**: If there's no recent Perth Bears coverage, no articles will be saved

3. **Check the logs**:
   ```bash
   cat logs/scraper.log
   ```

### Port 5000 gives 403 Forbidden

macOS uses port 5000 for AirPlay. The app is configured to use port 5050 instead.

If you still have issues:
1. Check what's using the port: `lsof -i :5050`
2. Change `VIEWER_PORT` in `config.py` to another number (e.g., 8080)

### Scraper blocked by a website

Some sites may block scrapers. If you see errors for a specific source:

1. Increase delays in `config.py`
2. Disable the problematic source by setting `"enabled": False`
3. Check `logs/scraper.log` for specific error messages

### Database issues

To reset the database completely:

```bash
rm data/articles.db
python scraper/main.py  # Creates fresh database
```

### Virtual environment issues

If Python can't find modules:

```bash
# Make sure you're in the project directory
cd "/Users/m4/Development/Claude Stuff/ScrapeMe"

# Activate the virtual environment
source venv/bin/activate

# Verify you see (venv) in your prompt
# If not, recreate it:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## File Locations

| File/Folder | Purpose |
|-------------|---------|
| `config.py` | All settings (keywords, sources, ports) |
| `data/articles.db` | SQLite database with saved articles |
| `logs/scraper.log` | Scraper activity log |
| `logs/cron.log` | Scheduled scrape output (if using cron) |
| `scraper/main.py` | Run this to fetch articles |
| `viewer/server.py` | Run this to start the web viewer |

---

## Quick Reference

```bash
# Always start with these two commands:
cd "/Users/m4/Development/Claude Stuff/ScrapeMe"
source venv/bin/activate

# Fetch new articles:
python scraper/main.py

# Start web viewer:
python viewer/server.py
# Then open http://localhost:5050

# View logs:
tail -f logs/scraper.log

# Check database stats:
python -c "from scraper.database import get_stats; print(get_stats())"
```
