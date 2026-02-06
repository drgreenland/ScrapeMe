#!/bin/bash
#
# Setup CRON job for Perth Bears News Scraper
#
# This script adds a cron job to run the scraper every 4 hours
# from 6am to 10pm local time.
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="${SCRIPT_DIR}/venv/bin/python"
SCRAPER_PATH="${SCRIPT_DIR}/scraper/main.py"
LOG_PATH="${SCRIPT_DIR}/logs/cron.log"

# Check if virtual environment exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "Error: Virtual environment not found at $SCRIPT_DIR/venv"
    echo "Please create it first with:"
    echo "  cd $SCRIPT_DIR"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Create the cron job entry
CRON_JOB="0 6,8,10,12,14,16,18,20,22 * * * $PYTHON_PATH $SCRAPER_PATH >> $LOG_PATH 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$SCRAPER_PATH"; then
    echo "Cron job already exists. Updating..."
    # Remove existing entry
    crontab -l 2>/dev/null | grep -v "$SCRAPER_PATH" | crontab -
fi

# Add the cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Cron job installed successfully!"
echo ""
echo "Schedule: Every 4 hours (6am, 10am, 2pm, 6pm, 10pm)"
echo "Log file: $LOG_PATH"
echo ""
echo "To verify, run: crontab -l"
echo "To remove, run: crontab -e and delete the line containing $SCRAPER_PATH"
