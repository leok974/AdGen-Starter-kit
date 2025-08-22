# AdGen System Architecture

This document provides a high-level overview of the AdGen system architecture, its components, and how they interact.

## 1. System Overview

The AdGen platform is designed as a decoupled, cloud-native application with three main parts:

1.  **Backend API (`adgen-api`)**: A Python FastAPI application responsible for orchestrating ad generation jobs.
2.  **Frontend UI (`adgen-frontend`)**: A Next.js single-page application that provides a user interface for creating and managing ad runs.
3.  **Generation Engine (ComfyUI)**: An external, GPU-powered service that takes a workflow graph and a prompt and produces the actual image or video assets.

The system is designed to be stateless where possible, with run artifacts and metadata persisted to a shared volume or cloud storage.

## 2. Component Interaction Flow

The primary interaction flow is as follows:

1.  A user interacts with the **Next.js Frontend** to define an ad generation job.
2.  The frontend sends a `POST /generate` request to the **FastAPI Backend**.
3.  The backend creates a run, patches a ComfyUI workflow graph, and submits it to the **ComfyUI Server**.
4.  The frontend polls the backend for status updates.
5.  Once the job is complete, the backend finalizes the run by collecting the artifacts from ComfyUI and creating a ZIP archive.
6.  The user can then download the results via the frontend.

## 3. API Patterns

*   **Asynchronous Operations**: Generation is handled asynchronously. A request to `/generate` immediately returns a `run_id` for tracking.
*   **Statelessness**: The API is stateless, with all run information stored in its corresponding directory. This supports horizontal scaling.
*   **RESTful Principles**: The API uses standard HTTP methods and status codes.
*   **Environment-Driven Configuration**: All configuration is managed via environment variables, adhering to 12-Factor App principles.

## 4. Error Handling

*   The API is designed to be resilient. If a connection to ComfyUI fails, the run is marked as "FAILED" and the client is notified, rather than returning a 500 error.
*   Detailed health checks (`/health/detailed`) provide insight into the status of external dependencies.

## 5. Test Mode

A `test` mode is available (`COMFY_MODE=test`) which mocks all calls to the ComfyUI backend. This enables cost-effective and reliable end-to-end testing of the API and frontend in a CI/CD environment without requiring a live GPU server.
