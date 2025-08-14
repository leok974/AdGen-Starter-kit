# AdGen — Weekend Prototype

## Prereqs
- Python 3.10+
- Node 18+
- ComfyUI running locally (for now) with your graphs saved under /comfy
- FFmpeg installed and on PATH

## Run backend
cd api && pip install -r requirements.txt && uvicorn main:app --reload --port 8000

## Run frontend
cd web && npm i && NEXT_PUBLIC_API_BASE=http://localhost:8000 npm run dev

## Environment Variables
- `CORS_ORIGINS`: Comma-separated list of allowed CORS origins (e.g., "http://localhost:3000,http://localhost:5173"). Defaults to a list of common local development ports.

## Where files go
- Uploads land in `assets/uploads/`
- Outputs land in `runs/<run_id>/`
- `metadata.json` is written per run

## Next steps
- Replace placeholder orchestrator calls with real ComfyUI HTTP requests
- Add Copy Agent (LLM) and simple QA checks
- Train a tiny brand LoRA and add to stills graph
