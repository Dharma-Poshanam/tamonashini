#!/usr/bin/env python3
"""
Tamonashini Daily Scheduler with Qwen Sentiment Analysis and SQLite Tracking
- Searches YouTube with targeted queries
- Filters with Qwen sentiment analysis (local vLLM)
- Tracks sent videos in SQLite to avoid duplicates
- Only sends email if new negative videos found
"""

import os
import sys
import smtplib
import sqlite3
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
import csv

# Load environment
load_dotenv(Path(__file__).parent / '.env.local')

class VideoDatabase:
    """SQLite database for tracking sent videos"""

    def __init__(self, db_path: str = "tamonashini_videos.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize database if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS sent_videos (
                video_id TEXT PRIMARY KEY,
                title TEXT,
                channel TEXT,
                url TEXT,
                sent_date TIMESTAMP,
                sentiment_score REAL,
                sentiment_label TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def is_sent(self, video_id: str) -> bool:
        """Check if video was already sent"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT 1 FROM sent_videos WHERE video_id = ?', (video_id,))
        result = c.fetchone()
        conn.close()
        return result is not None

    def add_video(self, video_id: str, title: str, channel: str, url: str,
                  sentiment_score: float, sentiment_label: str):
        """Add sent video to database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT OR IGNORE INTO sent_videos
            (video_id, title, channel, url, sent_date, sentiment_score, sentiment_label)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (video_id, title, channel, url, datetime.now(), sentiment_score, sentiment_label))
        conn.commit()
        conn.close()

    def get_stats(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM sent_videos')
        count = c.fetchone()[0]
        conn.close()
        return {'total_sent': count}

    def init_feedback_table(self):
        """Initialize feedback table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS video_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                feedback_type TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_feedback(self, video_id: str, feedback_type: str, notes: str = ''):
        """Add feedback for a video"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            INSERT INTO video_feedback (video_id, feedback_type, notes)
            VALUES (?, ?, ?)
        ''', (video_id, feedback_type, notes))
        conn.commit()
        conn.close()

    def get_feedback_for_video(self, video_id: str):
        """Get feedback for a specific video"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT feedback_type, timestamp, notes FROM video_feedback
            WHERE video_id = ? ORDER BY timestamp DESC LIMIT 1
        ''', (video_id,))
        result = c.fetchone()
        conn.close()
        return result

def get_previously_reported_videos(db_path: str = "tamonashini_videos.db", limit: int = 10) -> list:
    """Get recently reported videos from database, sorted by sentiment (most negative first)"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        SELECT video_id, title, channel, url, sent_date, sentiment_score, sentiment_label
        FROM sent_videos
        ORDER BY sentiment_score ASC, sent_date DESC
        LIMIT ?
    ''', (limit,))
    videos = c.fetchall()
    conn.close()
    return videos

def send_email_with_csv(csv_file, recipient, videos_count, db_path: str = "tamonashini_videos.db"):
    """Send email report (with or without videos)"""

    try:
        sender_email = "dev@dharmaposhanam.in"
        sender_password = os.getenv('EMAIL_PASSWORD', '')
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))

        if not sender_password:
            print(f"⚠️  EMAIL_PASSWORD not set - skipping email")
            return False

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient

        if videos_count > 0:
            msg['Subject'] = f'Tamonashini Report - {videos_count} new videos - {datetime.now().strftime("%Y-%m-%d")}'
            body = f"""Tamonashini Daily Analysis Report
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

✅ {videos_count} new negative/controversial videos found.
Official channels filtered out.
Results attached.

---
Tamonashini with Qwen2.5 Sentiment Analysis
Local SQLite database tracking
"""
        else:
            msg['Subject'] = f'Tamonashini Report - No negative videos - {datetime.now().strftime("%Y-%m-%d")}'
            body = f"""Tamonashini Daily Analysis Report
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

⊘ No new negative/controversial videos found.
Official channels filtered out.

Searched across multiple queries with sentiment analysis.
No attachment (no new videos to report).

---
Tamonashini with Qwen2.5 Sentiment Analysis
Local SQLite database tracking
"""

        # Add previously reported videos section with feedback links
        prev_videos = get_previously_reported_videos(db_path)
        if prev_videos:
            body += f"\n\n📋 PREVIOUSLY REPORTED VIDEOS (Last {len(prev_videos)}):\n"
            body += "=" * 70 + "\n"
            for i, (vid_id, title, channel, url, sent_date, score, label) in enumerate(prev_videos, 1):
                body += f"\n{i}. [{label.upper()}] {title}\n"
                body += f"   Channel: {channel}\n"
                body += f"   Score: {score:.2f} | Sent: {sent_date[:10]}\n"
                body += f"   URL: {url}\n"
                body += f"   Feedback: [✓ Correct] [✗ False Positive] [? Uncertain]\n"
                body += f"   Commands:\n"
                body += f"     python3 feedback_handler.py submit {vid_id} correct\n"
                body += f"     python3 feedback_handler.py submit {vid_id} false_positive\n"
                body += f"     python3 feedback_handler.py submit {vid_id} uncertain\n"

        msg.attach(MIMEText(body, 'plain'))

        # Only attach CSV if there are videos
        if videos_count > 0 and os.path.exists(csv_file):
            with open(csv_file, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={Path(csv_file).name}')
                msg.attach(part)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        status = f"({videos_count} new videos)" if videos_count > 0 else "(no new videos)"
        print(f"✅ Email sent to {recipient} {status}")
        return True

    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def filter_with_qwen(videos):
    """Filter videos using Qwen sentiment analysis"""
    try:
        from sentiment_analyzer_qwen import QwenSentimentAnalyzer

        qwen = QwenSentimentAnalyzer()
        relevant_videos = qwen.filter_and_analyze(videos)

        negative_videos = [v for v in relevant_videos
                          if v.get('analysis', {}).get('sentiment_score', 0) < -0.2]

        print(f"\n✅ {len(negative_videos)} negative/relevant videos found\n")
        return negative_videos

    except Exception as e:
        print(f"⚠️  Qwen analysis failed: {e}")
        print("   Using all videos (no filtering)\n")
        return videos

def run_analysis():
    """Run YouTube search with Qwen sentiment filtering and duplicate tracking"""
    try:
        print("\n" + "=" * 70)
        print(f"TAMONASHINI DAILY RUN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70 + "\n")

        # Initialize database
        db = VideoDatabase()
        db_stats = db.get_stats()
        print(f"Database: {db_stats['total_sent']} videos already tracked\n")

        credentials_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '/tmp/tamonashini-key.json')
        if not os.path.exists(credentials_file):
            print(f"❌ Credentials file not found: {credentials_file}")
            return False

        credentials = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/youtube.readonly']
        )

        youtube = build('youtube', 'v3', credentials=credentials)

        # Improved search queries
        queries = [
            'Ganapathy Sachchidananda Swamiji court',
            'Satchidananda Swami fraud',
            'Dattapeetham land encroachment',
            'Swami Ganapathy scandal',
            'Dattapeetham controversy',
        ]

        print(f"Searching YouTube with {len(queries)} targeted queries...\n")

        official_channels = {
            '@dattapeetham', '@gurubhavanaadpt', '@kshtcultural7147',
            '@DallasHanuman', '@YogaSangeeta', '@SGSRagaSagara', '@sgsswamiji',
            'Dattapeetham', 'Guru Bhavana', 'KSHT Cultural', 'Dallas Hanuman',
            'Yoga Sangeeta', 'SGS Raga Sagara', 'SGS Swamiji',
        }

        all_videos = []
        for query in queries:
            try:
                request = youtube.search().list(
                    q=query, part='snippet', maxResults=5,
                    order='relevance', type='video', regionCode='IN'
                )
                response = request.execute()

                for item in response.get('items', []):
                    video_id = item['id'].get('videoId', '')
                    channel = item['snippet']['channelTitle']

                    is_official = any(ch.lower() in channel.lower() or channel.lower() in ch.lower()
                                     for ch in official_channels)

                    if not is_official:
                        all_videos.append({
                            'id': video_id,
                            'title': item['snippet']['title'],
                            'channel': channel,
                            'date': item['snippet']['publishedAt'],
                            'url': f'https://youtube.com/watch?v={video_id}'
                        })
            except Exception as e:
                print(f"⚠️  Query error '{query}': {str(e)[:50]}")

        print(f"Found {len(all_videos)} videos (official channels filtered)\n")

        # Filter with Qwen
        filtered_videos = filter_with_qwen(all_videos)

        # Filter truly negative videos (score < -0.65 to avoid false positives)
        negative_videos = [v for v in filtered_videos
                          if v.get('analysis', {}).get('sentiment_score', 0) < -0.65]

        print(f"\n✅ {len(negative_videos)} truly negative videos (score < -0.65)\n")

        # Filter out already-sent videos
        new_videos = [v for v in negative_videos if not db.is_sent(v.get('id'))]

        # Sort by sentiment score (most negative first)
        new_videos.sort(key=lambda v: v.get('analysis', {}).get('sentiment_score', 0))

        print(f"New videos (not previously sent): {len(new_videos)}\n")

        # Create CSV
        csv_file = 'sentiment_analysis_results.csv'
        if new_videos:
            fieldnames = ['video_id', 'title', 'channel', 'date', 'url', 'sentiment_score', 'sentiment_label', 'status']
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for v in new_videos:
                    score = v.get('analysis', {}).get('sentiment_score', 0)
                    label = v.get('analysis', {}).get('sentiment_label', '')
                    status = f"[{label.upper()}] {v.get('id')} | {v.get('title')[:50]} - {v.get('channel')} | Score: {score:.2f}"

                    row = {
                        'video_id': v.get('id'),
                        'title': v.get('title'),
                        'channel': v.get('channel'),
                        'date': v.get('date'),
                        'url': v.get('url'),
                        'sentiment_score': score,
                        'sentiment_label': label,
                        'status': status,
                    }
                    writer.writerow(row)

                    # Add to database
                    db.add_video(
                        v.get('id'),
                        v.get('title'),
                        v.get('channel'),
                        v.get('url'),
                        score,
                        label
                    )
            print(f"✅ {len(new_videos)} new negative videos saved to {csv_file}")
        else:
            print(f"✅ No new truly negative videos found")

        return len(new_videos)

    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    """Main entry point"""
    credentials_file = '/tmp/tamonashini-key.json'
    if not os.path.exists(credentials_file):
        print("❌ Service account credentials not found at /tmp/tamonashini-key.json")
        return 1

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file

    # Run analysis
    new_videos_count = run_analysis()

    # Always send email (with or without videos)
    csv_file = Path(__file__).parent / 'sentiment_analysis_results.csv'
    recipient = os.getenv('RECIPIENT_EMAIL', 'cc@sumvid.ai')

    print(f"\nSending report to {recipient}...")
    send_email_with_csv(str(csv_file), recipient, new_videos_count)

    return 0

if __name__ == '__main__':
    sys.exit(main())
