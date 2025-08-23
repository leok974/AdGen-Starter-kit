#!/usr/bin/env bash
set -euo pipefail

# Staging deployment with test mode (no ComfyUI required)
PROJECT_ID="${PROJECT_ID:?PROJECT_ID required}"
SERVICE="${SERVICE:-adgen-api-staging}"
REGION="${REGION:-us-central1}"

echo "🧪 Deploying staging version with test mode..."

IMG="gcr.io/$PROJECT_ID/$SERVICE:$(git rev-parse --short HEAD)-staging"
gcloud builds submit --tag "$IMG" --project "$PROJECT_ID"

gcloud run deploy "$SERVICE" \
  --image "$IMG" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --max-instances 2 \
  --concurrency 10 \
  --cpu 1 \
  --memory 1Gi \
  --timeout 60 \
  --set-env-vars PORT=8080 \
  --set-env-vars RUNS_DIR=/tmp/adgen/runs \
  --set-env-vars GRAPH_PATH=/app/adgen/graphs/qwen.json \
  --set-env-vars COMFY_MODE=test \
  --set-env-vars RUN_RETENTION_HOURS=1 \
  --set-env-vars "CORS_ORIGINS=https://<PROD_VERCEL_DOMAIN>,http://localhost:3000,http://127.0.0.1:3000" \
  --set-env-vars "CORS_ORIGIN_REGEX=https://.*\.vercel\.app$" \
  --project "$PROJECT_ID"

SERVICE_URL=$(gcloud run services describe "$SERVICE" --region "$REGION" --project "$PROJECT_ID" --format="value(status.url)")
echo "🧪 Staging deployed: $SERVICE_URL"
