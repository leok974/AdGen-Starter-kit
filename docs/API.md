# AdGen API Reference

This document provides a reference for the AdGen backend API endpoints.

**Base URL**: The API is served from the root of the deployed service (e.g., `http://localhost:8000`).

---

## Health Checks

### `GET /health`

Checks the basic health of the API server.

*   **Success Response (200 OK)**:
    ```json
    {
      "ok": true
    }
    ```

### `GET /health/detailed`

Provides a detailed health check, including the status of external dependencies like storage and the ComfyUI API.

*   **Success Response (200 OK)**:
    ```json
    {
      "api": "ok",
      "timestamp": 1678886400.0,
      "storage": "ok",
      "graph": "ok",
      "comfy": "ok",
      "ok": true
    }
    ```
*   **Error Response (200 OK with `ok: false`)**: If a dependency is down, the overall status will be `false`.
    ```json
    {
      "api": "ok",
      "timestamp": 1678886400.0,
      "storage": "ok",
      "graph": "ok",
      "comfy": "error: [Errno 111] Connection refused",
      "ok": false
    }
    ```

---

## Run Management

### `POST /generate`

Starts a new ad generation run.

*   **Request Body**:
    ```json
    {
      "prompt": "A futuristic sports car on a neon-lit highway",
      "negative_prompt": "blurry, old, vintage",
      "seed": 12345
    }
    ```
*   **Success Response (200 OK)**:
    ```json
    {
      "run_id": "a1b2c3d4e5f6",
      "status": "RUNNING",
      "prompt_id": "f7g8h9i0j1k2"
    }
    ```
*   **Failure Response (200 OK)**: If the generation fails to start, the API still returns a `run_id` so the client can track the failure.
    ```json
    {
      "run_id": "a1b2c3d4e5f6",
      "status": "FAILED",
      "error": "[Errno 111] Connection refused"
    }
    ```

### `GET /runs`

Lists all past and current generation runs.

*   **Success Response (200 OK)**:
    ```json
    [
      {
        "run_id": "a1b2c3d4e5f6",
        "prompt": "A futuristic sports car...",
        "status": "COMPLETED",
        "created_at": "2025-08-21T12:00:00+0000",
        "finished_at": "2025-08-21T12:01:30+0000",
        "duration": 90
      },
      {
        "run_id": "b2c3d4e5f6g7",
        "prompt": "A cat wearing a top hat",
        "status": "RUNNING",
        "created_at": "2025-08-21T12:05:00+0000",
        "finished_at": null,
        "duration": null
      }
    ]
    ```

### `GET /runs/{run_id}`

Retrieves detailed information for a specific run, including its inputs and generated artifacts.

*   **Success Response (200 OK)**:
    ```json
    {
      "run_id": "a1b2c3d4e5f6",
      "status": "COMPLETED",
      "created_at": "2025-08-21T12:00:00+0000",
      "finished_at": "2025-08-21T12:01:30+0000",
      "inputs": {
        "prompt": "A futuristic sports car...",
        "negative_prompt": "blurry, old, vintage"
      },
      "artifacts": [
        {
          "filename": "a1b2c3d4e5f6_00001.png",
          "type": "image",
          "url": "/runs/a1b2c3d4e5f6/files/a1b2c3d4e5f6_00001.png"
        }
      ]
    }
    ```
*   **Error Response (404 Not Found)**: If the `run_id` does not exist.

### `POST /finalize/{run_id}`

Triggers the finalization process for a run. This involves polling ComfyUI for results, downloading the artifacts, and creating a ZIP archive.

*   **Success Response (200 OK)**: Returns the final, detailed run metadata.
*   **Error Response (404 Not Found)**: If the `run_id` does not exist.

### `POST /runs/{run_id}/cancel`

Cancels a `PENDING` or `RUNNING` run.

*   **Success Response (200 OK)**: Returns the updated run metadata with a `CANCELLED` status.
*   **Error Response (404 Not Found)**: If the `run_id` does not exist.

### `DELETE /runs/{run_id}`

Deletes a run and all its associated artifacts (run directory and ZIP file).

*   **Success Response (204 No Content)**
*   **Error Response (400 Bad Request)**: If the `run_id` format is invalid.
*   **Error Response (500 Internal Server Error)**: If the deletion fails.

---

## Artifacts

### `GET /download/{run_id}`

Downloads the ZIP archive for a completed run.

*   **Success Response (200 OK)**: The response body will be the binary content of the ZIP file.
*   **Error Response (404 Not Found)**: If the ZIP file for the `run_id` does not exist.
