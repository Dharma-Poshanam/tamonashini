#!/usr/bin/env python3
"""
Tamonashini Daily Scheduler
Runs at 5pm daily, searches YouTube, sends results via email
Avoids Gemini/protobuf issues by using YouTube API only
"""

import os
import sys
import smtplib
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

def send_email_with_csv(csv_file, recipient):
    """Send CSV results via email"""
    try:
        # Email configuration
        sender_email = "dev@dharmaposhanam.in"  # Your Gmail account that generated the app password
        sender_password = os.getenv('EMAIL_PASSWORD', '')
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))

        if not sender_password:
            print(f"⚠️  EMAIL_PASSWORD not set - skipping email")
            return False

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = f'Tamonashini Daily Report - {datetime.now().strftime("%Y-%m-%d")}'

        # Body
        body = f"""Tamonashini Daily Analysis Report
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

YouTube videos analyzed and results attached.
Official channels have been filtered out.
Third-party content only.

---
Tamonashini Sentiment Analyzer
"""

        msg.attach(MIMEText(body, 'plain'))

        # Attach CSV file
        if os.path.exists(csv_file):
            with open(csv_file, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={Path(csv_file).name}')
                msg.attach(part)

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        print(f"✅ Email sent to {recipient}")
        return True

    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def run_analysis():
    """Run YouTube search and save results"""
    try:
        print("\n" + "=" * 70)
        print(f"TAMONASHINI DAILY RUN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70 + "\n")

        # Get credentials
        credentials_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '/tmp/tamonashini-key.json')
        if not os.path.exists(credentials_file):
            print(f"❌ Credentials file not found: {credentials_file}")
            return False

        credentials = service_account.Credentials.from_service_account_file(
            credentials_file,
            scopes=['https://www.googleapis.com/auth/youtube.readonly']
        )

        youtube = build('youtube', 'v3', credentials=credentials)

        # Search queries
        queries = [
            'Ganapathy Sachchidananda Swamiji',
            'Satchidananda Swami',
            'Dattapeetham',
            'land encroachment Dattapeetham',
            'Ganapathy court case',
        ]

        print(f"Searching YouTube with {len(queries)} queries...\n")

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

                    # Check if official channel
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

        print(f"✅ Found {len(all_videos)} videos (filtered official channels)\n")

        # Create CSV
        csv_file = 'sentiment_analysis_results.csv'
        if all_videos:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'title', 'channel', 'date', 'url'])
                writer.writeheader()
                writer.writerows(all_videos)
            print(f"✅ Results saved to {csv_file}")
        else:
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'title', 'channel', 'date', 'url'])
                writer.writeheader()
            print(f"✅ No videos found, CSV created")

        return True

    except Exception as e:
        print(f"❌ Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main entry point"""
    # Set up credentials
    credentials_file = '/tmp/tamonashini-key.json'
    if not os.path.exists(credentials_file):
        print("❌ Service account credentials not found at /tmp/tamonashini-key.json")
        return 1

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file

    # Run analysis
    success = run_analysis()

    # Send results
    if success:
        csv_file = Path(__file__).parent / 'sentiment_analysis_results.csv'
        recipient = os.getenv('RECIPIENT_EMAIL', 'cc@sumvid.ai')

        print(f"\nSending results to {recipient}...")
        send_email_with_csv(str(csv_file), recipient)

    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
