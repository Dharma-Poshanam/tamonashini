# Tamonashini Sentiment Analyzer

Monitors YouTube for negative sentiment videos about Ganapathy Sachchidananda Swamiji using Vertex AI's native language analysis (English, Kannada, Telugu).

## Features

- **Multi-language support**: Analyzes content in English, Kannada, and Telugu
- **Vertex AI integration**: Uses Google's Generative AI for native language sentiment analysis
- **BNS 356 compliance**: Focuses on identifying potentially defamatory statements
- **Automated monitoring**: Runs on Google Cloud Scheduler every 2 hours
- **CSV export**: Results stored in `sentiment_analysis_results.csv` for legal review

## Local Testing

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set up Google Cloud authentication
gcloud auth application-default login
```

### Set up .env.local

```bash
# Copy template
cp .env.example .env.local

# Edit with your YouTube API key
# .env.local should contain:
# YOUTUBE_API_KEY=your_api_key_here
```

### Run locally

```bash
python main.py
```

This will:
1. Search YouTube for videos about the specified person
2. Extract transcripts
3. Detect language (English/Kannada/Telugu)
4. Analyze sentiment using Vertex AI
5. Save results to `sentiment_analysis_results.csv`

## Output Format

`sentiment_analysis_results.csv` contains:

| Column | Description |
|--------|-------------|
| video_id | YouTube video ID |
| url | Direct YouTube link |
| title | Video title |
| channel_name | Uploader channel |
| upload_date | Publication date |
| language | Detected language (en/kn/te) |
| transcript_excerpt | First 200 chars of content |
| sentiment_score | -1 (most negative) to 1 (most positive) |
| sentiment_label | negative/neutral/positive |
| negative_phrases | Extracted negative/defamatory phrases |
| imputation_type | Type of claim (fraud/misconduct/crime/etc.) |
| view_count | Video view count |
| timestamp | Analysis timestamp |

## Deployment to Cloud Scheduler

### 1. Deploy to Google Cloud

```bash
# Set your YouTube API key
export YOUTUBE_API_KEY="your_api_key_here"

# Deploy to Cloud Scheduler (runs every 2 hours in Mumbai)
bash deploy_scheduler.sh
```

### 2. View results in Cloud Storage

Results are automatically uploaded to GCS bucket:
```bash
gsutil ls gs://dattavani-sentiment-results/
```

### 3. Monitor execution

```bash
# View scheduler job status
gcloud scheduler jobs describe dattavani-sentiment-analyzer --location asia-south1

# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=dattavani-sentiment-analyzer" --limit 50

# Trigger job manually
gcloud scheduler jobs run dattavani-sentiment-analyzer --location asia-south1
```

## Search Queries

The analyzer searches for:
- "Ganapathy Sachchidananda Swamiji"
- "Satchidananda Swami" (alternate spelling)
- "Dattapeetham Swami"
- "ಗಣಪತಿ ಸತ್ಯನಂದ" (Kannada)
- "గణపతి సత్యానంద" (Telugu)
- "land encroachment Dattapeetham"
- "Ganapathy court case"
- "Sachchidananda fraud"
- "Dattapeetham controversy"
- "Swami Ganapathy case"

## Legal Framework

Results are categorized under **BNS (Bharatiya Nyaya Sanhita) Section 356** - Defamation:

For a claim to be defamatory, it must:
1. Be an imputation of fact (not opinion)
2. Be false or made with recklessness about truth/falsity
3. Be published
4. Damage reputation
5. Be made knowingly or with criminal rashness

**All results should be reviewed by legal counsel before taking action.**

## Language Detection

- **English**: ASCII characters
- **Kannada**: Unicode range U+0C80–U+0CFF
- **Telugu**: Unicode range U+0C00–U+0C7F

## Sentiment Scoring

- **< -0.5**: Highly negative
- **-0.5 to -0.3**: Moderately negative (flagged for review)
- **-0.3 to 0.3**: Neutral
- **> 0.3**: Positive

Only videos with sentiment score < -0.3 are saved to CSV.

## Troubleshooting

### "YOUTUBE_API_KEY not set"
- Ensure `.env.local` exists in project root
- Verify the file contains: `YOUTUBE_API_KEY=your_key_here`

### "No captions found for video"
- Some videos may not have captions available
- Analyzer will use video title as fallback

### "Vertex AI sentiment analysis error"
- Check that Generative AI API is enabled on your GCP project
- Run: `gcloud services enable aiplatform.googleapis.com`

## Architecture

```
YouTube Videos
    ↓
[Search API] → Extract transcripts
    ↓
[Language Detection] → English/Kannada/Telugu
    ↓
[Vertex AI Agent] → Sentiment analysis (native language)
    ↓
[CSV Export] → sentiment_analysis_results.csv
    ↓
[Legal Review] → BNS 356 assessment
```

## Next Steps

1. Test locally: `python main.py`
2. Review results in `sentiment_analysis_results.csv`
3. Deploy to Cloud: `bash deploy_scheduler.sh`
4. Monitor logs for any errors
5. Share CSV results with legal team for defamation assessment
