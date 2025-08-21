# orchestrator.py — env-driven ComfyUI orchestrator
from __future__ import annotations
import os, uuid, json, time, shutil
from typing import Dict, List, Any
from pathlib import Path
import httpx
import fcntl
from unittest.mock import MagicMock

# Test mode for CI/mocking
TEST_MODE = os.getenv("COMFY_MODE", "").lower() == "test"

# --- Env config ---
COMFY_API = os.getenv("COMFY_API", "http://host.docker.internal:8188").rstrip("/")
RUNS_DIR  = os.getenv("RUNS_DIR", "/app/adgen/runs")
GRAPH_PATH = os.getenv("GRAPH_PATH", "/app/adgen/graphs/qwen.json")
POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "0.8"))
POLL_TIMEOUT  = float(os.getenv("POLL_TIMEOUT", "180"))

Path(RUNS_DIR).mkdir(parents=True, exist_ok=True)
if not Path(GRAPH_PATH).exists():
    raise FileNotFoundError(f"Graph file not found at: {GRAPH_PATH}")

# --- Helpers ---
def _ensure_dir(p: str | Path) -> None:
    Path(p).mkdir(parents=True, exist_ok=True)

def _run_dir(run_id: str) -> str:
    d = os.path.join(RUNS_DIR, str(run_id))
    _ensure_dir(d)
    return d

def _zip_run(run_id: str) -> str:
    base = os.path.join(RUNS_DIR, str(run_id))
    shutil.make_archive(base, "zip", _run_dir(run_id))
    return f"{base}.zip"

def _http() -> httpx.Client:
    if TEST_MODE:
        # Return mock client for testing
        mock_client = MagicMock()
        mock_client.post.return_value.json.return_value = {"prompt_id": "test_prompt_123"}
        mock_client.get.return_value.json.return_value = {
            "test_prompt_123": {
                "outputs": {
                    "test_node": {
                        "images": [{"filename": "test_image.png", "subfolder": "", "type": "output"}]
                    }
                }
            }
        }
        mock_client.get.return_value.content = b"fake_image_data"
        mock_client.__enter__ = lambda self: self
        mock_client.__exit__ = lambda self, *args: None
        return mock_client
    return httpx.Client(base_url=COMFY_API, timeout=60)

def _coerce_run_id(v) -> str:
    if isinstance(v, dict):
        cand = v.get("run_id") or v.get("id") or (v.get("detail") or {})
        if isinstance(cand, dict):
            cand = cand.get("run_id") or cand.get("id")
        v = cand
    return str(v or uuid.uuid4().hex[:12])

# --- Graph helpers ---
def _load_graph() -> Dict[str, Any]:
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _patch_graph_for_run(graph: Dict[str, Any], *, run_id: str, prompt: str, negative: str | None = None) -> Dict[str, Any]:
    # Set prompt text on CLIPTextEncode nodes
    for node in graph.values():
        if node.get("class_type") == "CLIPTextEncode":
            node.setdefault("inputs", {})
            title = (node.get("_meta", {}).get("title", "") or "").lower()
            if "neg" in title and negative:
                node["inputs"]["text"] = negative
            elif "neg" not in title:
                node["inputs"]["text"] = prompt
    # Ensure SaveImage writes under this run_id
    for node in graph.values():
        if node.get("class_type") == "SaveImage":
            node.setdefault("inputs", {})
            node["inputs"]["filename_prefix"] = run_id
    return graph

# --- Comfy helpers ---
def _submit_prompt(client: httpx.Client, graph: Dict[str, Any], client_id: str) -> str:
    r = client.post("/prompt", json={"prompt": graph, "client_id": client_id})
    r.raise_for_status()
    pid = r.json().get("prompt_id")
    if not pid:
        raise RuntimeError(f"ComfyUI did not return prompt_id: {r.text}")
    return pid

def _poll_history(client: httpx.Client, prompt_id: str) -> Dict[str, Any]:
    t0 = time.time()
    while time.time() - t0 < POLL_TIMEOUT:
        r = client.get(f"/history/{prompt_id}")
        if r.status_code == 200 and r.text.strip() not in ("", "{}"):
            return r.json()
        time.sleep(POLL_INTERVAL)
    raise TimeoutError("ComfyUI job timed out")

def _iter_images(hist: Dict[str, Any]) -> List[Dict[str, str]]:
    out: List[Dict[str, str]] = []
    def collect(outputs: Dict[str, Any]):
        for node_data in outputs.values():
            for im in node_data.get("images") or []:
                if "filename" in im:
                    out.append({
                        "filename": im["filename"],
                        "subfolder": im.get("subfolder", ""),
                        "type": im.get("type", "output"),
                    })
    if "outputs" in hist:
        collect(hist["outputs"])
    else:
        for v in hist.values():
            if isinstance(v, dict) and "outputs" in v:
                collect(v["outputs"])
    return out

# --- API functions used by FastAPI routes ---
def create_run(payload: Dict | None = None) -> Dict:
    payload = payload or {}
    run_id = payload.get("run_id") or uuid.uuid4().hex[:12]
    meta_path = os.path.join(_run_dir(run_id), "meta.json")

    run_data = {
        "run_id": run_id,
        "status": "PENDING",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "inputs": payload,
        "artifacts": [],
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(run_data, f, indent=2)

    print(f"[orchestrator] create_run -> {run_id}")
    return run_data

def kickoff_generation(run_id: str, payload: Dict | None = None) -> Dict:
    run_id = _coerce_run_id(run_id)
    payload = payload or {}
    prompt = payload.get("prompt") or "sprite soda on a rock on water surrounded by a valley"
    negative = payload.get("negative_prompt")
    seed = payload.get("seed")

    graph = _load_graph()
    graph = _patch_graph_for_run(graph, run_id=run_id, prompt=prompt, negative=negative)
    if seed is not None:
        for node in graph.values():
            if node.get("class_type", "").lower().endswith("ksampler"):
                node.setdefault("inputs", {})["seed"] = int(seed)

    with _http() as client:
        prompt_id = _submit_prompt(client, graph, client_id=run_id)

    # Update meta.json with run info
    meta_path = os.path.join(_run_dir(run_id), "meta.json")
    try:
        with open(meta_path, "r+", encoding="utf-8") as f:
            meta = json.load(f)
            meta["prompt_id"] = prompt_id
            meta["status"] = "RUNNING"
            f.seek(0)
            json.dump(meta, f, indent=2)
            f.truncate()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error updating meta.json for {run_id}: {e}")
        # Create the file if it doesn't exist or is invalid
        meta = {
            "run_id": run_id,
            "status": "RUNNING",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "inputs": payload,
            "prompt_id": prompt_id,
            "artifacts": [],
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)


    print(f"[orchestrator] kickoff_generation run_id={run_id} prompt_id={prompt_id}")
    return {"run_id": run_id, "status": "RUNNING", "prompt_id": prompt_id}

def list_run_files(run_id: str) -> List[Dict]:
    run_id = _coerce_run_id(run_id)
    base = _run_dir(run_id)
    results: List[Dict] = []
    for root, _, files in os.walk(base):
        for fn in files:
            if fn == "meta.json":
                continue
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, base).replace("\\", "/")
            results.append({"path": rel, "size": os.path.getsize(p)})
    print(f"[orchestrator] list_run_files {run_id} -> {len(results)} files")
    return results

def finalize_run(run_id: str) -> Dict:
    run_id = _coerce_run_id(run_id)
    meta_path = os.path.join(_run_dir(run_id), "meta.json")
    try:
        meta = json.loads(open(meta_path, "r", encoding="utf-8").read())
    except Exception:
        meta = {}

    payload = meta.get("payload", {}) if isinstance(meta.get("payload"), dict) else {}
    prompt = payload.get("prompt") or "sprite soda on a rock on water surrounded by a valley"
    negative = payload.get("negative_prompt")

    images = []
    with _http() as client:
        prompt_id = meta.get("prompt_id")
        if not prompt_id:
            if TEST_MODE:
                prompt_id = "test_prompt_123"
            else:
                graph = _load_graph()
                graph = _patch_graph_for_run(graph, run_id=run_id, prompt=prompt, negative=negative)
                prompt_id = _submit_prompt(client, graph, client_id=run_id)
            meta["prompt_id"] = prompt_id
            with open(meta_path, "wb") as f:
                f.write(json.dumps(meta, indent=2).encode())

        try:
            if TEST_MODE:
                # Create fake image for testing
                test_image = {"filename": f"{run_id}_test.png", "subfolder": "", "type": "output", "url": f"/runs/{run_id}/files/{run_id}_test.png"}
                out_path = os.path.join(_run_dir(run_id), test_image["filename"])
                with open(out_path, "wb") as f:
                    f.write(b"fake_image_data_for_testing")
                images.append({**test_image, "saved_to": out_path})
            else:
                hist = _poll_history(client, prompt_id)
                for im in _iter_images(hist):
                    params = {"filename": im["filename"], "subfolder": im.get("subfolder",""), "type": im.get("type","output")}
                    r = client.get("/view", params=params)
                    r.raise_for_status()
                    out_path = os.path.join(_run_dir(run_id), im["filename"])
                    with open(out_path, "wb") as f:
                        f.write(r.content)
                    images.append({**im, "saved_to": out_path, "url": f"/runs/{run_id}/files/{im['filename']}"})

            status = "COMPLETED"
        except Exception as e:
            print(f"Error during finalization of {run_id}: {e}")
            status = "FAILED"

    # Update meta.json with final status
    with open(meta_path, "r+", encoding="utf-8") as f:
        meta = json.load(f)
        meta["status"] = status
        meta["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        meta["artifacts"] = images
        f.seek(0)
        json.dump(meta, f, indent=2)
        f.truncate()

    zip_path = _zip_run(run_id)
    print(f"[orchestrator] finalize_run -> zip={zip_path}")
    return meta

def list_runs() -> List[Dict]:
    """Lists all runs, reading metadata from each run's directory."""
    runs = []
    for p in Path(RUNS_DIR).iterdir():
        if p.is_dir():
            meta_path = p / "meta.json"
            if meta_path.exists():
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        runs.append({
                            "run_id": meta.get("run_id"),
                            "prompt": meta.get("inputs", {}).get("prompt"),
                            "status": meta.get("status"),
                            "created_at": meta.get("created_at"),
                            "finished_at": meta.get("finished_at"),
                            "duration": (
                                int(time.mktime(time.strptime(meta["finished_at"], "%Y-%m-%dT%H:%M:%S%z"))) -
                                int(time.mktime(time.strptime(meta["created_at"], "%Y-%m-%dT%H:%M:%S%z")))
                            ) if meta.get("finished_at") else None,
                        })
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Skipping corrupt meta.json for run {p.name}: {e}")
    return sorted(runs, key=lambda r: r["created_at"], reverse=True)

def get_run_detail(run_id: str) -> Dict | None:
    """Gets detailed information for a single run."""
    run_id = _coerce_run_id(run_id)
    meta_path = Path(RUNS_DIR) / run_id / "meta.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def cancel_run(run_id: str) -> Dict:
    """Cancels a run by updating its status."""
    run_id = _coerce_run_id(run_id)
    meta_path = Path(RUNS_DIR) / run_id / "meta.json"
    if meta_path.exists():
        with open(meta_path, "r+", encoding="utf-8") as f:
            meta = json.load(f)
            if meta["status"] in ["PENDING", "RUNNING"]:
                meta["status"] = "CANCELLED"
                meta["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
                f.seek(0)
                json.dump(meta, f, indent=2)
                f.truncate()
                print(f"[orchestrator] Cancelled run {run_id}")
                return meta
    raise FileNotFoundError(f"Run {run_id} not found.")

def _update_run_status(run_id: str, status: str, error: str | None = None) -> None:
    """Updates the status of a run in its meta.json file."""
    run_id = _coerce_run_id(run_id)
    meta_path = Path(RUNS_DIR) / run_id / "meta.json"
    if meta_path.exists():
        with open(meta_path, "r+", encoding="utf-8") as f:
            meta = json.load(f)
            meta["status"] = status
            if error:
                meta["error"] = error
            if status in ["FAILED", "COMPLETED", "CANCELLED"]:
                meta["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            f.seek(0)
            json.dump(meta, f, indent=2)
            f.truncate()
            print(f"[orchestrator] Updated run {run_id} status to {status}")
