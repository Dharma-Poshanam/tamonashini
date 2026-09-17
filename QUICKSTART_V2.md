# Quick Start - Sentiment Analyzer v2

## What's New

**Two-phase analysis:**
1. **Phase 1**: Title analysis (fast, always runs)
2. **Phase 2**: Full video analysis (optional, only for negative titles)

## 5-Minute Setup

### 1. Install & Authenticate
```bash
cd /projects/yogasangeeta/dattavani-sentiment-analyzer
pip install -r requirements.txt
gcloud auth application-default login
gcloud config set project dattavani
gcloud services enable aiplatform.googleapis.com youtube.googleapis.com
```

### 2. Verify .env.local
```bash
cat .env.local
# Should show: YOUTUBE_API_KEY=AQ.Ab8RN...
```

### 3. Run Analysis

**Option A: Title Analysis Only** (Fastest, Default)
```bash
python main_v2.py
```

**Option B: Title + Full Video Analysis** (Comprehensive)
```bash
ANALYZE_FULL_VIDEO=true python main_v2.py
```

### 4. Check Results
```bash
cat sentiment_analysis_results.csv
```

## Understanding Output

| Column | Meaning |
|--------|---------|
| `title_sentiment_score` | How negative is the title (-1 to 1) |
| `title_sentiment_label` | negative/neutral/positive |
| `title_negative_phrases` | Keywords detected in title |
| `full_video_sentiment_score` | Score from full video (if Phase 2 enabled) |
| `defamatory_claims` | Specific false claims (if Phase 2 enabled) |

## Two-Phase Explanation

### Phase 1: Title Analysis (Required)
```
Video Title: "Swami Ganapathy Accused of Land Fraud"
                    ↓
            Gemini Flash Analysis
                    ↓
Sentiment: -0.8 (highly_negative)
Phrases: ["accused", "fraud"]
```
✅ Detected! Proceed to Phase 2 if enabled.

### Phase 2: Full Video Analysis (Optional)
Only runs if:
1. Phase 1 title score < -0.3 (negative), AND
2. `ANALYZE_FULL_VIDEO=true`

```
Full Video Content
        ↓
Gemini Pro Analysis
        ↓
Defamatory Claims:
- "Court case was rigged" (timestamp 2:15)
- "Stole land from poor farmers" (timestamp 5:30)
Language: Kannada (detected)
```

## Cost Comparison

| Mode | Cost/Video | Time/Video | Videos/Day |
|------|-----------|----------|-----------|
| Title only | ~$0.0005 | ~3 sec | 1000+ |
| Title + Video | ~$0.002 | ~1-2 min | 100-200 |

## Performance Tips

**For quick surveys:**
```bash
python main_v2.py
# ~10-20 seconds for 140 videos
```

**For detailed analysis:**
```bash
ANALYZE_FULL_VIDEO=true python main_v2.py
# ~20-30 minutes for 140 videos
```

## Troubleshooting

### "No negative videos found"
- Titles might not have obvious negative keywords
- Try: `ANALYZE_FULL_VIDEO=true` for deeper analysis
- Or review the CSV - scores might be borderline

### "Analyzer is slow"
- Title-only mode: Should be very fast (<1 min for 100 videos)
- Full video mode: Expected 1-2 min per video
- Use title-only for initial scan, then full mode for promising videos

### "API Error: youtube.apiQuotaExceeded"
- YouTube API quota is 10,000 units/day
- Search uses ~100 units per video
- In title-only mode, can do ~100 videos comfortably
- Wait 24 hours or upgrade quota in Google Cloud Console

## Deploy to Cloud

Once happy with local results:

```bash
# Make deploy script executable
chmod +x deploy_scheduler.sh

# Deploy (runs every 2 hours in Mumbai)
bash deploy_scheduler.sh

# Set to use full video analysis in Cloud
# Edit deploy_scheduler.sh to add:
# --set-env-vars "ANALYZE_FULL_VIDEO=false"
```

## Next Steps

1. ✅ Run title-only analysis
2. ✅ Review CSV results
3. ✅ If needed, run with `ANALYZE_FULL_VIDEO=true` for deep analysis
4. ✅ Share CSV with legal team
5. ✅ Deploy to Cloud Scheduler

See `CHANGELOG.md` for detailed v2 updates.
