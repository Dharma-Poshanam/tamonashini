# Tamonashini Sentiment Analyzer - Implementation Summary

## What Has Been Built

A **Vertex AI Agent-based sentiment analyzer** that monitors YouTube for negative sentiment content about Ganapathy Sachchidananda Swamiji.

### Components

1. **sentiment_analyzer.py**
   - Main analyzer class using YouTube Data API + Vertex AI
   - Native language support: English, Kannada, Telugu
   - Extracts video metadata, transcripts, and captions
   - Analyzes sentiment and extracts negative phrases
   - Exports results to CSV for legal review

2. **main.py**
   - Entry point for local testing and Cloud deployment
   - Loads environment variables from `.env.local`
   - Configurable search queries

3. **deploy_scheduler.sh**
   - Automates deployment to Google Cloud
   - Creates Cloud Run service (asia-south1/Mumbai)
   - Sets up Cloud Scheduler job (runs every 2 hours)
   - Configures IAM permissions

4. **Dockerfile**
   - Containerized deployment for Cloud Run
   - Python 3.11 with all dependencies

5. **Documentation**
   - README.md: Full feature documentation
   - QUICKSTART.md: 5-minute setup guide
   - This file: Implementation details

## Key Features

### ✅ Multi-language Native Analysis
- **English**: Standard text analysis
- **Kannada**: Unicode range U+0C80–U+0CFF
- **Telugu**: Unicode range U+0C00–U+0C7F
- Vertex AI analyzes each language in its native context

### ✅ BNS 356 Compliance
Results are structured for **Bharatiya Nyaya Sanhita Section 356** (Defamation):
- Imputation of fact (vs. opinion)
- False or reckless statement
- Published
- Damages reputation
- Made knowingly or with rashness

### ✅ Sentiment Analysis
- **Vertex AI Generative AI**: Uses Claude-style models for nuanced understanding
- **Sentiment Score**: -1 (most negative) to 1 (most positive)
- **Negative Phrases Extraction**: Identifies defamatory language
- **Imputation Type**: Categorizes claim type (fraud/crime/misconduct/false accusation)

### ✅ Automated Monitoring
- Searches YouTube continuously (every 2 hours)
- Supports multiple search queries and variations
- Includes alternate spellings (Sachchidananda/Satchidananda)

### ✅ CSV Export for Legal Review
```
video_id | url | title | channel_name | upload_date | language | 
transcript_excerpt | sentiment_score | sentiment_label | negative_phrases | 
imputation_type | view_count | timestamp
```

## Local Testing Checklist

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify `.env.local` has `YOUTUBE_API_KEY`
- [ ] Authenticate: `gcloud auth application-default login`
- [ ] Enable APIs: `gcloud services enable aiplatform.googleapis.com youtube.googleapis.com`
- [ ] Run: `python main.py`
- [ ] Check results: `cat sentiment_analysis_results.csv`

**Estimated runtime: 2-5 minutes for 10 videos**

## Cloud Deployment Checklist

- [ ] Test locally first (see above)
- [ ] Set API key in environment: `export YOUTUBE_API_KEY="..."`
- [ ] Make deploy script executable: `chmod +x deploy_scheduler.sh`
- [ ] Deploy: `bash deploy_scheduler.sh`
- [ ] Verify Cloud Scheduler job created: `gcloud scheduler jobs describe dattavani-sentiment-analyzer --location asia-south1`
- [ ] Manually trigger test run: `gcloud scheduler jobs run dattavani-sentiment-analyzer --location asia-south1`
- [ ] View logs: `gcloud logging read "resource.type=cloud_run_revision" --limit 50`

**Cloud resources:**
- Cloud Run service: `dattavani-sentiment-analyzer` (asia-south1)
- Cloud Scheduler job: `dattavani-sentiment-analyzer` (runs at 0, 2, 4, 6, 8... hours UTC)
- Storage: Results can be uploaded to GCS bucket (optional)

## Search Queries Included

The analyzer searches for:

```python
[
    'Ganapathy Sachchidananda Swamiji',
    'Satchidananda Swami',  # Alternate spelling
    'Dattapeetham Swami',
    'ಗಣಪತಿ ಸತ್ಯನಂದ',  # Kannada
    'గణపతి సత్యానంద',   # Telugu
    'land encroachment Dattapeetham',
    'Ganapathy court case',
    'Sachchidananda fraud',
    'Dattapeetham controversy',
    'Swami Ganapathy case',
]
```

**10+ queries in English, Kannada, and Telugu** ensures comprehensive coverage.

## How It Works

```
┌─────────────────────────────────────────────┐
│ 1. Search YouTube                           │
│    (10 search queries, multiple languages)  │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│ 2. Extract Metadata                         │
│    (Title, channel, upload date, views)     │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│ 3. Get Transcripts & Captions               │
│    (YouTube captions API)                   │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│ 4. Detect Language                          │
│    (English / Kannada / Telugu)             │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│ 5. Vertex AI Sentiment Analysis             │
│    (Native language understanding)          │
├─────────────────────────────────────────────┤
│ Returns:                                    │
│ - Sentiment score (-1 to 1)                 │
│ - Label (negative/neutral/positive)         │
│ - Negative phrases                          │
│ - Imputation type (fraud/crime/etc.)        │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│ 6. Filter & Export (sentiment < -0.3)       │
│    sentiment_analysis_results.csv           │
└────────────────┬────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────┐
│ 7. Legal Team Review                        │
│    (BNS 356 assessment)                     │
└─────────────────────────────────────────────┘
```

## Output Example

```csv
video_id,url,title,channel_name,upload_date,language,transcript_excerpt,sentiment_score,sentiment_label,negative_phrases,imputation_type,view_count,timestamp
abc123,https://youtube.com/watch?v=abc123,Misleading Title,Critic Channel,2026-09-15T10:00:00Z,en,"accused of financial fraud...","-0.85","negative","fraud, deception, scam","fraud","15230","2026-09-17T14:32:45Z"
```

## Important Notes

### ⚠️ Legal Disclaimer
- **All results must be reviewed by Indian legal counsel** before taking action
- Only statements meeting **BNS 356 criteria** are actionable
- Results are for **defensive purposes** (protecting reputation, gathering evidence)
- Not for targeting or harassing content creators

### 🔐 Security
- YouTube API key stored in `.env.local` (local) or Cloud Secret Manager (production)
- Never commit `.env.local` to git
- Use service accounts for Cloud deployment
- Sensitive data never logged

### ⚡ Performance
- **Local**: ~2-5 minutes for 10 videos
- **Cloud**: Runs asynchronously every 2 hours
- **Cost**: Depends on YouTube API quota and Vertex AI usage

## Next Steps

1. **Test locally**
   ```bash
   python main.py
   ```

2. **Review results**
   ```bash
   cat sentiment_analysis_results.csv
   ```

3. **Deploy to Cloud**
   ```bash
   bash deploy_scheduler.sh
   ```

4. **Monitor execution**
   ```bash
   gcloud scheduler jobs describe dattavani-sentiment-analyzer --location asia-south1
   ```

5. **Share with legal team**
   ```bash
   # Copy CSV to legal team
   cp sentiment_analysis_results.csv /path/to/legal/team/
   ```

## Architecture Notes

- **Region**: Mumbai (asia-south1) - ensures compliance with Indian infrastructure
- **Language support**: Native analysis (not translation-based)
- **Sentiment model**: Vertex AI Generative AI (Claude-based)
- **Update frequency**: Every 2 hours (configurable via Cloud Scheduler)

## Support & Troubleshooting

See **QUICKSTART.md** for common issues and solutions.

For detailed feature documentation, see **README.md**.
