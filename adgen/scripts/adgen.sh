#!/usr/bin/env bash
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
PROMPT="${1:-sprite soda on a rock on water surrounded by a valley}"
OUTPUT_DIR="${OUTPUT_DIR:-/tmp}"

if ! command -v jq >/dev/null; then
    echo "❌ jq is required but not installed" >&2
    exit 1
fi

echo "🎯 Generating image: '$PROMPT'"

# Generate
gen_response=$(curl -sf -X POST "$BASE/generate" \
    -H 'content-type: application/json' \
    -d "{\"prompt\":\"$PROMPT\"}")

run=$(echo "$gen_response" | jq -r '.run_id // .detail.run_id // .run_id.run_id // empty')
if [[ -z "$run" || "$run" == "null" ]]; then
    run=$(echo "$gen_response" | jq -r '..|.run_id? // empty' | head -n1)
fi

if [[ -z "$run" || "$run" == "null" ]]; then
    echo "❌ Failed to extract run_id from response:" >&2
    echo "$gen_response" | jq . >&2
    exit 1
fi

echo "📋 Run ID: $run"

# Finalize
echo "⚡ Processing..."
if ! curl -sf -X POST "$BASE/finalize/$run" >/dev/null; then
    echo "❌ Finalize failed" >&2
    exit 1
fi

# Download
output_dir="$OUTPUT_DIR/adgen_$run"
mkdir -p "$output_dir"

echo "📥 Downloading results..."
if curl -sfL "$BASE/download/$run?path=$run.zip" -o "$output_dir/$run.zip"; then
    echo "✅ Downloaded via API"
elif docker ps --filter "name=adgen-api" --format "{{.Names}}" | grep -q adgen-api; then
    echo "🐳 Fallback: copying from Docker container..."
    if docker cp "adgen-api:/app/adgen/runs/$run.zip" "$output_dir/$run.zip"; then
        echo "✅ Downloaded via Docker"
    else
        echo "❌ Both download methods failed" >&2
        exit 1
    fi
else
    echo "❌ Download failed and no Docker container found" >&2
    exit 1
fi

# Extract
if command -v unzip >/dev/null; then
    unzip -o "$output_dir/$run.zip" -d "$output_dir" >/dev/null
    echo "📁 Extracted to: $output_dir"
else
    echo "📦 Downloaded to: $output_dir/$run.zip"
fi

# Open (if GUI available)
if [[ -n "${DISPLAY:-}" ]] || [[ "$(uname)" == "Darwin" ]]; then
    (open "$output_dir" 2>/dev/null || xdg-open "$output_dir" 2>/dev/null || true) &
    echo "🖼️ Opening results folder..."
fi

echo "🎉 Complete! Results in: $output_dir"
