# AdGen + ComfyUI Workflow

This document explains the full end-to-end workflow for generating images using the **AdGen API** together with **ComfyUI**.

---

## Overview

1. **Generate** → AdGen API creates a new run and stores metadata.
2. **ComfyUI** → Produces images based on the prompt.
3. **Finalize** → AdGen API collects the images from ComfyUI, copies them into the run directory, and creates a ZIP archive.
4. **Download** → Retrieve the packaged ZIP file containing your generated content.

---

## Step-by-Step (PowerShell)

```powershell
# 1. Generate
$payload = @{ prompt = "Your prompt here" } | ConvertTo-Json
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/generate" `
    -Method Post -ContentType "application/json" -Body $payload
$runId = $response.run_id
$runId

# 2. Wait for ComfyUI to complete
# Watch the ComfyUI terminal to see when generation finishes.

# 3. Finalize (collect + package outputs)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/finalize/$runId" -Method Post

# 4. Download results
Invoke-WebRequest "http://127.0.0.1:8000/download/$runId" `
    -OutFile "results_$runId.zip"
```

---

## Expected Output

* A ZIP file named `results_<runId>.zip`
* Inside: generated PNGs (or other media) for the run

Example:

```
results_4885950c8a3a.zip
 ├── 4885950c8a3a_00001_.png  (920 KB)
 └── 4885950c8a3a_00002_.png  (3.5 MB)
```

---

## Notes

* The AdGen API sets up run directories and manages packaging.
* ComfyUI must be running and configured to output images during the process.
* If you want files to persist on your host automatically, mount the `runs` directory as a Docker volume (see `docker-compose.dev.yml`).
