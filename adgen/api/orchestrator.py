# api/orchestrator.py
import uuid
from typing import Dict, List
from pathlib import Path
from settings import settings


def _coerce_run_id(v): # Accept run record dicts or plain strings; always return a string id
    if isinstance(v, dict):
        v = v.get("run_id") or v.get("id") or (v.get("detail", {}) if isinstance(v.get("detail"), dict) else {})
    if isinstance(v, dict):
        v = v.get("run_id")
    if not v:
        v = uuid.uuid4().hex[:12]
    return str(v)


# Expected external functions the API calls:
# - create_run() -> str
# - kickoff_generation(run_id: str, payload: Dict) -> Dict
# - list_run_files(run_id: str) -> List[str]
# - finalize_run(run_id: str) -> Path (zip path)


def create_run() -> str:
    # create a run directory
    from uuid import uuid4

    run_id = uuid4().hex[:12]
    (settings.RUNS_DIR / run_id).mkdir(parents=True, exist_ok=True)
    print(f"[orchestrator] create_run -> {run_id}")
    return run_id


def kickoff_generation(run_id: str, payload: Dict | None = None) -> Dict:
    run_id = _coerce_run_id(run_id)
    payload = payload or {}
    print(f"[orchestrator] kickoff_generation run_id={run_id}")
    print(f"[orchestrator] mode={settings.COMFY_MODE} api={settings.COMFY_API}")
    print(f"[orchestrator] payload={payload}")
    # Your real code should:
    # - if COMFY_MODE=='api': POST to Comfy API; else write to hotfolder
    # - return { "accepted": True, "run_id": run_id } or richer status
    return {"accepted": True, "run_id": run_id}


def list_run_files(run_id: str) -> List[str]:
    run_id = _coerce_run_id(run_id)
    folder = settings.RUNS_DIR / run_id
    files = [str(p) for p in folder.glob("*") if p.is_file()]
    print(f"[orchestrator] list_run_files {run_id} -> {len(files)} files")
    return files


def finalize_run(run_id: str) -> Path:
    run_id = _coerce_run_id(run_id)
    import shutil

    folder = settings.RUNS_DIR / run_id
    zip_path = settings.RUNS_DIR / f"{run_id}.zip"
    shutil.make_archive(str(zip_path.with_suffix("")), "zip", folder)
    print(f"[orchestrator] finalize_run -> {zip_path}")
    return zip_path
