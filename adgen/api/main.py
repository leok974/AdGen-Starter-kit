# api/main.py
import os
import time, shutil, fcntl
from fastapi import status
import re
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from orchestrator import create_run, kickoff_generation, list_runs, get_run_detail, cancel_run, finalize_run, _update_run_status

app = FastAPI(title="AdGen API", version="0.1.0")

# --- Configuration ---
RUNS_DIR = Path(os.getenv("RUNS_DIR", "/app/adgen/runs")).resolve()
COMFY_API = os.getenv("COMFY_API", "http://host.docker.internal:8188").rstrip("/")
GRAPH_PATH = os.getenv("GRAPH_PATH", "/app/adgen/graphs/qwen.json")

# Configure CORS: explicit origins + optional regex for Vercel previews
origins_env = os.getenv("CORS_ORIGINS", "http://localhost:3000")
cors_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
cors_origin_regex = os.getenv("CORS_ORIGIN_REGEX")  # e.g. r"https://.*\.vercel\.app$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=cors_origin_regex,  # enable previews like https://*-vercel.app
    allow_credentials=True,
    allow_methods=["*"],   # includes OPTIONS for preflight
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
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    # Validate required files
    if not Path(GRAPH_PATH).exists():
        print(f"⚠️ Warning: Graph file not found at {GRAPH_PATH}")

    print(f"✅ AdGen API starting")
    print(f"   RUNS_DIR: {RUNS_DIR}")
    print(f"   GRAPH_PATH: {GRAPH_PATH}")
    print(f"   COMFY_API: {COMFY_API}")
    print(f"   TEST_MODE: {os.getenv('COMFY_MODE', 'production')}")

    # Retention sweep for old runs (with file locking for Cloud Run safety)
    try:
        max_age_hours = int(os.getenv("RUN_RETENTION_HOURS", "24"))
        cutoff = time.time() - max_age_hours * 3600
        lock_file = RUNS_DIR / ".retention_lock"

        try:
            with lock_file.open('w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

                kept, removed = 0, 0
                for p in RUNS_DIR.iterdir():
                    try:
                        if p.is_dir() and p.stat().st_mtime < cutoff:
                            shutil.rmtree(p)
                            removed += 1
                            # Also remove corresponding zip
                            z = RUNS_DIR / f"{p.name}.zip"
                            if z.exists():
                                z.unlink()
                        elif p.is_dir():
                            kept += 1
                    except Exception as e:
                        print(f"⚠️ Retention error for {p}: {e}")

                print(f"🧹 Retention sweep: kept={kept}, removed={removed}")

        except (OSError, IOError):
            print("🔒 Retention sweep skipped (another instance running)")
        finally:
            try:
                lock_file.unlink()
            except FileNotFoundError:
                pass

    except Exception as e:
        print(f"⚠️ Retention sweep failed: {e}")


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/health/detailed")
def detailed_health():
    """Detailed health check including external dependencies"""
    status = {"api": "ok", "timestamp": time.time()}

    # Check runs directory
    try:
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        status["storage"] = "ok"
    except Exception as e:
        status["storage"] = f"error: {e}"

    # Check graph file
    if Path(GRAPH_PATH).exists():
        status["graph"] = "ok"
    else:
        status["graph"] = f"missing: {GRAPH_PATH}"

    # Check ComfyUI connectivity (skip in test mode)
    if os.getenv("COMFY_MODE", "").lower() != "test":
        try:
            import httpx
            with httpx.Client(timeout=5) as client:
                resp = client.get(f"{COMFY_API}/")
                status["comfy"] = "ok" if resp.status_code == 200 else f"status: {resp.status_code}"
        except Exception as e:
            status["comfy"] = f"error: {e}"
    else:
        status["comfy"] = "test_mode"

    overall_ok = all(v == "ok" or v == "test_mode" for v in status.values() if v != status["timestamp"])
    status["ok"] = overall_ok

    return status


@app.post("/generate")
def generate(body: GenerateBody):
    try:
        # Always create run first
        result = create_run(body.dict())
        run_id = result["run_id"]

        try:
            # Attempt to start generation
            generation_result = kickoff_generation(run_id, body.dict())
            return generation_result
        except Exception as e:
            # Mark run as failed but still return run_id
            _update_run_status(run_id, "FAILED", str(e))
            return {
                "run_id": run_id,
                "status": "FAILED",
                "error": str(e)
            }
    except Exception as e:
        # Only return 500 if we can't even create the run
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/runs")
async def list_runs_endpoint():
    """Return list of all runs with basic info"""
    try:
        return list_runs()
    except Exception as e:
        print(f"[/runs] ERROR: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/runs/{run_id}")
async def get_run_detail_endpoint(run_id: str):
    """Return detailed run info including artifacts"""
    try:
        detail = get_run_detail(run_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Run not found")
        return detail
    except Exception as e:
        print(f"[/runs/{run_id}] ERROR: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/runs/{run_id}/cancel")
async def cancel_run_endpoint(run_id: str):
    """Cancel a running generation"""
    try:
        return cancel_run(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found")
    except Exception as e:
        print(f"[/runs/{run_id}/cancel] ERROR: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/finalize/{run_id}")
def finalize(run_id: str):
    try:
        result = finalize_run(run_id)
        return result
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


@app.delete("/runs/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: str):
    """Delete a specific run and its associated files"""
    if not run_id or not run_id.replace("-", "").replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="Invalid run_id format")

    try:
        # Remove run directory
        run_path = RUNS_DIR / run_id
        if run_path.exists() and run_path.is_dir():
            shutil.rmtree(run_path)

        # Remove zip file
        zip_path = RUNS_DIR / f"{run_id}.zip"
        if zip_path.exists():
            zip_path.unlink()

        print(f"🗑️ Deleted run: {run_id}")

    except Exception as e:
        print(f"⚠️ Delete error for {run_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {e}")
