# AdGen-Starter-kit

## 🧪 Testing & Deployment

### Smoke Tests
Run comprehensive API validation:

```bash
# Local Docker testing
bash scripts/smoke.sh

# Against deployed service
bash scripts/smoke.sh https://your-service.run.app

# PowerShell version
.\scripts\smoke.ps1 -Base "http://localhost:8000" -Prompt "test image"
```

### Quick Image Generation
Generate and download images with one command:

```bash
# Generate image (opens results folder automatically)
bash scripts/adgen.sh "sprite soda can on ice"

# Custom output location
OUTPUT_DIR=/tmp/my_art bash scripts/adgen.sh "cyberpunk city at sunset"
```

### CI/CD
- **GitHub Actions** runs smoke tests automatically on PRs
- **Test Mode** allows CI without ComfyUI dependency
- **Staging deployments** available with `scripts/deploy-staging.sh`

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/health/detailed` | GET | Health + ComfyUI connectivity |
| `/generate` | POST | Create new run |
| `/finalize/{run_id}` | POST | Process and download images |
| `/runs/{run_id}/files` | GET | List run files |
| `/download/{run_id}` | GET | Download zip archive |
| `/runs/{run_id}` | DELETE | Delete run and files |

### Environment Variables

#### Core Settings
- `COMFY_API` - ComfyUI endpoint (default: `http://host.docker.internal:8188`)
- `RUNS_DIR` - Storage directory (default: `/app/adgen/runs`)
- `GRAPH_PATH` - ComfyUI workflow file (default: `/app/adgen/graphs/qwen.json`)

#### Testing & Operations
- `COMFY_MODE=test` - Enable test mode (mocks ComfyUI for CI)
- `RUN_RETENTION_HOURS=24` - Auto-cleanup old runs (default: 24h)
- `POLL_TIMEOUT=180` - Max wait for ComfyUI job (default: 180s)

### Deployment

#### Local Development
```bash
# Start with Docker Compose
docker compose -f adgen/docker-compose.dev.yml up --build

# Test the API
bash scripts/smoke.sh
```

#### Production (Google Cloud Run)
```bash
export PROJECT_ID=your-gcp-project
export COMFY_ENDPOINT=https://your-comfy-api.com:8188
bash scripts/deploy.sh
```

#### Staging (Test Mode)
```bash
export PROJECT_ID=your-gcp-project
bash scripts/deploy-staging.sh
```

## 🔧 Troubleshooting

### Common Issues

**"Graph file not found"**
- Ensure `adgen/api/adgen/graphs/qwen.json` exists
- Check `GRAPH_PATH` environment variable

**"ComfyUI connection refused"**
- Verify ComfyUI is running on correct port
- Test: `curl http://localhost:8188/` should return 200
- For Docker: use `host.docker.internal:8188`

**"No files generated"**
- Check ComfyUI workflow has SaveImage nodes
- Verify `filename_prefix` is being set correctly
- Look at container logs: `docker logs adgen-api`

**CI tests failing**
- CI runs in test mode (no real ComfyUI needed)
- Check GitHub Actions logs for specific errors
- Verify Docker builds succeed locally

### Debug Commands
```bash
# Check container health
docker exec -it adgen-api curl localhost:8000/health/detailed

# Inspect run directory
docker exec -it adgen-api ls -la /app/adgen/runs/

# View logs
docker logs -f adgen-api

# Test ComfyUI connectivity from container
docker exec -it adgen-api python -c "
import httpx;
print(httpx.get('http://host.docker.internal:8188/').status_code)
"
```

---

## 📌 Workflow Guide

We’ve documented the full **AdGen + ComfyUI generation workflow** in a dedicated file:

👉 [WORKFLOW.md](./WORKFLOW.md)

This guide covers:
- How to start a generation run
- Monitoring ComfyUI outputs
- Finalizing runs into packaged ZIPs
- Downloading results locally

Use this if you want a **step-by-step PowerShell example** to quickly generate and retrieve ad assets.

---

## ⚡ Scripts

We provide a PowerShell script to automate the full AdGen + ComfyUI workflow.

### `Generate-AdGenContent.ps1`

This script handles the complete process:

1. Health checks (AdGen API + ComfyUI)
2. Start generation (`/generate`)
3. Wait for ComfyUI to finish
4. Finalize run (`/finalize/{run_id}`)
5. Download + extract results (`/download/{run_id}`)
6. Auto-open images
7. Optional cleanup (`DELETE /runs/{run_id}`)

### Usage

```powershell
# Basic usage
.\Generate-AdGenContent.ps1 -Prompt "Create an advertisement for a luxury watch"

# With more options
.\Generate-AdGenContent.ps1 -Prompt "Sports car advertisement" -NegativePrompt "blurry, low quality" -Seed 42 -MaxWaitMinutes 15

# Custom output directory
.\Generate-AdGenContent.ps1 -Prompt "Beverage advertisement" -OutputDir ".\adgen_out"
```

Key Features

Error handling and informative messages

Configurable wait times and output directories

Automatic file organization with timestamps

Health checks before starting

Progress reporting throughout

---

## 📦 Batch Processing

For generating multiple ads in one run, we provide a PowerShell script:

### `Generate-AdGenContent-Batch.ps1`

This script processes multiple prompts from either a **CSV** or a **TXT** file.

### Features
- Reads prompts from CSV (`prompt`, `negative_prompt`, `seed`, `name`) or TXT (one prompt per line).
- Health checks AdGen API + ComfyUI before starting.
- Sequential or concurrent processing modes.
- Monitors ComfyUI queue to detect when jobs finish.
- Finalizes and downloads results for each job.
- Extracts ZIPs automatically.
- Provides a detailed summary (success/failure counts, total images, total size).

### Usage Examples

```powershell
# Sequential (default, recommended)
& "adgen\scripts\Generate-AdGenContent-Batch.ps1" -InputFile "prompts.csv" -OutputDir "batch_ads" -DelayBetweenJobs 30

# Concurrent mode (all jobs start together)
& "adgen\scripts\Generate-AdGenContent-Batch.ps1" -InputFile "prompts.csv" -OutputDir "batch_ads" -ConcurrentMode

# Custom timeout + delay
& "adgen\scripts\Generate-AdGenContent-Batch.ps1" -InputFile "prompts.txt" -OutputDir "my_batch" -MaxWaitMinutes 15 -DelayBetweenJobs 60
```
Input Formats
CSV (prompts.csv):

```csv
name,prompt,negative_prompt,seed
luxury_watch,"Elegant luxury watch advertisement, dramatic lighting, black background",cluttered,42
sports_car,"High-performance sports car ad, dynamic angle, sunset backdrop",blurry,123
coffee_shop,"Cozy coffee shop poster, warm lighting, rustic atmosphere",artificial,456
tech_gadget,"Sleek smartphone advertisement, minimalist design, gradient background","low quality, plastic",789
```
TXT (prompts.txt):

```csharp
Elegant luxury watch advertisement with dramatic lighting
High-performance sports car ad with dynamic sunset
Cozy coffee shop poster with warm atmosphere
Sleek smartphone advertisement, minimalist design
Premium headphones ad with modern aesthetic
```