# AdGen API Scripts

## Development Scripts

### `smoke.ps1` / `smoke.sh`
Comprehensive smoke tests that validate the full API workflow:
- Health check with retries
- Generate run with robust ID extraction
- Finalize with timeout handling
- Validate files were created

**Usage:**
```bash
# Local testing
bash scripts/smoke.sh http://localhost:8000 "test prompt"

# Custom timeout
TIMEOUT=180 bash scripts/smoke.sh http://localhost:8000 "complex prompt"
```

### `adgen.sh`
End-to-end image generation helper for macOS/Linux:
- Generates image with custom prompt
- Downloads results (API + Docker fallback)
- Extracts and opens results folder
- Comprehensive error handling

**Usage:**
```bash
# Basic usage
bash scripts/adgen.sh "sprite soda can floating in space"

# Custom output directory
OUTPUT_DIR=/tmp/my_images bash scripts/adgen.sh "cyberpunk city"
```

## Deployment Scripts

### `deploy.sh`
Production deployment to Google Cloud Run:
- Validates environment variables
- Builds with Cloud Build
- Deploys with production settings
- Requires ComfyUI endpoint

**Required Environment:**
```bash
export PROJECT_ID=your-gcp-project
export COMFY_ENDPOINT=https://your-comfy.example.com:8188
bash scripts/deploy.sh
```

### `deploy-staging.sh`
Staging deployment with test mode:
- No ComfyUI dependency (uses mocks)
- Lower resource limits
- Shorter retention

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `COMFY_MODE` | `production` | Set to `test` for mocking |
| `COMFY_API` | `http://host.docker.internal:8188` | ComfyUI endpoint |
| `RUN_RETENTION_HOURS` | `24` | Auto-cleanup old runs |
| `RUNS_DIR` | `/app/adgen/runs` | Storage directory |
| `GRAPH_PATH` | `/app/adgen/graphs/qwen.json` | ComfyUI workflow |
| `TIMEOUT` | `120` | Smoke test timeout |
