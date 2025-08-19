# orchestrator.py — single-file orchestrator: no external settings import needed
import os
import uuid
import json
import time
import shutil
import pathlib
from typing import Dict, List, Any
import httpx

# ---- Config (env overrideable) ----
COMFY_API = os.getenv("COMFY_API", "http://host.docker.internal:8188/").rstrip("/")
RUNS_DIR = os.getenv("RUNS_DIR", "/app/adgen/runs")
GRAPH_PATH = os.getenv("GRAPH_PATH", "/app/adgen/graphs/qwen.json")  # ensure this exists in the container

# ---- Small helpers ----
def _ensure_dir(p: str) -> None:
    pathlib.Path(p).mkdir(parents=True, exist_ok=True)

def _run_dir(run_id: str) -> str:
    d = os.path.join(RUNS_DIR, str(run_id))
    _ensure_dir(d)
    return d

def _zip_run(run_id: str) -> str:
    folder = _run_dir(run_id)
    zip_base = os.path.join(RUNS_DIR, str(run_id))
    shutil.make_archive(zip_base, "zip", folder)
    return f"{zip_base}.zip"

def _save_bytes(path: str, data: bytes) -> None:
    _ensure_dir(os.path.dirname(path))
    with open(path, "wb") as f:
        f.write(data)

def _http() -> httpx.Client:
    return httpx.Client(base_url=COMFY_API, timeout=60)

def _coerce_run_id(v):
    # Accept dicts or strings; always return a string id
    if isinstance(v, dict):
        v = v.get("run_id") or v.get("id") or (v.get("detail") or {})
        if isinstance(v, dict):
            v = v.get("run_id")
    if not v:
        v = uuid.uuid4().hex[:12]
    return str(v)

# ---- ComfyUI helpers ----
def _submit_prompt(client: httpx.Client, graph: Dict[str, Any], client_id: str) -> str:
    r = client.post("/prompt", json={"prompt": graph, "client_id": client_id})
    r.raise_for_status()
    return r.json().get("prompt_id")

def _poll_history_by_prompt_id(client: httpx.Client, prompt_id: str, timeout_s: float = 180.0) -> Dict[str, Any]:
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        r = client.get(f"/history/{prompt_id}")
        if r.status_code == 200 and r.text.strip() not in ("", "{}"):
            return r.json()
        time.sleep(0.8)
    raise TimeoutError("ComfyUI job timed out")

def _download_image(client: httpx.Client, image_meta: Dict[str, str]) -> bytes:
    params = {
        "filename": image_meta["filename"],
        "subfolder": image_meta.get("subfolder", ""),
        "type": image_meta.get("type", "output"),
    }
    r = client.get("/view", params=params)
    r.raise_for_status()
    return r.content

def _iter_images_from_history(hist: Dict[str, Any]) -> List[Dict[str, str]]:
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

# ---- Graph helpers ----
def _load_graph() -> Dict[str, Any]:
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _patch_graph_for_run(graph: Dict[str, Any], run_id: str, prompt: str, negative: str | None = None) -> Dict[str, Any]:
    # Set prompt text on CLIPTextEncode nodes
    for node in graph.values():
        if node.get("class_type") == "CLIPTextEncode":
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

# ===== API used by main.py =====
def create_run(payload: Dict | None = None) -> Dict:
    payload = payload or {}
    run_id = payload.get("run_id") or uuid.uuid4().hex[:12]
    meta_path = os.path.join(_run_dir(run_id), "meta.json")
    _save_bytes(meta_path, json.dumps({"payload": payload}, indent=2).encode())
    print(f"[orchestrator] create_run -> {run_id}")
    return {"run_id": run_id, "status": "created", "input": payload}

def kickoff_generation(run_id: str, payload: Dict | None = None) -> Dict:
    run_id = _coerce_run_id(run_id)
    payload = payload or {}
    prompt = payload.get("prompt", "sprite soda on a rock on water surrounded by a valley")
    negative = payload.get("negative_prompt")
    seed = payload.get("seed")

    print(f"[orchestrator] kickoff_generation run_id={run_id}")
    print(f"[orchestrator] mode=api api={COMFY_API}")
    print(f"[orchestrator] payload={payload}")

    graph = _load_graph()
    graph = _patch_graph_for_run(graph, run_id=run_id, prompt=prompt, negative=negative)
    if seed is not None:
        # attempt to set a 'seed' if a KSampler node exists and exposes it
        for node in graph.values():
            if node.get("class_type", "").lower().endswith("ksampler"):
                node.setdefault("inputs", {})["seed"] = int(seed)

    with _http() as client:
        prompt_id = _submit_prompt(client, graph, client_id=run_id)

    # persist meta
    meta_path = os.path.join(_run_dir(run_id), "meta.json")
    try:
        meta = {}
        if os.path.exists(meta_path):
            meta = json.loads(open(meta_path, "r", encoding="utf-8").read())
        meta.update({"prompt_id": prompt_id, "prompt": prompt, "negative_prompt": negative})
        _save_bytes(meta_path, json.dumps(meta, indent=2).encode())
    except Exception:
        pass

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

    # Use saved payload prompt if present; fallback to a default
    payload = meta.get("payload", {}) if isinstance(meta.get("payload"), dict) else {}
    prompt = payload.get("prompt", "sprite soda on a rock on water surrounded by a valley")
    negative = payload.get("negative_prompt")

    prompt_id = meta.get("prompt_id")
    images = []

    with _http() as client:
        # Kick off if not started yet
        if not prompt_id:
            graph = _load_graph()
            graph = _patch_graph_for_run(graph, run_id=run_id, prompt=prompt, negative=negative)
            prompt_id = _submit_prompt(client, graph, client_id=run_id)
            meta["prompt_id"] = prompt_id
            _save_bytes(meta_path, json.dumps(meta, indent=2).encode())

        # Poll and download images
        hist = _poll_history_by_prompt_id(client, prompt_id)
        for im in _iter_images_from_history(hist):
            data = _download_image(client, im)
            out_path = os.path.join(_run_dir(run_id), im["filename"])
            _save_bytes(out_path, data)
            images.append(im | {"saved_to": out_path})

    files = list_run_files(run_id)
    zip_path = _zip_run(run_id)
    return {"run_id": run_id, "images": images, "files": files, "zip": zip_path}
