#!/bin/bash
# Setup Tamonashini to run daily at 5pm (17:00)

set -e

PROJECT_DIR="/projects/yogasangeeta/tamonashini"
CRON_SCRIPT="tamonashini_scheduler.py"
LOG_FILE="/tmp/tamonashini-cron.log"

echo "=========================================="
echo "TAMONASHINI - CRON JOB SETUP"
echo "=========================================="

# Check if script exists
if [ ! -f "$PROJECT_DIR/$CRON_SCRIPT" ]; then
    echo "❌ Error: $CRON_SCRIPT not found in $PROJECT_DIR"
    exit 1
fi

# Make script executable
chmod +x "$PROJECT_DIR/$CRON_SCRIPT"
echo "✅ Script made executable"

# Check for service account key
if [ ! -f "/tmp/tamonashini-key.json" ]; then
    echo ""
    echo "⚠️  Service account key not found"
    echo "Run this to create it:"
    echo "  gcloud iam service-accounts keys create /tmp/tamonashini-key.json \\"
    echo "    --iam-account=gemini-cli-sa@dattavani.iam.gserviceaccount.com \\"
    echo "    --project=dattavani"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create cron job entry
CRON_ENTRY="0 17 * * * cd $PROJECT_DIR && /usr/bin/python3 $CRON_SCRIPT >> $LOG_FILE 2>&1"

echo ""
echo "Cron job entry:"
echo "  $CRON_ENTRY"
echo ""

# Check if already exists
if crontab -l 2>/dev/null | grep -q "tamonashini_scheduler.py"; then
    echo "⚠️  Cron job already exists!"
    echo ""
    echo "Current cron jobs:"
    crontab -l | grep -i tamonashini
    echo ""
    read -p "Replace it? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelled"
        exit 1
    fi
    # Remove old entry
    crontab -l | grep -v tamonashini_scheduler.py | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null || echo "") | (cat; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job installed!"
echo ""
echo "Configuration:"
echo "  Schedule: Daily at 5:00 PM (17:00)"
echo "  Script: $PROJECT_DIR/$CRON_SCRIPT"
echo "  Log: $LOG_FILE"
echo "  Email: cc@sumvid.ai"
echo ""
echo "View cron job:"
echo "  crontab -l | grep tamonashini"
echo ""
echo "View logs:"
echo "  tail -f $LOG_FILE"
echo ""
echo "=========================================="

# Show next run
echo ""
echo "Next scheduled run:"
python3 << 'PYSCRIPT'
from datetime import datetime, timedelta

now = datetime.now()
if now.hour >= 17:
    next_run = now.replace(hour=17, minute=0, second=0, microsecond=0) + timedelta(days=1)
else:
    next_run = now.replace(hour=17, minute=0, second=0, microsecond=0)

print(f"  {next_run.strftime('%Y-%m-%d at %H:%M:%S')}")
PYSCRIPT

echo ""
echo "✅ Setup complete!"
