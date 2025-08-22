# Deployment Guide

This document outlines the procedures for deploying the AdGen application, both for local development and for production on Google Cloud.

## 1. Local Development

Local deployment is managed using Docker Compose. This is the recommended method for development and testing.

### Prerequisites

- Docker and Docker Compose installed.
- Git client.

### Steps

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/adgen-starter-kit.git
    cd adgen-starter-kit
    ```

2.  **Start the services:**
    The `docker-compose.dev.yml` file is configured to start the `adgen-api` and a mock ComfyUI service.

    ```bash
    docker compose -f adgen/docker-compose.dev.yml up --build
    ```

3.  **Verify the deployment:**
    Once the containers are running, you can test the API using the provided smoke test script.

    ```bash
    bash scripts/smoke.sh
    ```

    You should see a successful output indicating that the API is healthy and responding correctly.

## 2. Cloud Deployment (Google Cloud Run)

The application is designed to be deployed as a containerized service on Google Cloud Run.

### Prerequisites

- Google Cloud SDK (`gcloud`) installed and configured.
- A Google Cloud project with the Cloud Run and Cloud Build APIs enabled.
- A running ComfyUI instance accessible from the internet.

### Steps

1.  **Set environment variables:**
    Before running the deployment script, you need to set the following environment variables:

    ```bash
    export PROJECT_ID=your-gcp-project-id
    export COMFY_ENDPOINT=https://your-comfy-api-endpoint.com:8188
    ```

2.  **Run the deployment script:**
    The `deploy.sh` script automates the process of building the Docker image, pushing it to Google Container Registry, and deploying it to Cloud Run.

    ```bash

    bash scripts/deploy.sh
    ```

3.  **Verify the deployment:**
    After the script completes, it will output the URL of the deployed service. You can use the smoke test to verify it:

    ```bash
    bash scripts/smoke.sh https://your-service-name.run.app
    ```

### Staging Environment

A separate script is provided for deploying a staging version of the application. The staging environment runs in `test` mode, which mocks the ComfyUI backend. This is useful for testing API and frontend changes without incurring GPU costs.

1.  **Set the project ID:**
    ```bash
    export PROJECT_ID=your-gcp-project-id
    ```

2.  **Run the staging deployment script:**
    ```bash
    bash scripts/deploy-staging.sh
    ```
