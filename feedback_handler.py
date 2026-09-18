#!/usr/bin/env python3
"""
Tamonashini Feedback Handler
Processes feedback on sentiment analysis results
"""

import sys
import sqlite3
from datetime import datetime
from pathlib import Path

class FeedbackQueue:
    """Manages feedback submissions"""

    def __init__(self, db_path: str = "tamonashini_videos.db"):
        self.db_path = db_path
        self.init_feedback_table()

    def init_feedback_table(self):
        """Initialize feedback table"""
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

    def submit_feedback(self, video_id: str, feedback_type: str, notes: str = '', use_cloud_tasks: bool = True):
        """Submit feedback for a video"""

        # Validate feedback type
        valid_types = ['correct', 'false_positive', 'uncertain']
        if feedback_type.lower() not in valid_types:
            return False, f"Invalid feedback type. Must be one of: {', '.join(valid_types)}"

        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            # Check if video exists
            c.execute('SELECT 1 FROM sent_videos WHERE video_id = ?', (video_id,))
            if not c.fetchone():
                conn.close()
                return False, f"Video {video_id} not found in database"

            # Insert feedback locally
            c.execute('''
                INSERT INTO video_feedback (video_id, feedback_type, notes)
                VALUES (?, ?, ?)
            ''', (video_id, feedback_type.lower(), notes))
            conn.commit()
            conn.close()

            # Try to queue to Cloud Tasks if enabled
            if use_cloud_tasks:
                try:
                    from cloud_tasks_feedback import submit_feedback_to_cloud_tasks
                    submit_feedback_to_cloud_tasks(video_id, feedback_type.lower(), notes)
                except ImportError:
                    pass

            return True, f"Feedback recorded: {video_id} → {feedback_type}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def get_feedback_stats(self):
        """Get feedback statistics"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT feedback_type, COUNT(*) FROM video_feedback
            GROUP BY feedback_type
        ''')
        stats = dict(c.fetchall())

        c.execute('SELECT COUNT(*) FROM video_feedback')
        total = c.fetchone()[0]

        conn.close()
        return {'total': total, 'by_type': stats}

    def get_pending_videos(self):
        """Get videos without feedback"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            SELECT sv.video_id, sv.title, sv.sentiment_score
            FROM sent_videos sv
            LEFT JOIN video_feedback vf ON sv.video_id = vf.video_id
            WHERE vf.id IS NULL
            ORDER BY sv.sentiment_score ASC
        ''')
        videos = c.fetchall()
        conn.close()
        return videos

def main():
    """CLI interface for feedback submission"""

    if len(sys.argv) < 2:
        print("Usage: python3 feedback_handler.py <command> [args]")
        print("\nCommands:")
        print("  submit <video_id> <correct|false_positive|uncertain> [notes]")
        print("  stats")
        print("  pending")
        print("\nExample:")
        print("  python3 feedback_handler.py submit ABC123 correct")
        print("  python3 feedback_handler.py submit ABC123 false_positive 'Actually positive content'")
        return 1

    queue = FeedbackQueue()
    command = sys.argv[1]

    if command == 'submit':
        if len(sys.argv) < 4:
            print("Error: submit requires video_id and feedback_type")
            return 1

        video_id = sys.argv[2]
        feedback_type = sys.argv[3]
        notes = ' '.join(sys.argv[4:]) if len(sys.argv) > 4 else ''

        success, message = queue.submit_feedback(video_id, feedback_type, notes)
        print(message)
        return 0 if success else 1

    elif command == 'stats':
        stats = queue.get_feedback_stats()
        print(f"\n📊 Feedback Statistics:")
        print(f"   Total feedback: {stats['total']}")
        for ftype, count in stats['by_type'].items():
            print(f"   - {ftype}: {count}")
        return 0

    elif command == 'pending':
        videos = queue.get_pending_videos()
        print(f"\n⏳ Videos pending feedback ({len(videos)}):")
        for vid_id, title, score in videos:
            print(f"   [{score:.2f}] {vid_id} | {title[:50]}")
        return 0

    else:
        print(f"Unknown command: {command}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
