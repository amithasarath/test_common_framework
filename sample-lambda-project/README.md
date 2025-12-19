# Sample Lambda Project

This is a sample Lambda project that uses `test_common_framework` from GitHub.

## Project Structure

```
sample-lambda-project/
├── lambda_function.py          # Main Lambda handler
├── src/
│   ├── __init__.py
│   └── helpers.py              # Helper functions
├── pyproject.toml              # Poetry dependencies (specifies framework version)
├── .gitignore
└── .github/
    └── workflows/
        ├── build-layer.yml     # Builds and publishes Lambda layer
        └── deploy-lambda.yml   # Deploys Lambda function code
```

## Dependencies (pyproject.toml)

```toml
[tool.poetry.dependencies]
# Private package from GitHub
test-common-framework = {git = "https://github.com/amithasarath/test_common_framework.git", tag = "v0.1.5"}

# Public packages from PyPI
requests = "^2.31.0"
watchtower = "^3.0.1"
opencv-python-headless = "^4.8.0"
```

## GitHub Workflows

### 1. build-layer.yml (Runs when dependencies change)

**Triggers:** `pyproject.toml` or `poetry.lock` changes

```
pyproject.toml changed
        │
        ▼
┌─────────────────────────────────────────┐
│  build-layer.yml                        │
├─────────────────────────────────────────┤
│  1. poetry install                      │
│     ├── Pull test_common_framework      │
│     │   from GitHub (tag: v0.1.5)       │
│     └── Pull PyPI packages              │
│                                         │
│  2. Copy .venv → layer/                 │
│  3. zip layer                           │
│  4. aws lambda publish-layer-version    │
└─────────────────────────────────────────┘
        │
        ▼
   Layer ARN: arn:aws:lambda:us-east-1:123:layer:my-layer:5
```

### 2. deploy-lambda.yml (Runs when code changes)

**Triggers:** `lambda_function.py` or `src/**` changes

```
lambda_function.py changed
        │
        ▼
┌─────────────────────────────────────────┐
│  deploy-lambda.yml                      │
├─────────────────────────────────────────┤
│  1. Get latest layer ARN from AWS       │
│  2. zip lambda_function.py + src/       │
│  3. aws lambda update-function-code     │
│  4. aws lambda update-function-config   │
│     --layers <layer_arn>                │
└─────────────────────────────────────────┘
```

## Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `GH_TOKEN` | GitHub Personal Access Token with `repo` scope |
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |

## Local Development

```bash
# Install dependencies
poetry install

# Run tests
poetry run pytest

# Check installed packages
poetry show
```

## Updating test_common_framework Version

1. Edit `pyproject.toml`:
   ```toml
   test-common-framework = {git = "...", tag = "v0.1.6"}  # New version
   ```

2. Push to main → `build-layer.yml` runs automatically

3. Layer is rebuilt with new version
