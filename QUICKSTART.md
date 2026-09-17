# Quick Start Guide

## Local Testing (5 minutes)

### 1. Install dependencies
```bash
cd /projects/yogasangeeta/dattavani-sentiment-analyzer
pip install -r requirements.txt
```

### 2. Verify .env.local exists
```bash
cat .env.local
# Should show: YOUTUBE_API_KEY=your_api_key_here
```

### 3. Authenticate with Google Cloud
```bash
gcloud auth application-default login
gcloud config set project dattavani
```

### 4. Enable required APIs
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable youtube.googleapis.com
```

### 5. Run the analyzer
```bash
python main.py
```

Expected output:
```
INFO:__main__:Searching YouTube for: Ganapathy Sachchidananda Swamiji
INFO:__main__:Found 10 videos
INFO:__main__:Analyzing 10 videos...
INFO:__main__:Analysis complete. Results saved to sentiment_analysis_results.csv
```

### 6. Check results
```bash
cat sentiment_analysis_results.csv
# Opens CSV with sentiment analysis results
```

## Understanding the Results

Each row in `sentiment_analysis_results.csv` represents a video analyzed:

- **sentiment_score**: -1 to 1 (lower = more negative)
- **sentiment_label**: negative/neutral/positive
- **negative_phrases**: Phrases that triggered negative sentiment
- **imputation_type**: What type of claim is being made (fraud, crime, misconduct, etc.)

**Only videos with sentiment_score < -0.3 are saved.**

## Next: Deploy to Cloud Scheduler

Once you're satisfied with local results:

```bash
# Make deploy script executable
chmod +x deploy_scheduler.sh

# Deploy to Google Cloud (runs every 2 hours in Mumbai)
bash deploy_scheduler.sh
```

This will:
1. Build and deploy a Cloud Run service
2. Set up a Cloud Scheduler job to run every 2 hours
3. Automatically upload results to Cloud Storage

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'google'"
```bash
pip install --upgrade google-api-python-client google-generativeai google-cloud-aiplatform
```

### Error: "YOUTUBE_API_KEY not set"
- Verify `.env.local` exists and has correct API key
- Run: `cat .env.local`

### Error: "No captions found for video"
- This is normal - some videos don't have captions
- Analyzer uses video title as fallback

### Error: "Vertex AI sentiment analysis error"
- Ensure Generative AI API is enabled:
  ```bash
  gcloud services enable aiplatform.googleapis.com
  ```

## Support

For questions about:
- **Sentiment analysis**: See README.md
- **Legal framework**: See "Legal Framework" section in README.md
- **Deployment**: See "Deployment to Cloud Scheduler" in README.md
