# Tamonashini - Daily Automated Run

Run Tamonashini every day at 5pm with automatic email reports.

## Setup Instructions

### 1. Create Service Account Key

```bash
gcloud iam service-accounts keys create /tmp/tamonashini-key.json \
  --iam-account=gemini-cli-sa@dattavani.iam.gserviceaccount.com \
  --project=dattavani
```

### 2. Configure Email (Optional)

Edit `/projects/yogasangeeta/tamonashini/.env.local`:

```bash
# Gmail Configuration (for sending reports)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_PASSWORD=your_gmail_app_password
RECIPIENT_EMAIL=cc@sumvid.ai
```

**To get Gmail app password:**
1. Go to https://myaccount.google.com/security
2. Enable 2-Factor Authentication
3. Generate an "App Password" for "Mail" on "Linux"
4. Use that password in EMAIL_PASSWORD

### 3. Set Up Cron Job

```bash
cd /projects/yogasangeeta/tamonashini
chmod +x setup_cron.sh
./setup_cron.sh
```

This will:
- ✅ Install cron job for daily 5pm run
- ✅ Set up log file at `/tmp/tamonashini-cron.log`
- ✅ Configure email delivery to `cc@sumvid.ai`

### 4. Verify Installation

```bash
# View installed cron job
crontab -l | grep tamonashini

# View logs
tail -f /tmp/tamonashini-cron.log

# Run manually (for testing)
cd /projects/yogasangeeta/tamonashini
python3 tamonashini_scheduler.py
```

## Daily Workflow

**Every day at 5:00 PM:**

1. Tamonashini runs automatically
2. Searches YouTube for videos about Ganapathy Sachchidananda Swamiji
3. Filters out official channels (@dattapeetham, @YogaSangeeta, etc.)
4. Analyzes sentiment of third-party content
5. Exports results to `sentiment_analysis_results.csv`
6. Sends email report to `cc@sumvid.ai` with CSV attached

## Configuration

### Cron Schedule

Current: **5:00 PM daily** (17:00)

To change time, edit crontab:
```bash
crontab -e
# Find the tamonashini line and edit the time
# Format: MM HH * * * (minute hour day month dayofweek)
# Example: 0 19 * * * = 7:00 PM daily
```

### Search Queries

Edit `tamonashini_scheduler.py`, function `run_analysis()`:

```python
queries = [
    'Ganapathy Sachchidananda Swamiji',
    'Satchidananda Swami',
    'Dattapeetham',
    # Add more queries here
]
```

### Official Channels Filter

Edit `sentiment_analyzer_simple.py`, class `TamonashiniSentimentAnalyzer`:

```python
OFFICIAL_CHANNELS = {
    '@dattapeetham',
    '@YogaSangeeta',
    # Add more official channels here
}
```

## Troubleshooting

### Email not sending
- Check `EMAIL_PASSWORD` is set in `.env.local`
- Verify Gmail account has 2FA enabled
- Use an "App Password", not your regular password
- Check `/tmp/tamonashini-cron.log` for errors

### YouTube API error
- Verify service account key exists: `/tmp/tamonashini-key.json`
- Check `GOOGLE_APPLICATION_CREDENTIALS` in `.env.local`
- Verify gemini-cli-sa service account has YouTube API access

### Cron job not running
- Verify cron is running: `sudo systemctl status cron`
- Check cron logs: `grep CRON /var/log/syslog` (Ubuntu) or `log stream --predicate 'eventMessage contains[cd] "cron"'` (macOS)
- Verify Python path: `which python3`
- Check file permissions: `ls -la tamonashini_scheduler.py`

### Python 3.14 protobuf issue
- This is handled gracefully in the scheduler
- Falls back to basic YouTube search if Gemini import fails
- Email will still be sent with results

## Output

### CSV File
`sentiment_analysis_results.csv` contains:
- video_id
- url
- title
- channel_name
- upload_date
- title_sentiment_score
- title_sentiment_label
- negative_keywords
- view_count
- analysis_timestamp

### Email Report
Daily email to cc@sumvid.ai with:
- Summary of analysis
- CSV file attached
- Timestamp
- Number of videos analyzed

## Example Log Output

```
======================================================================
TAMONASHINI DAILY RUN - 2024-09-17 17:00:00
======================================================================

Searching with 5 queries...
INFO:sentiment_analyzer_simple:Searching: Ganapathy Sachchidananda Swamiji
INFO:sentiment_analyzer_simple:Found 5 videos
Analyzing 5 videos...
⊘ Skipping official channel: Sri Ganapathy Sachchidananda Swamiji - SGS Swamiji
✓ Analyzing: Anagha Media
...
✅ Analysis complete!
✅ Email sent to cc@sumvid.ai
```

## Manual Test

```bash
cd /projects/yogasangeeta/tamonashini
python3 tamonashini_scheduler.py
```

This will:
1. Run analysis immediately
2. Send test email to cc@sumvid.ai
3. Show results in terminal
4. Log output to `/tmp/tamonashini-cron.log`

## Support

For issues, check:
- `.env.local` - All environment variables set
- `/tmp/tamonashini-key.json` - Service account key exists
- `/tmp/tamonashini-cron.log` - Latest logs
- `crontab -l` - Cron job is installed

## Next Steps

1. ✅ Create service account key
2. ✅ Configure email settings (optional)
3. ✅ Run setup script: `./setup_cron.sh`
4. ✅ Verify: `crontab -l | grep tamonashini`
5. ✅ Test: `python3 tamonashini_scheduler.py`
6. ✅ Monitor: `tail -f /tmp/tamonashini-cron.log`

Done! Tamonashini will run automatically every day at 5pm.
