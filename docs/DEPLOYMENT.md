# Deployment Guide

This document explains how to deploy the AdGen platform, including both the backend API and the frontend application.

## 1. Local Development Setup

The local development environment uses Docker Compose to run the FastAPI backend and a local Next.js development server for the frontend.

### Prerequisites

*   Docker and Docker Compose
*   Node.js and npm (or yarn/pnpm)
*   An instance of ComfyUI running and accessible to the backend container.

### Backend (FastAPI)

1.  **Navigate to the `adgen` directory.**
2.  **Configure Environment**: The `docker-compose.dev.yml` file is pre-configured for local development. It expects ComfyUI to be running on the host machine at `http://host.docker.internal:8188`.
3.  **Start the Service**:
    ```bash
    docker compose -f adgen/docker-compose.dev.yml up --build
    ```
4.  **Verify**: The API should be available at `http://localhost:8000`. You can check its health by visiting `http://localhost:8000/health`.

### Frontend (Next.js)

1.  **Navigate to the `adgen-frontend` directory.**
2.  **Install Dependencies**:
    ```bash
    npm install
    ```
3.  **Configure Environment**: The `.env.local` file should point to the local backend API:
    ```
    NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
    ```
4.  **Start the Development Server**:
    ```bash
    npm run dev
    ```
5.  **Verify**: The frontend should be available at `http://localhost:3000`.

## 2. Cloud Deployment (Google Cloud Run)

The application is designed to be deployed to Google Cloud Run. We provide scripts to automate this process.

### Prerequisites

*   Google Cloud SDK (`gcloud`) installed and configured.
*   A GCP project with the Cloud Build and Cloud Run APIs enabled.
*   Permissions to submit builds and deploy services.
*   A running ComfyUI instance accessible from the internet.

### Production Deployment

1.  **Set Environment Variables**:
    ```bash
    export PROJECT_ID=your-gcp-project-id
    export COMFY_ENDPOINT=https://your-comfy-api-url.com
    ```
2.  **Run the Deployment Script**:
    ```bash
    bash scripts/deploy.sh
    ```
    This script will:
    *   Build the Docker image using Cloud Build.
    *   Push the image to Google Artifact Registry.
    *   Deploy the image to Cloud Run with production settings.

### Staging Deployment

The staging deployment uses the API's **Test Mode**, which mocks calls to ComfyUI. This is useful for testing the API and frontend without needing a live ComfyUI backend.

1.  **Set Environment Variable**:
    ```bash
    export PROJECT_ID=your-gcp-project-id
    ```
2.  **Run the Staging Deployment Script**:
    ```bash
    bash scripts/deploy-staging.sh
    ```
    This will deploy a separate service (e.g., `adgen-api-staging`) with `COMFY_MODE=test` enabled.

## 3. Environment Configuration

The backend API is configured entirely through environment variables.

| Variable              | Default                            | Description                                                                 |
| --------------------- | ---------------------------------- | --------------------------------------------------------------------------- |
| `PORT`                | `8080`                             | The port the container listens on. Mapped to `8000` on the host in local dev. |
| `COMFY_MODE`          | `api`                              | Set to `test` for CI/mocking, or `hotfolder` for file-based workflows.        |
| `COMFY_API`           | `http://host.docker.internal:8188` | The URL of the ComfyUI API.                                                 |
| `RUNS_DIR`            | `/app/adgen/runs`                  | The directory to store run artifacts. For Cloud Run, this must be `/tmp`.   |
| `GRAPH_PATH`          | `/app/adgen/graphs/qwen.json`      | The path to the default ComfyUI workflow graph.                               |
| `RUN_RETENTION_HOURS` | `24`                               | How long to keep run artifacts before the startup retention sweep cleans them up. |

## 4. Monitoring and Logging

*   **Local**: Use `docker logs adgen-api` to view the logs of the running backend container.
*   **Cloud Run**: All `print` statements and logs from the FastAPI application are automatically sent to **Google Cloud Logging**. You can view them in the GCP console under your Cloud Run service.
*   **Health Checks**: The `/health/detailed` endpoint can be used as a readiness probe in a production environment to ensure the service is fully operational before it receives traffic.
