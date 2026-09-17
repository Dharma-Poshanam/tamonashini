# Official Channels Filter

## What This Does

The analyzer automatically skips videos from official channels to avoid analyzing your own content.

## Official Channels List

The following channels are excluded from sentiment analysis:

| Channel Handle | Channel Name |
|---|---|
| @dattapeetham | Dattapeetham |
| @gurubhavanaadpt | Guru Bhavana |
| @kshtcultural7147 | KSHT Cultural |
| @DallasHanuman | Dallas Hanuman |
| @YogaSangeeta | Yoga Sangeeta |
| @SGSRagaSagara | SGS Raga Sagara |
| @sgsswamiji | SGS Swamiji |

## How It Works

1. When searching YouTube, videos are retrieved from all channels
2. Before analyzing each video, the channel name is checked
3. If the channel matches any official channel (partial or full match, case-insensitive), the video is skipped
4. A log message shows which videos are being skipped

## Example Output

```
INFO:__main__:Found 10 videos
INFO:__main__:Analyzing 140 videos (title-first strategy)...
INFO:__main__:Skipping abc123 - Official channel: Yoga Sangeeta
INFO:__main__:Video def456: negative (-0.65)
INFO:__main__:Skipping ghi789 - Official channel: Dattapeetham
```

## Modifying the List

To add or remove official channels, edit `sentiment_analyzer_v2.py`:

```python
class TamonashiniSentimentAnalyzer:
    OFFICIAL_CHANNELS = {
        '@dattapeetham',
        # Add new channels here
        '@yournewchannel',
    }
```

Then update both the handle (with @) and display name for better matching.

## Why This Matters

- **Avoids self-analysis**: Your own videos won't be flagged as negative
- **Focuses on competitors/critics**: Analysis targets external content only
- **Cleaner reports**: CSV results only contain third-party content
- **Faster processing**: Skipped videos don't consume API calls

## Technical Details

The filter uses case-insensitive partial matching:
- `@dattapeetham` matches "Dattapeetham Official", "DATTAPEETHAM", etc.
- `Dattapeetham` matches "Dattapeetham Ashram", "Dattapeetham Official", etc.
- Matching is done in both directions to catch variations

## Checking the Filter

View which channels are being skipped:
```bash
python main_v2.py 2>&1 | grep "Skipping"
```

This shows all official channel videos excluded from analysis.
