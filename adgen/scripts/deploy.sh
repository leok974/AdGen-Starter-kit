#!/usr/bin/env bash
set -euo pipefail

# Validation
if [[ -z "${PROJECT_ID:-}" ]]; then
    echo "❌ PROJECT_ID environment variable is required" >&2
    exit 1
fi

if [[ ! "$PROJECT_ID" =~ ^[a-z0-9-]+$ ]]; then
    echo "❌ Invalid PROJECT_ID format: $PROJECT_ID" >&2
    exit 1
fi

SERVICE="${SERVICE:-adgen-api}"
REGION="${REGION:-us-central1}"
COMFY_ENDPOINT="${COMFY_ENDPOINT:-}"

if [[ -z "$COMFY_ENDPOINT" ]]; then
    echo "❌ COMFY_ENDPOINT environment variable is required for production deployment" >&2
    echo "   Set it to your ComfyUI service URL (e.g., https://your-comfy.example.com:8188)" >&2
    exit 1
fi

# Build and deploy
echo "🏗️ Building image for project: $PROJECT_ID"
IMG="gcr.io/$PROJECT_ID/$SERVICE:$(git rev-parse --short HEAD)"

echo "📦 Submitting build to Cloud Build..."
gcloud builds submit --tag "$IMG" --project "$PROJECT_ID"

echo "🚀 Deploying to Cloud Run..."
gcloud run deploy "$SERVICE" \
  --image "$IMG" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --max-instances 5 \
  --concurrency 50 \
  --cpu 1 \
  --memory 2Gi \
  --timeout 300 \
  --set-env-vars PORT=8080 \
  --set-env-vars RUNS_DIR=/tmp/adgen/runs \
  --set-env-vars GRAPH_PATH=/app/adgen/graphs/qwen.json \
  --set-env-vars COMFY_API="$COMFY_ENDPOINT" \
  --set-env-vars RUN_RETENTION_HOURS=2 \
  --set-env-vars "CORS_ORIGINS=https://<PROD_VERCEL_DOMAIN>,http://localhost:3000,http://127.0.0.1:3000" \
  --set-env-vars "CORS_ORIGIN_REGEX=https://.*\.vercel\.app$" \
  --project "$PROJECT_ID"

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT_ID" --format="value(status.url)")

echo "✅ Deployment complete!"
echo "🌐 Service URL: $SERVICE_URL"
echo ""
echo "🧪 Test your deployment:"
echo "  curl $SERVICE_URL/health"
echo "  curl $SERVICE_URL/health/detailed"
echo ""
echo "🔧 Smoke test:"
echo "  bash scripts/smoke.sh $SERVICE_URL 'production test'"
