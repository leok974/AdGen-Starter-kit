#!/usr/bin/env bash
set -euo pipefail

BASE="${1:-http://localhost:8000}"
PROMPT="${2:-smoke test can on ice}"
TIMEOUT="${TIMEOUT:-120}"

wait_for_health() {
    local url="$1"
    local max_attempts=30

    for i in $(seq 1 $max_attempts); do
        if curl -sf --max-time 5 "$url/health" | jq -e '.ok==true' >/dev/null 2>&1; then
            return 0
        fi
        echo "Health check $i/$max_attempts failed, retrying..."
        sleep 2
    done
    echo "❌ Service not healthy after $max_attempts attempts" >&2
    return 1
}

extract_run_id() {
    local response="$1"
    local run_id

    # Try multiple extraction methods
    run_id=$(echo "$response" | jq -r '.run_id // .detail.run_id // .run_id.run_id // empty' 2>/dev/null)

    if [[ -z "$run_id" || "$run_id" == "null" ]]; then
        # Fallback: find any run_id in the structure
        run_id=$(echo "$response" | jq -r '..|.run_id? // empty' 2>/dev/null | head -n1)
    fi

    if [[ -z "$run_id" || "$run_id" == "null" || ! "$run_id" =~ ^[a-f0-9]{8,}$ ]]; then
        echo "❌ No valid run_id found in: $response" >&2
        return 1
    fi

    echo "$run_id"
}

echo "🔍 Checking health..."
wait_for_health "$BASE"

echo "🎯 Generating run..."
gen_response=$(curl -sf --max-time "$TIMEOUT" -X POST "$BASE/generate" \
    -H 'content-type: application/json' \
    -d "{\"prompt\":\"$PROMPT\"}")

run=$(extract_run_id "$gen_response")
echo "📋 RUN ID: $run"

echo "⚡ Finalizing run..."
if ! curl -sf --max-time "$TIMEOUT" -X POST "$BASE/finalize/$run" >/dev/null; then
    echo "❌ Finalize failed. Checking current status..."
    curl -sf "$BASE/runs/$run/files" | jq . || echo "No status available"
    exit 1
fi

echo "📁 Checking files..."
files_response=$(curl -sf --max-time 30 "$BASE/runs/$run/files")
file_count=$(echo "$files_response" | jq -r '.files | length')

if [[ "$file_count" == "0" || "$file_count" == "null" ]]; then
    echo "❌ No files generated in run $run"
    echo "Response: $files_response"
    exit 1
fi

echo "📊 Files found: $file_count"
echo "✅ Smoke test PASSED"
