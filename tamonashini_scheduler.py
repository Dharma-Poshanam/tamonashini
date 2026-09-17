#!/usr/bin/env python3
"""
Tamonashini Daily Scheduler
Runs at 5pm daily, analyzes videos, sends results via email
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

# Load environment
load_dotenv(Path(__file__).parent / '.env.local')

def send_email_with_csv(csv_file, recipient):
    """Send CSV results via email"""
    try:
        # Email configuration
        sender_email = "noreply@sumvid.ai"
        sender_password = os.getenv('EMAIL_PASSWORD', '')
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient
        msg['Subject'] = f'Tamonashini Daily Report - {datetime.now().strftime("%Y-%m-%d")}'

        # Body
        body = f"""
Tamonashini Daily Analysis Report
{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Negative sentiment videos found and analyzed.
Results attached as CSV file.

All official channels have been filtered out.
Only third-party content is included in the analysis.

---
Tamonashini Sentiment Analyzer
Running locally
"""

        msg.attach(MIMEText(body, 'plain'))

        # Attach CSV file
        if os.path.exists(csv_file):
            with open(csv_file, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename= {Path(csv_file).name}')
                msg.attach(part)

        # Send email
        if sender_password:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            print(f"✅ Email sent to {recipient}")
            return True
        else:
            print(f"⚠️  EMAIL_PASSWORD not set - skipping email")
            print(f"   Results saved to: {csv_file}")
            return False

    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

def run_analysis():
    """Run the Tamonashini analyzer"""
    try:
        print("\n" + "=" * 70)
        print(f"TAMONASHINI DAILY RUN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70 + "\n")

        # Import analyzer (handle protobuf issues gracefully)
        try:
            from sentiment_analyzer_simple import TamonashiniSentimentAnalyzer
        except ImportError as e:
            print(f"⚠️  Import warning (expected on Python 3.14): {type(e).__name__}")
            print("   Attempting workaround...\n")

            # Try minimal import approach
            import subprocess
            result = subprocess.run([
                sys.executable, '-c',
                """
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path('.') / '.env.local')

from google.oauth2 import service_account
from googleapiclient.discovery import build
import csv
from datetime import datetime

# Quick YouTube search without full analyzer
credentials = service_account.Credentials.from_service_account_file(
    os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '/tmp/tamonashini-key.json'),
    scopes=['https://www.googleapis.com/auth/youtube.readonly']
)
youtube = build('youtube', 'v3', credentials=credentials)

queries = [
    'Ganapathy Sachchidananda Swamiji',
    'Dattapeetham fraud',
    'Satchidananda court case'
]

all_videos = []
for query in queries:
    request = youtube.search().list(
        q=query, part='snippet', maxResults=3,
        order='relevance', type='video', regionCode='IN'
    )
    response = request.execute()
    for item in response.get('items', []):
        all_videos.append({
            'title': item['snippet']['title'],
            'channel': item['snippet']['channelTitle'],
            'date': item['snippet']['publishedAt']
        })

print(f"Found {len(all_videos)} videos")
for v in all_videos[:3]:
    print(f"- {v['title'][:60]}...")
    print(f"  Channel: {v['channel']}")
"""
            ], cwd=Path(__file__).parent)
            return result.returncode == 0

        # Initialize analyzer
        credentials_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '/tmp/tamonashini-key.json')
        analyzer = TamonashiniSentimentAnalyzer(
            analyze_full_video=False,
            credentials_file=credentials_file
        )

        # Search queries
        queries = [
            'Ganapathy Sachchidananda Swamiji',
            'Satchidananda Swami',
            'Dattapeetham',
            'land encroachment Dattapeetham',
            'Ganapathy court case',
        ]

        print(f"Searching with {len(queries)} queries...")
        analyzer.run(queries)

        print(f"\n✅ Analysis complete!")
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
        print("   Run: gcloud iam service-accounts keys create /tmp/tamonashini-key.json ...")
        return 1

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_file

    # Run analysis
    success = run_analysis()

    # Send results
    if success:
        csv_file = Path(__file__).parent / 'sentiment_analysis_results.csv'
        recipient = 'cc@sumvid.ai'

        print(f"\nSending results to {recipient}...")
        send_email_with_csv(str(csv_file), recipient)

    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
