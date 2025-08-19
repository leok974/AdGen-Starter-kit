import os
import json
import uuid
import time
import shutil
from pathlib import Path
from typing import Dict, List
import httpx

# --- Environment Setup ---
COMFY_API_URL = os.getenv("COMFY_API", "http://127.0.0.1:8188")
RUNS_DIR = Path(os.getenv("RUNS_DIR", "adgen/runs")).resolve()
GRAPH_PATH = Path(os.getenv("GRAPH_PATH", "adgen/graphs/qwen.json")).resolve()
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "2")) # seconds

# Ensure base directories exist
RUNS_DIR.mkdir(parents=True, exist_ok=True)
if not GRAPH_PATH.exists():
    raise FileNotFoundError(f"Graph file not found at: {GRAPH_PATH}")


def _get_run_path(run_id: str) -> Path:
    """Returns the validated path for a given run_id."""
    if not run_id or not isinstance(run_id, str) or len(run_id) > 16:
        raise ValueError("Invalid run_id specified.")
    run_path = (RUNS_DIR / run_id).resolve()
    if not run_path.parent == RUNS_DIR:
        raise ValueError("Invalid run_id, path traversal detected.")
    return run_path

def create_run() -> str:
    """
    Creates a directory for a new run and returns the run_id.
    """
    run_id = uuid.uuid4().hex[:12]
    run_path = _get_run_path(run_id)
    run_path.mkdir(parents=True, exist_ok=True)
    print(f"[orchestrator] Created run '{run_id}' at {run_path}")
    return run_id


def kickoff_generation(run_id: str, payload: Dict) -> str:
    """
    Loads the graph, patches it with the prompt, and queues it in ComfyUI.
    Returns the prompt_id from ComfyUI.
    """
    print(f"[orchestrator] Kicking off generation for run_id: {run_id}")
    run_path = _get_run_path(run_id)
    prompt_text = payload.get("prompt")
    if not prompt_text:
        raise ValueError("Prompt is required in the payload.")

    # Load and patch the graph
    with open(GRAPH_PATH, "r") as f:
        graph = json.load(f)

    # The prompt node is "6" in the provided qwen.json
    graph["6"]["inputs"]["text"] = prompt_text

    # Prepare the request for ComfyUI
    client_id = str(uuid.uuid4())
    comfy_payload = {"prompt": graph, "client_id": client_id}

    # Queue the prompt
    with httpx.Client() as client:
        url = f"{COMFY_API_URL.rstrip('/')}/prompt"
        print(f"[orchestrator] Posting to {url}")
        response = client.post(url, json=comfy_payload)
        response.raise_for_status()
        result = response.json()

    if "prompt_id" not in result:
        raise RuntimeError(f"ComfyUI did not return a prompt_id. Response: {result}")

    prompt_id = result["prompt_id"]
    print(f"[orchestrator] ComfyUI accepted job. prompt_id: {prompt_id}")

    # Save prompt_id for finalize_run
    (run_path / "prompt_id.txt").write_text(prompt_id)

    return prompt_id


def list_run_files(run_id: str) -> List[str]:
    """
    Lists all files in the specified run directory.
    """
    run_path = _get_run_path(run_id)
    if not run_path.exists():
        return []
    return [str(p.name) for p in run_path.glob("*") if p.is_file()]


def finalize_run(run_id: str) -> Path:
    """
    Polls ComfyUI for results, downloads images, and zips the run directory.
    """
    print(f"[orchestrator] Finalizing run for run_id: {run_id}")
    run_path = _get_run_path(run_id)
    prompt_id_file = run_path / "prompt_id.txt"

    if not prompt_id_file.exists():
        raise FileNotFoundError(f"Could not find prompt_id.txt for run_id: {run_id}")

    prompt_id = prompt_id_file.read_text().strip()

    with httpx.Client(timeout=30) as client:
        # 1. Poll for history
        history_url = f"{COMFY_API_URL.rstrip('/')}/history/{prompt_id}"
        print(f"[orchestrator] Polling history at {history_url}")
        while True:
            response = client.get(history_url)
            response.raise_for_status()
            history = response.json()
            if prompt_id in history:
                print(f"[orchestrator] History found for prompt_id: {prompt_id}")
                break
            print(f"[orchestrator] Waiting for results... (poll in {POLL_INTERVAL}s)")
            time.sleep(POLL_INTERVAL)

        # 2. Download output images
        outputs = history[prompt_id].get("outputs", {})
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                for image_data in node_output["images"]:
                    filename = image_data["filename"]
                    view_url = f"{COMFY_API_URL.rstrip('/')}/view?filename={filename}"
                    print(f"[orchestrator] Downloading image: {filename} from {view_url}")

                    img_response = client.get(view_url)
                    img_response.raise_for_status()

                    with open(run_path / filename, "wb") as f:
                        f.write(img_response.content)
                    print(f"[orchestrator] Saved image to {run_path / filename}")

    # 3. Zip the run folder
    zip_path_base = RUNS_DIR / run_id
    shutil.make_archive(
        base_name=str(zip_path_base),
        format='zip',
        root_dir=run_path
    )
    zip_path = zip_path_base.with_suffix(".zip")
    print(f"[orchestrator] Created zip file: {zip_path}")

    return zip_path
