#!/usr/bin/env bash
set -euo pipefail
echo "🔍 Basic smoke test"
BASE="${1:-http://localhost:8000}"

# Simple health check
if curl -sf "$BASE/health" | grep -q '"ok":true'; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

# Simple generate test
gen=$(curl -sf -X POST "$BASE/generate" -H 'content-type: application/json' -d '{"prompt":"test"}')
if echo "$gen" | grep -q "run_id"; then
    echo "✅ Generate endpoint works"
else
    echo "❌ Generate failed"
    exit 1
fi

echo "✅ Basic smoke test PASSED"
