# ORCA CI Pipeline

This repository uses GitHub Actions for Continuous Integration. The pipeline ensures that the codebase remains healthy by running imports, health checks, and linting on every push and pull request.

## Pipeline Overview

The CI pipeline (`.github/workflows/ci.yml`) performs the following steps:
1.  **Environment Setup**: Initializes Python 3.10 and 3.11 environments.
2.  **Dependency Installation**: Installs requirements from `requirements.txt` and `requirements-dev.txt`.
3.  **Linting**: Runs `ruff` to check for code style and common errors.
4.  **Tests**:
    *   **Import Tests**: Verifies that main modules can be imported without error.
    *   **Health Checks**: Boots `orca_api` and `orca_runtime` in subprocesses and verifies their health endpoints.

## Local Verification

To run the same checks locally:

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

### 2. Run Linting
```bash
ruff check .
```

### 3. Run Tests
```bash
pytest -v -s tests/
```

## Integration Tests with External Services

By default, CI tests do not require external services (Ollama, LM Studio, etc.). If you want to run tests that interact with these services locally:

1.  Ensure the services are running on their default ports.
2.  Run the smoke scripts in the `tools/` directory:
    ```bash
    python tools/smoke_ollama.py
    python tools/smoke_orpheus.py
    ```

## Adding New Tests

New tests should be added to the `tests/` directory. Use `pytest` conventions (files named `test_*.py`).
