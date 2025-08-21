# Contributing to AdGen

First off, thank you for considering contributing to the AdGen project! Your help is greatly appreciated.

This document provides guidelines for contributing to the project.

## Development Setup

To get started with development, you'll need to set up both the backend and frontend environments. Please refer to the **[Deployment Guide](./docs/DEPLOYMENT.md)** for detailed instructions on the local development setup.

**Quick Summary:**

1.  **Backend**: Run the FastAPI server using Docker Compose.
    ```bash
    docker compose -f adgen/docker-compose.dev.yml up --build
    ```
2.  **Frontend**: Run the Next.js development server.
    ```bash
    cd adgen-frontend
    npm install
    npm run dev
    ```

## Code Style

*   **Python (Backend)**: We use `black` for code formatting and `flake8` for linting. Please ensure your code adheres to these standards before submitting a pull request.
*   **TypeScript/React (Frontend)**: We use the standard Next.js ESLint configuration. Please run `npm run lint` to check your code.

## Testing

*   **Backend**: The backend has a suite of smoke tests that can be run locally. These tests are also run in our GitHub Actions CI pipeline.
    ```bash
    # Run from the project root
    bash scripts/smoke.sh
    ```
*   **Frontend**: Frontend testing is not yet implemented.

## Pull Request Process

1.  **Fork the repository** and create your branch from `main`.
2.  **Make your changes**. Please ensure that your changes are well-tested.
3.  **Update the documentation**. If you are adding a new feature or changing an existing one, please update the relevant documentation in the `docs/` directory and the `README.md`.
4.  **Ensure the test suite passes**.
5.  **Issue a pull request** to the `main` branch. Please provide a clear description of your changes and why they are needed.

## Issue Reporting

If you find a bug or have a feature request, please create an issue on GitHub. We use issue templates to ensure that we have all the necessary information to address the issue.

*   **[Bug Report](./.github/ISSUE_TEMPLATE/bug_report.md)**
*   **[Feature Request](./.github/ISSUE_TEMPLATE/feature_request.md)**

Thank you again for your contribution!
