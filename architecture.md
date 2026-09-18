# Tamonashini Architecture

**Version**: 2.0 (Feedback-Driven Improvement)  
**Last Updated**: September 2026  
**Owner**: Legal Monitoring Team

---

## Executive Summary

Tamonashini is a **real-time YouTube sentiment monitoring system** that detects and tracks negative sentiment content about Ganapathy Sachchidananda Swamiji across multiple languages (English, Kannada, Telugu). It combines YouTube video scraping, native-language sentiment analysis via Vertex AI, email-based human feedback, and SQLite tracking to create a closed-loop system for continuous model improvement.

---

## System Architecture

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    YOUTUBE CONTENT LAYER                    │
│  (Videos about target topic, multilingual, streaming)       │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  YouTube Data API Search           │
        │  - 14 search query variations      │
        │  - Includes alternate spellings    │
        │  - Language: en, kn, te            │
        └────────────┬─────────────────────┘
                     │
                     ▼
    ┌─────────────────────────────────────┐
    │  Content Extraction                 │
    │  - Transcripts (YouTube captions)    │
    │  - Video metadata (title, channel)   │
    │  - View counts, upload dates         │
    └────────────┬──────────────────────┘
                 │
                 ▼
    ┌─────────────────────────────────────┐
    │  Language Detection                 │
    │  - Unicode range analysis           │
    │  - 3 languages: EN, KN, TE          │
    │  - Fallback: English                │
    └────────────┬──────────────────────┘
                 │
                 ▼
    ┌─────────────────────────────────────┐
    │  Sentiment Analysis                 │
    │  - Vertex AI (Claude models)        │
    │  - Native language analysis         │
    │  - BNS 356 compliance check         │
    │  - Defamatory phrase extraction     │
    └────────────┬──────────────────────┘
                 │
         ┌───────┴───────┐
         │               │
         ▼               ▼
    ┌─────────┐    ┌──────────────┐
    │Negative │    │Neutral/      │
    │Videos   │    │Positive      │
    │(score < │    │(ignored)     │
    │ -0.3)   │    │              │
    └────┬────┘    └──────────────┘
         │
         ▼
    ┌──────────────────────────────────┐
    │  SQLite Duplicate Check          │
    │  tamonashini_videos.db           │
    │  - Track sent videos             │
    │  - Avoid duplicate emails        │
    └────┬───────────────────────────┘
         │
    ┌────┴──────────────────────┐
    │New video                  │
    │(not in database)          │
    └────┬──────────────────────┘
         │
         ▼
    ┌──────────────────────────────────┐
    │  Email Generation & Sending      │
    │  - HTML5 template (Qwen)         │
    │  - Interactive feedback buttons  │
    │  - Cloud Tasks queue integration │
    │  - SMTP delivery                 │
    └────┬───────────────────────────┘
         │
         ▼
    ┌──────────────────────────────────┐
    │  Human Feedback Loop             │
    │  - Accurate / Incorrect buttons  │
    │  - Cloud Tasks webhook           │
    │  - Feedback server listener      │
    └────┬───────────────────────────┘
         │
         ▼
    ┌──────────────────────────────────┐
    │  Feedback Handler                │
    │  feedback_handler.py             │
    │  - Queue feedback records        │
    │  - Store in feedback DB          │
    └────┬───────────────────────────┘
         │
         ▼
    ┌──────────────────────────────────┐
    │  Model Improvement Loop          │
    │  feedback_analyzer.py            │
    │  - Analyze A/B test results      │
    │  - Refine sentiment thresholds   │
    │  - Improve accuracy metrics      │
    └──────────────────────────────────┘
```

---

## Component Architecture

### 1. Core Processing Pipeline

#### `tamonashini_scheduler.py` (Entry Point)
**Role**: Orchestrates daily sentiment analysis runs  
**Key Responsibilities**:
- Loads environment configuration (.env.local)
- Triggers YouTube search across all query variations
- Orchestrates content extraction and sentiment analysis
- Manages SQLite database for deduplication
- Generates and sends HTML email reports
- Handles error logging and retry logic

**Key Classes**:
- `VideoDatabase`: SQLite operations for tracking sent videos
- `TamonashiniScheduler`: Main orchestration logic

**Environment Variables**:
```
YOUTUBE_API_KEY      # YouTube Data API v3 key (required)
GOOGLE_APPLICATION_CREDENTIALS  # GCP service account (for Vertex AI)
EMAIL_USER           # Sender email (Gmail)
EMAIL_PASSWORD       # Gmail app password
EMAIL_TO             # Recipient email
SMTPLIB_SMTP_HOST    # SMTP server (smtp.gmail.com)
SMTPLIB_SMTP_PORT    # SMTP port (587)
```

---

#### `sentiment_analyzer_qwen.py` (Qwen-Based Analysis)
**Role**: Lightweight sentiment analysis using Qwen models  
**Status**: Active (replaces Vertex AI for cost optimization)  
**Key Features**:
- Local vLLM inference (no cloud API calls)
- Multilingual support: English, Kannada, Telugu
- Extracts negative/defamatory phrases
- Categorizes imputation type (fraud, crime, misconduct)
- Returns sentiment score (-1.0 to 1.0) and label

**Sentiment Thresholds**:
```
< -0.5   : Highly negative (flagged)
-0.5 to -0.3 : Moderately negative (saved to CSV)
-0.3 to 0.3  : Neutral (filtered out)
> 0.3    : Positive (filtered out)
```

**Note**: Original Vertex AI implementation in `sentiment_analyzer_v2.py` available for native language nuance if needed.

---

### 2. Email & Feedback System

#### `email_template.py`
**Role**: Generates HTML5 email with interactive feedback buttons  
**Features**:
- Responsive design (mobile + desktop)
- Clickable "Accurate" / "Incorrect" buttons
- Cloud Tasks webhook integration
- Video details (title, channel, transcript excerpt)
- Sentiment score and negative phrases displayed

**Email Structure**:
```
Header: Tamonashini Daily Report
├── New Videos Found: N
├── Report Date: YYYY-MM-DD
│
Video Cards (sorted by sentiment score, most negative first)
├── Title, Channel, Upload Date
├── Sentiment Score & Label
├── Transcript excerpt (first 200 chars)
├── Negative/Defamatory phrases
└── Feedback buttons → Cloud Tasks webhook
```

---

#### `feedback_server.py` (Flask App)
**Role**: HTTP endpoint for email button clicks  
**Endpoints**:
- `GET/POST /feedback?video_id=X&type=Y` — Record feedback from email
- `GET /health` — Health check for monitoring
- `GET /` — Info page

**Security**:
- XSS protection via `escape()` on user input
- CSRF implicit (stateless design)
- HTTPS required in production

**Deployment**: Can run locally or in Cloud Run container

---

#### `feedback_handler.py`
**Role**: Processes and queues user feedback  
**Flow**:
1. Receives feedback from `/feedback` endpoint
2. Validates video_id and feedback_type (accurate/incorrect)
3. Appends to feedback queue or database
4. Returns success/error JSON

**Storage**: Feedback logged for later analysis

---

#### `cloud_tasks_feedback.py`
**Role**: Manages Google Cloud Tasks queue integration  
**Features**:
- Creates Cloud Tasks for each video analysis
- Webhook delivery to feedback_server.py
- Retry logic (exponential backoff)
- DLQ (Dead Letter Queue) for failed deliveries

**Flow**:
```
tamonashini_scheduler → cloud_tasks_feedback
    ↓
[Create Task] → Cloud Tasks Queue
    ↓
(On schedule) → POST /feedback webhook
    ↓
feedback_server → feedback_handler
    ↓
Store feedback record
```

---

### 3. Model Improvement Loop

#### `feedback_analyzer.py`
**Role**: Analyzes feedback to improve model accuracy  
**Responsibilities**:
- Reads feedback records from database
- Calculates A/B test metrics (accuracy, precision, recall)
- Identifies false positives / false negatives
- Recommends sentiment threshold adjustments
- Generates improvement report

**A/B Testing Strategy**:
- **Version A**: Original thresholds (-0.3 cutoff)
- **Version B**: Adjusted thresholds (based on feedback)
- Metrics: Accuracy, Precision, Recall, F1-score

**Output**:
```json
{
  "version_a": {
    "true_positives": 45,
    "false_positives": 3,
    "false_negatives": 2,
    "accuracy": 0.93
  },
  "version_b": {
    "true_positives": 46,
    "false_positives": 1,
    "false_negatives": 3,
    "accuracy": 0.94
  },
  "recommendation": "Adopt Version B (lower false positive rate)"
}
```

---

## Data Schema

### SQLite: `tamonashini_videos.db`

```sql
CREATE TABLE sent_videos (
    video_id TEXT PRIMARY KEY,
    title TEXT,
    channel TEXT,
    url TEXT,
    sent_date TIMESTAMP,
    sentiment_score REAL,
    sentiment_label TEXT
);

-- Indexes for fast lookup
CREATE INDEX idx_video_id ON sent_videos(video_id);
CREATE INDEX idx_sent_date ON sent_videos(sent_date DESC);
```

### Feedback Database (TBD)
```sql
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT NOT NULL,
    feedback_type TEXT CHECK(feedback_type IN ('accurate', 'incorrect')),
    notes TEXT,
    user_email TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(video_id) REFERENCES sent_videos(video_id)
);
```

### CSV Output: `sentiment_analysis_results.csv`

| Column | Type | Description |
|--------|------|-------------|
| video_id | TEXT | YouTube video ID |
| url | TEXT | Full YouTube video URL |
| title | TEXT | Video title |
| channel_name | TEXT | Uploader channel |
| upload_date | TEXT | Publication date |
| language | TEXT | Detected language (en/kn/te) |
| transcript_excerpt | TEXT | First 200 chars of content |
| sentiment_score | FLOAT | -1.0 (negative) to 1.0 (positive) |
| sentiment_label | TEXT | negative / neutral / positive |
| negative_phrases | TEXT | CSV of defamatory phrases |
| imputation_type | TEXT | fraud / crime / misconduct / etc. |
| view_count | INT | Video view count |
| timestamp | DATETIME | Analysis timestamp |

---

## Deployment Architecture

### Local Development

```
Development Machine
├── .env.local (YouTube API key, email credentials)
├── Python 3.11+ with dependencies
├── YouTube Data API (read-only access)
├── Vertex AI / Qwen (local inference)
├── SQLite (tamonashini_videos.db)
└── SMTP (Gmail credentials)
```

**Run Command**:
```bash
python tamonashini_scheduler.py
```

---

### Cloud Deployment (GCP)

#### Architecture Diagram
```
┌─────────────────────────────────────────────┐
│          CLOUD SCHEDULER (asia-south1)      │
│  Job: dattavani-sentiment-analyzer          │
│  Trigger: Every 2 hours (UTC 0, 2, 4, ...)  │
└──────────────────┬──────────────────────────┘
                   │
                   │ HTTP POST
                   ▼
        ┌──────────────────────┐
        │   CLOUD RUN          │
        │ dattavani-sentiment- │
        │ analyzer (asia-south1)
        ├──────────────────────┤
        │ - Python 3.11        │
        │ - Qwen (vLLM)        │
        │ - YouTube API        │
        │ - SQLite persistent  │
        └──────────┬───────────┘
                   │
        ┌──────────┴──────────────┐
        │                         │
        ▼                         ▼
    ┌────────┐             ┌─────────────┐
    │ Secret │             │  Cloud      │
    │ Manager│             │  Storage    │
    │(API    │             │  (Results)  │
    │keys)   │             └─────────────┘
    └────────┘
        │
        │ SMTP
        ▼
    ┌─────────────────┐
    │ Gmail SMTP      │
    │ (Email sending) │
    └─────────────────┘
        │
        │ HTTP
        ▼
    ┌──────────────────────┐
    │  Feedback Server     │
    │  (Cloud Run / Local) │
    │  /feedback endpoint  │
    └──────────────────────┘
```

#### Key GCP Services

| Service | Region | Role |
|---------|--------|------|
| Cloud Scheduler | asia-south1 | Trigger job every 2 hours |
| Cloud Run | asia-south1 | Execute sentiment analysis |
| Secret Manager | asia-south1 | Store API keys securely |
| Cloud Logging | asia-south1 | Monitor execution logs |
| Cloud Storage | asia-south1 | (Optional) Store CSV results |

**Region Rationale**: asia-south1 (Mumbai) for data residency and latency (India-facing app per org standards).

#### Deployment Commands

```bash
# 1. Create Cloud Run service
gcloud run deploy dattavani-sentiment-analyzer \
  --region asia-south1 \
  --image gcr.io/PROJECT/tamonashini:latest \
  --memory 2Gi \
  --timeout 3600 \
  --set-env-vars "YOUTUBE_API_KEY=$(gcloud secrets versions access latest --secret=youtube-api-key)"

# 2. Create Cloud Scheduler job
gcloud scheduler jobs create pubsub dattavani-sentiment-analyzer \
  --location asia-south1 \
  --schedule "0 */2 * * *" \  # Every 2 hours
  --http-method GET \
  --uri "https://dattavani-sentiment-analyzer-HASH.run.app/run" \
  --headers "Content-Type=application/json"

# 3. Monitor logs
gcloud logging read \
  'resource.type=cloud_run_revision AND resource.labels.service_name=dattavani-sentiment-analyzer' \
  --limit 50 --format json
```

---

## Technology Stack

### Core Technologies

| Layer | Technology | Purpose | Version |
|-------|-----------|---------|---------|
| **Language** | Python 3.11+ | Backend logic | 3.11 |
| **Web Framework** | Flask | HTTP feedback server | 2.x |
| **Database** | SQLite 3 | Video deduplication | — |
| **Video Source** | YouTube Data API v3 | Search & metadata | v3 |
| **NLP / Sentiment** | Qwen (vLLM) | Local inference | Latest |
| **Alternative NLP** | Vertex AI Generative AI | Cloud-based analysis | Latest |
| **Containerization** | Docker | Cloud Run deployment | 20.x |
| **Email** | SMTP (Gmail) | Report delivery | — |
| **Task Queue** | Cloud Tasks | Feedback webhooks | Google Cloud |
| **IaC** | Terraform / Cloud Build | Infrastructure | Latest |

### Python Dependencies

See `requirements.txt`:
- `google-cloud-aiplatform` — Vertex AI SDK
- `google-api-python-client` — YouTube Data API
- `flask` — Feedback server
- `python-dotenv` — Environment variables
- `requests` — HTTP client for vLLM

---

## Security & Compliance

### Data Privacy

1. **PII Handling**: No personal data stored except video metadata (public)
2. **Email Credentials**: Stored in `.env.local` (git-ignored), promoted to Secret Manager in prod
3. **API Keys**: YouTube API key in Secret Manager; accessed at runtime
4. **HTTPS**: All Cloud Run endpoints require HTTPS

### BNS 356 Compliance (Defamation Law)

Results categorized to support legal review:
- **Imputation Type**: fraud, crime, misconduct, false accusation
- **Defamatory Phrases**: Extracted and highlighted
- **Sentiment Score**: Quantifies negativity for legal threshold

**Not Legal Advice**: All results reviewed by legal counsel before action.

### Secure Deployment Practices

✅ No hardcoded secrets (all in Secret Manager)  
✅ XSS protection in feedback_server.py  
✅ SQL parameterization in SQLite queries  
✅ Service account IAM (Cloud Run → APIs)  
✅ Audit logging (Cloud Logging)  

---

## Failure Modes & Resilience

| Failure | Impact | Mitigation |
|---------|--------|-----------|
| YouTube API quota exceeded | No videos found | Implement exponential backoff, quota monitoring |
| Network timeout (vLLM) | Analysis blocked | Fallback to Qwen API or skip batch |
| Email delivery failure | Report not sent | Retry via SMTP, Cloud Tasks DLQ |
| SQLite database locked | Duplicate check fails | WAL mode (Write-Ahead Logging) enabled |
| Cloud Run timeout (>3600s) | Incomplete analysis | Batch processing (max 100 videos/run) |
| Invalid video metadata | Incomplete record | Fallback to title-only analysis |

---

## Monitoring & Observability

### Cloud Logging

**Log Queries**:
```bash
# All errors
gcloud logging read 'severity=ERROR AND resource.type=cloud_run_revision' --limit 50

# Job execution summary
gcloud logging read 'resource.type=cloud_scheduler_job' --limit 20

# Feedback received
gcloud logging read 'textPayload=~"Feedback recorded"' --limit 20
```

### Key Metrics

1. **Videos Analyzed**: Count per run
2. **Negative Videos Found**: Count with score < -0.3
3. **Email Delivery Success Rate**: Sent / Total
4. **Feedback Rate**: Clicks / Emails sent
5. **Model Accuracy**: True Positives / (TP + FP)

### Alerting (Recommended)

- **No videos found** (3 consecutive runs) → Alert
- **Email delivery failure** (2+ errors) → Alert
- **Cloud Run timeout** → Alert
- **Feedback accuracy < 85%** → Investigation

---

## Development Workflow

### Local Testing
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up credentials
cp .env.example .env.local
# Edit .env.local with API keys

# 3. Run sentiment analyzer
python tamonashini_scheduler.py

# 4. Test feedback server (separate terminal)
python feedback_server.py --port 9000
# Click email buttons to trigger /feedback endpoint
```

### Adding a New Search Query
1. Edit `tamonashini_scheduler.py` → `SEARCH_QUERIES` list
2. Test locally with `python tamonashini_scheduler.py`
3. Monitor for false positives in email reports
4. Commit with PR (link to feedback analysis)

### Updating Sentiment Thresholds
1. Collect feedback via email buttons (≥100 samples)
2. Run `feedback_analyzer.py` to generate A/B report
3. Update `SENTIMENT_THRESHOLD` in `sentiment_analyzer_qwen.py`
4. Test on historical data
5. Deploy to Cloud Run (new image)

---

## Known Limitations & Future Work

### Current Limitations
- **Language Coverage**: English, Kannada, Telugu only (not other Indic languages)
- **Transcripts Only**: Doesn't analyze video images/graphics
- **Real-time Lag**: 2-hour batch delay (not streaming)
- **No Fact-Checking**: Flags negative statements, doesn't verify truth
- **Email-Only Feedback**: No API for programmatic feedback submission

### Recommended Improvements
1. **Add Tamil / Malayalam support** — Expand language coverage
2. **Implement DLP scanning** — Detect personal contact info in transcripts
3. **Fine-tune Qwen locally** — Improve defamation detection accuracy
4. **Real-time streaming** — Move from batch to streaming (Apache Kafka)
5. **Legal integration** — Auto-forward to legal team Slack channel
6. **Video-level analysis** — Analyze images + audio + transcripts
7. **Fact-checking API** — Integrate fact-checking service (Factly, ClaimBuster)

---

## References

### Internal Documents
- `README.md` — Feature overview and user guide
- `QUICKSTART.md` — 5-minute setup guide
- `IMPLEMENTATION_SUMMARY.md` — Detailed feature breakdown
- `DAILY_SETUP.md` — Maintenance checklist
- `requirements.txt` — Python dependencies

### External References
- [YouTube Data API v3 Documentation](https://developers.google.com/youtube/v3)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [BNS 2023 Section 356 (Defamation)](https://www.indiacode.nic.in/)
- [Qwen Model Documentation](https://github.com/QwenLM/Qwen)

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 2.0 | Sep 2026 | Added feedback loop, email HTML5, Cloud Tasks integration |
| 1.5 | Aug 2026 | Switched to Qwen for cost optimization |
| 1.0 | Jul 2026 | Initial Vertex AI sentiment analyzer |

---

**Last reviewed**: September 2026  
**Next review**: December 2026
