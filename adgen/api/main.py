# api/main.py
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from orchestrator import create_run, kickoff_generation, list_run_files, finalize_run

app = FastAPI(title="AdGen API", version="0.1.0")

# --- Configuration ---
# Get CORS origins from environment variable, default to common local dev ports
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000").split(",")
RUNS_DIR = Path(os.getenv("RUNS_DIR", "adgen/runs")).resolve()

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateBody(BaseModel):
    prompt: str
    negative_prompt: str | None = None
    seed: int | None = None
    logo_image: str | None = None
    mood_image: str | None = None


@app.on_event("startup")
async def on_startup():
    print("=== AdGen API Started ===")
    print(f"RUNS_DIR: {RUNS_DIR}")
    print(f"CORS origins: {CORS_ORIGINS}")
    print("See /docs for API schema.")
    print("=========================")


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    # In a real app, this would check DB connections, etc.
    return {"ok": True}


@app.post("/generate")
def generate(body: GenerateBody):
    try:
        run_id = create_run()
        prompt_id = kickoff_generation(run_id, body.model_dump())
        return {"run_id": run_id, "status": "queued", "prompt_id": prompt_id}
    except Exception as e:
        print(f"[/generate] ERROR: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/runs/{run_id}/files")
def get_run_files(run_id: str):
    try:
        files = list_run_files(run_id)
        return {"run_id": run_id, "files": files}
    except Exception as e:
        print(f"[/runs/{run_id}/files] ERROR: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/finalize/{run_id}")
def finalize(run_id: str):
    try:
        zip_path = finalize_run(run_id)
        return {"run_id": run_id, "zip_path": str(zip_path)}
    except Exception as e:
        print(f"[/finalize/{run_id}] ERROR: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{run_id}")
def download_zip(run_id: str):
    try:
        zip_path = RUNS_DIR / f"{run_id}.zip"
        if not zip_path.exists():
            raise FileNotFoundError(f"Zip file not found for run_id: {run_id}")
        return FileResponse(str(zip_path), media_type="application/zip", filename=zip_path.name)
    except FileNotFoundError as e:
        print(f"[/download/{run_id}] ERROR: {repr(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"[/download/{run_id}] ERROR: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))
