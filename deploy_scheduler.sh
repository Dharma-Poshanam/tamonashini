#!/bin/bash
# Deploy sentiment analyzer to Google Cloud Scheduler
# Runs every 2 hours in Mumbai region

set -e

PROJECT_ID="dattavani"
REGION="asia-south1"
JOB_NAME="tamonashini"
SCHEDULE="0 */2 * * *"  # Every 2 hours
SERVICE_ACCOUNT="tamonashini@${PROJECT_ID}.iam.gserviceaccount.com"
CLOUD_RUN_SERVICE="tamonashini"

echo "🚀 Deploying Tamonashini Sentiment Analyzer to Cloud Scheduler..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Schedule: $SCHEDULE (every 2 hours)"

# Set project
gcloud config set project $PROJECT_ID

# 1. Create Cloud Run service (if not exists)
echo "📦 Building and deploying Cloud Run service..."
gcloud run deploy $CLOUD_RUN_SERVICE \
  --source . \
  --region $REGION \
  --memory 4Gi \
  --timeout 3600 \
  --no-allow-unauthenticated \
  --set-env-vars "YOUTUBE_API_KEY=${YOUTUBE_API_KEY}" \
  --platform managed

# 2. Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe $CLOUD_RUN_SERVICE --region $REGION --format 'value(status.url)')
echo "Cloud Run service URL: $SERVICE_URL"

# 3. Create or update Cloud Scheduler job
echo "⏰ Setting up Cloud Scheduler job..."

# Check if job exists
if gcloud scheduler jobs describe $JOB_NAME --location $REGION &>/dev/null; then
  echo "Updating existing job..."
  gcloud scheduler jobs update http $JOB_NAME \
    --location $REGION \
    --schedule "$SCHEDULE" \
    --http-method POST \
    --uri "$SERVICE_URL/run" \
    --message-body '{}'
else
  echo "Creating new job..."
  gcloud scheduler jobs create http $JOB_NAME \
    --location $REGION \
    --schedule "$SCHEDULE" \
    --http-method POST \
    --uri "$SERVICE_URL/run" \
    --message-body '{}'
fi

# 4. Set up IAM permissions
echo "🔐 Setting up IAM permissions..."
gcloud scheduler jobs add-iam-policy-binding $JOB_NAME \
  --location $REGION \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/run.invoker"

echo "✅ Deployment complete!"
echo "Job will run every 2 hours in $REGION"
echo "View logs with:"
echo "  gcloud scheduler jobs describe $JOB_NAME --location $REGION"
echo "  gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$CLOUD_RUN_SERVICE\" --limit 50"
