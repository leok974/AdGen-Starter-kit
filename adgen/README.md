# AdGen — Weekend Prototype

## Docker Quick Start
1.  **Install Docker and Docker Compose.**
2.  **Create a `.env` file:** Copy `.env.sample` to `.env` and edit as needed.
3.  **Build the container:** `docker compose -f docker-compose.dev.yml build`
4.  **Run the container:** `docker compose -f docker-compose.dev.yml up -d`
5.  **Confirm the API is running:** `curl http://localhost:8000/health` should return `{"ok":true}`.
6.  **Use `make logs`** to tail the logs and `make down` to stop the services.

---

## Manual Setup

### Prereqs
- Python 3.10+
- Node 18+
- ComfyUI running locally (for now) with your graphs saved under /comfy
- FFmpeg installed and on PATH

### Run backend
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
