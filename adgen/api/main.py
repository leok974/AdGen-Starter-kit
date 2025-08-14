# api/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict
from .settings import settings, dump_settings_banner
from .orchestrator import create_run, kickoff_generation, list_run_files, finalize_run

app = FastAPI(title="AdGen API", version="0.1.0")

# Broad CORS for local dev (frontend on :3000 or :5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
    # add any other fields you pass from the frontend

@app.on_event("startup")
async def on_startup():
    print(dump_settings_banner())
    print("[startup] FastAPI started. /health and /docs should be live.")

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/generate")
def generate(body: GenerateBody):
    try:
        run_id = create_run()
        result = kickoff_generation(run_id, body.model_dump())
        return {"run_id": run_id, "status": "accepted", "detail": result}
    except Exception as e:
        print("[/generate] ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/runs/{run_id}/files")
def get_run_files(run_id: str):
    try:
        files = list_run_files(run_id)
        return {"run_id": run_id, "files": files}
    except Exception as e:
        print("[/runs/:id/files] ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/finalize/{run_id}")
def finalize(run_id: str):
    try:
        zip_path = finalize_run(run_id)
        return {"run_id": run_id, "zip": str(zip_path)}
    except Exception as e:
        print("[/finalize/:id] ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))

# Optional direct download
@app.get("/download/{run_id}")
def download_zip(run_id: str):
    try:
        path = settings.RUNS_DIR / f"{run_id}.zip"
        if not path.exists():
            raise FileNotFoundError(f"{path} not found")
        return FileResponse(str(path), media_type="application/zip", filename=path.name)
    except Exception as e:
        print("[/download/:id] ERROR:", repr(e))
        raise HTTPException(status_code=404, detail=str(e))
