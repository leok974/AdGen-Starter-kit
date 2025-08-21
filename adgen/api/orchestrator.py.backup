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
    with open(meta_path, "wb") as f:
        f.write(json.dumps({"payload": payload}, indent=2).encode())
    print(f"[orchestrator] create_run -> {run_id}")
    return {"run_id": run_id, "status": "created", "input": payload}

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

    # Save prompt_id
    meta_path = os.path.join(_run_dir(run_id), "meta.json")
    try:
        meta = {}
        if os.path.exists(meta_path):
            meta = json.loads(open(meta_path, "r", encoding="utf-8").read())
        meta.update({"prompt_id": prompt_id, "prompt": prompt, "negative_prompt": negative})
        with open(meta_path, "wb") as f:
            f.write(json.dumps(meta, indent=2).encode())
    except Exception:
        pass

    print(f"[orchestrator] kickoff_generation run_id={run_id} prompt_id={prompt_id}")
    return {"run_id": run_id, "status": "started", "prompt_id": prompt_id}

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

        if TEST_MODE:
            # Create fake image for testing
            test_image = {"filename": f"{run_id}_test.png", "subfolder": "", "type": "output"}
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
                images.append({**im, "saved_to": out_path})

    files = list_run_files(run_id)
    zip_path = _zip_run(run_id)
    print(f"[orchestrator] finalize_run -> zip={zip_path}")
    return {"run_id": run_id, "images": images, "files": files, "zip": zip_path}
