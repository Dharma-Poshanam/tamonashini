#!/usr/bin/env python3
"""
Tamonashini Cloud Tasks Feedback Queue
Submits feedback to Google Cloud Tasks for processing
"""

import os
import json
from datetime import datetime
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

class CloudTasksFeedback:
    """Submit feedback to Google Cloud Tasks queue"""

    def __init__(self,
                 project: str = 'dattavani',
                 queue: str = 'tamonashini-feedback',
                 location: str = 'asia-south1',
                 service_account_file: str = '/tmp/tamonashini-key.json'):

        self.project = project
        self.queue = queue
        self.location = location
        self.service_account_file = service_account_file
        self.client = tasks_v2.CloudTasksClient()
        self.parent = self.client.queue_path(project, location, queue)

    def submit_feedback(self, video_id: str, feedback_type: str, notes: str = '') -> bool:
        """Submit feedback task to Cloud Tasks queue"""

        try:
            task = {
                'http_request': {
                    'http_method': tasks_v2.HttpMethod.POST,
                    'url': f'https://tamonashini.dharmaposhanam.in/feedback',  # Update with actual URL
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        'video_id': video_id,
                        'feedback_type': feedback_type,
                        'notes': notes,
                        'timestamp': datetime.utcnow().isoformat()
                    }).encode()
                }
            }

            # Set task schedule time (immediate)
            now = datetime.utcnow()
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(now)
            task['schedule_time'] = timestamp

            # Create task
            response = self.client.create_task(request={'parent': self.parent, 'task': task})
            print(f"✅ Feedback queued: {video_id} → {feedback_type}")
            print(f"   Task: {response.name}")
            return True

        except Exception as e:
            print(f"❌ Failed to queue feedback: {str(e)}")
            return False

def submit_feedback_to_cloud_tasks(video_id: str, feedback_type: str, notes: str = '') -> bool:
    """Convenience function to submit feedback"""
    try:
        queue = CloudTasksFeedback()
        return queue.submit_feedback(video_id, feedback_type, notes)
    except Exception as e:
        print(f"⚠️  Cloud Tasks not available: {e}")
        print("   Falling back to local feedback storage...")
        return False
