# API Reference

This document provides a reference for the AdGen API endpoints.

## Base URL

The base URL for the API depends on the environment:

-   **Local Development:** `http://localhost:8000`
-   **Production:** `https://your-service-name.run.app`

## Endpoints

### Health Checks

#### `GET /health`

Checks the basic health of the API server.

-   **Success Response (200 OK):**
    ```json
    {
      "status": "ok"
    }
    ```

#### `GET /health/detailed`

Provides a detailed health check, including connectivity to the ComfyUI backend.

-   **Success Response (200 OK):**
    ```json
    {
      "api": "ok",
      "comfy_ui": "ok"
    }
    ```
-   **Error Response (503 Service Unavailable):**
    ```json
    {
      "api": "ok",
      "comfy_ui": "error: connection failed"
    }
    ```

### Generation

#### `POST /generate`

Starts a new ad generation run.

-   **Request Body:**
    ```json
    {
      "prompt": "a photo of a cat",
      "params": {
        "negative_prompt": "blurry, low quality",
        "seed": 12345
      }
    }
    ```
-   **Success Response (200 OK):**
    ```json
    {
      "run_id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8"
    }
    ```

#### `POST /finalize/{run_id}`

Finalizes a completed run by collecting the generated files into a ZIP archive.

-   **Path Parameters:**
    -   `run_id` (string, required): The ID of the run to finalize.
-   **Success Response (200 OK):**
    ```json
    {
      "status": "finalized",
      "files": ["image1.png", "image2.png"]
    }
    ```

### File Management

#### `GET /runs/{run_id}/files`

Lists the files available in a completed run.

-   **Path Parameters:**
    -   `run_id` (string, required): The ID of the run.
-   **Success Response (200 OK):**
    ```json
    {
      "run_id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8",
      "files": ["image1.png", "image2.png"]
    }
    ```

#### `GET /download/{run_id}`

Downloads a ZIP archive of all the files in a run.

-   **Path Parameters:**
    -   `run_id` (string, required): The ID of the run.
-   **Success Response (200 OK):**
    -   The response body will be a ZIP file (`application/zip`).

#### `DELETE /runs/{run_id}`

Deletes a run and all its associated files.

-   **Path Parameters:**
    -   `run_id` (string, required): The ID of the run to delete.
-   **Success Response (200 OK):**
    ```json
    {
      "status": "deleted",
      "run_id": "a1b2c3d4-e5f6-7890-g1h2-i3j4k5l6m7n8"
    }
    ```
