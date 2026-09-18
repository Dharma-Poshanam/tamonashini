#!/usr/bin/env python3
"""
Tamonashini Feedback Analyzer
Analyzes feedback to improve sentiment analysis accuracy
Provides dynamic threshold and prompt refinements
"""

import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta

class FeedbackAnalyzer:
    """Analyzes feedback patterns and recommends improvements"""

    def __init__(self, db_path: str = "tamonashini_videos.db"):
        self.db_path = db_path

    def get_feedback_accuracy_by_score(self, days: int = 30):
        """Calculate accuracy metrics by sentiment score range"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get videos with feedback from last N days
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        c.execute('''
            SELECT sv.sentiment_score, vf.feedback_type
            FROM sent_videos sv
            JOIN video_feedback vf ON sv.video_id = vf.video_id
            WHERE vf.timestamp > ?
            ORDER BY sv.sentiment_score ASC
        ''', (cutoff_date.isoformat(),))

        results = c.fetchall()
        conn.close()

        # Group by score range and analyze
        buckets = defaultdict(lambda: {'correct': 0, 'false_positive': 0, 'uncertain': 0, 'total': 0})

        for score, feedback_type in results:
            # Round to nearest 0.1 for bucketing
            bucket_key = f"{score:.1f}"
            buckets[bucket_key][feedback_type] += 1
            buckets[bucket_key]['total'] += 1

        # Calculate accuracy for each bucket
        accuracy = {}
        for bucket, counts in sorted(buckets.items()):
            if counts['total'] > 0:
                correct_pct = (counts['correct'] / counts['total']) * 100
                accuracy[bucket] = {
                    'correct': counts['correct'],
                    'false_positive': counts['false_positive'],
                    'uncertain': counts['uncertain'],
                    'total': counts['total'],
                    'accuracy_pct': correct_pct
                }

        return accuracy

    def get_false_positive_examples(self, limit: int = 10):
        """Get examples of false positives for prompt refinement"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT sv.video_id, sv.title, sv.sentiment_score, sv.sentiment_label
            FROM sent_videos sv
            JOIN video_feedback vf ON sv.video_id = vf.video_id
            WHERE vf.feedback_type = 'false_positive'
            ORDER BY sv.sentiment_score DESC
            LIMIT ?
        ''', (limit,))

        videos = c.fetchall()
        conn.close()
        return videos

    def get_correct_examples(self, limit: int = 10):
        """Get examples of correctly identified negatives for prompt refinement"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT sv.video_id, sv.title, sv.sentiment_score, sv.sentiment_label
            FROM sent_videos sv
            JOIN video_feedback vf ON sv.video_id = vf.video_id
            WHERE vf.feedback_type = 'correct'
            ORDER BY sv.sentiment_score ASC
            LIMIT ?
        ''', (limit,))

        videos = c.fetchall()
        conn.close()
        return videos

    def recommend_threshold(self, min_accuracy: float = 80.0):
        """Recommend optimal threshold based on feedback accuracy"""
        accuracy = self.get_feedback_accuracy_by_score()

        if not accuracy:
            return None, "No feedback data available"

        # Find threshold where accuracy is above min_accuracy
        sorted_buckets = sorted(accuracy.items(), key=lambda x: float(x[0]))

        for score_str, metrics in sorted_buckets:
            score = float(score_str)
            if metrics['accuracy_pct'] >= min_accuracy:
                return score, metrics

        # If no bucket meets threshold, return the most accurate one
        best_bucket = max(sorted_buckets, key=lambda x: x[1]['accuracy_pct'])
        return float(best_bucket[0]), best_bucket[1]

    def generate_refined_prompt_context(self):
        """Generate prompt context based on feedback"""
        false_positives = self.get_false_positive_examples(5)
        correct_examples = self.get_correct_examples(5)

        context = "\n\nFEEDBACK-INFORMED GUIDANCE:\n"
        context += "=" * 70 + "\n"

        if false_positives:
            context += "\n❌ NOT negative (false positives to avoid):\n"
            for vid_id, title, score, label in false_positives:
                context += f"  • \"{title}\" (Score: {score:.2f}) - Motivational/devotional, not controversial\n"

        if correct_examples:
            context += "\n✓ TRULY negative (correct identifications):\n"
            for vid_id, title, score, label in correct_examples:
                context += f"  • \"{title}\" (Score: {score:.2f}) - Contains accusations/controversy\n"

        return context

    def get_report(self):
        """Generate comprehensive feedback report"""
        accuracy = self.get_feedback_accuracy_by_score()
        recommended_threshold, threshold_metrics = self.recommend_threshold()

        report = "\n" + "=" * 70
        report += "\n📊 TAMONASHINI FEEDBACK ANALYSIS REPORT\n"
        report += "=" * 70 + "\n"

        report += f"\nAccuracy by Score Range (Last 30 days):\n"
        report += "-" * 70 + "\n"
        report += f"{'Score':>8} {'Correct':>8} {'False +':>8} {'Uncertain':>10} {'Accuracy':>10}\n"
        report += "-" * 70 + "\n"

        for score_str in sorted(accuracy.keys(), key=float):
            metrics = accuracy[score_str]
            report += f"{score_str:>8} {metrics['correct']:>8} {metrics['false_positive']:>8} "
            report += f"{metrics['uncertain']:>10} {metrics['accuracy_pct']:>9.1f}%\n"

        report += "-" * 70 + "\n"

        if recommended_threshold:
            report += f"\n🎯 Recommended Threshold: {recommended_threshold:.2f}\n"
            report += f"   Accuracy at this threshold: {threshold_metrics['accuracy_pct']:.1f}%\n"
            report += f"   ({threshold_metrics['correct']} correct, {threshold_metrics['false_positive']} false positives)\n"

        report += f"\n📝 Context for Model Refinement:\n"
        report += self.generate_refined_prompt_context()

        report += "\n" + "=" * 70 + "\n"

        return report

    def export_finetuning_data(self, output_file: str = 'finetuning_data.jsonl'):
        """Export feedback data in format suitable for fine-tuning"""
        import json

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get all videos with feedback
        c.execute('''
            SELECT sv.video_id, sv.title, sv.channel, sv.sentiment_score,
                   vf.feedback_type, vf.notes
            FROM sent_videos sv
            JOIN video_feedback vf ON sv.video_id = vf.video_id
            ORDER BY sv.sentiment_score ASC
        ''')

        videos = c.fetchall()
        conn.close()

        # Convert to fine-tuning format (instruction/output pairs)
        finetuning_examples = []
        for vid_id, title, channel, score, feedback_type, notes in videos:
            # Determine if the original classification was correct
            is_correct = feedback_type == 'correct'

            example = {
                'messages': [
                    {
                        'role': 'user',
                        'content': f'Analyze this YouTube video:\nTitle: "{title}"\nChannel: "{channel}"\n\nIs it negative/controversial content about Ganapaty Sachchidananda Swamiji?'
                    },
                    {
                        'role': 'assistant',
                        'content': f'Sentiment: {"NEGATIVE" if is_correct and score < -0.65 else "NOT NEGATIVE"}\nScore: {score:.2f}\nCorrect: {is_correct}'
                    }
                ]
            }

            if notes:
                example['metadata'] = {'notes': notes, 'video_id': vid_id}

            finetuning_examples.append(example)

        # Write to JSONL file
        with open(output_file, 'w') as f:
            for example in finetuning_examples:
                f.write(json.dumps(example) + '\n')

        return len(finetuning_examples), output_file

def main():
    """CLI interface for feedback analysis"""
    import sys

    analyzer = FeedbackAnalyzer()

    if len(sys.argv) < 2:
        command = 'report'
    else:
        command = sys.argv[1]

    if command == 'report':
        print(analyzer.get_report())
    elif command == 'threshold':
        threshold, metrics = analyzer.recommend_threshold()
        if threshold:
            print(f"Recommended threshold: {threshold:.2f}")
            print(f"Accuracy: {metrics['accuracy_pct']:.1f}%")
        else:
            print("No recommendation available")
    elif command == 'prompt-context':
        print(analyzer.generate_refined_prompt_context())
    elif command == 'export-finetuning':
        count, path = analyzer.export_finetuning_data()
        print(f"✅ Exported {count} examples to {path}")
        print("   Ready for fine-tuning!")
    else:
        print("Usage: python3 feedback_analyzer.py [report|threshold|prompt-context|export-finetuning]")
        return 1

    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main())
