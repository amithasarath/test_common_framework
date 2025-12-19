# test-common-framework

Common utility functions for reuse across projects.

## Installation

### From GitHub (via Poetry)

```bash
# Add to your project's pyproject.toml
poetry add git+https://github.com/your-username/test_common_framework.git

# Or with a specific version/tag
poetry add git+https://github.com/your-username/test_common_framework.git@v1.0.0

# Or with a specific branch
poetry add git+https://github.com/your-username/test_common_framework.git@main
```

### For Development

```bash
git clone https://github.com/your-username/test_common_framework.git
cd test_common_framework
poetry install
```

## Usage

```python
import test_common_framework

# Check version
print(test_common_framework.__version__)

# Use utilities
from test_common_framework.utils import (
    setup_logger,
    safe_json_loads,
    retry,
    flatten_dict,
    get_nested_value,
    chunk_list,
)

# Example: Setup logger
logger = setup_logger("my_app")
logger.info("Hello!")

# Example: Safe JSON parsing
data = safe_json_loads('{"key": "value"}', default={})

# Example: Retry decorator
@retry(max_attempts=3, delay=1.0)
def unstable_function():
    pass
```

## Versioning

- **Main branch**: Rounded versions (e.g., `1.0.0`, `1.1.0`, `2.0.0`)
- **Feature branches**: Sub-versions (e.g., `1.0.0-dev.1`, `1.0.0-alpha.1`)

## Development

```bash
# Run tests
poetry run pytest

# Format code
poetry run black .

# Lint
poetry run flake8
```

## Using in AWS Lambda Projects

### Step 1: Add Dependency to Your Lambda Project

**This is where you specify which version of test-common-framework your Lambda will use.**

In your Lambda project, create or update `pyproject.toml`:

```toml
[tool.poetry]
name = "my-lambda-function"
version = "0.1.0"
description = "My Lambda function"

[tool.poetry.dependencies]
python = "^3.11"

# ============================================
# Private package from GitHub (this framework)
# ============================================
# Change "v0.1.1" to the version you need
test-common-framework = {git = "https://github.com/amithasarath/test_common_framework.git", tag = "v0.1.1"}

# ============================================
# Public packages from PyPI
# ============================================
requests = "^2.31.0"
watchtower = "^3.0.1"
opencv-python-headless = "^4.8.0"    # Use headless for Lambda (no GUI dependencies)
boto3 = "^1.34.0"
pydantic = "^2.5.0"

# Add any other packages you need...

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**All packages listed here will be included in the Lambda layer.**

#### Version Pinning Options for test-common-framework

| Method | Syntax | Use Case |
|--------|--------|----------|
| Tag (recommended) | `tag = "v0.1.1"` | Production - locked to specific release |
| Branch | `branch = "main"` | Development - always get latest |
| Commit | `rev = "abc123"` | Lock to exact commit |

### Two Repository Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TWO SEPARATE REPOSITORIES                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  REPO 1: test_common_framework          REPO 2: my-lambda-project           │
│  ─────────────────────────────          ─────────────────────────           │
│  github.com/amithasarath/               github.com/amithasarath/            │
│  test_common_framework                  my-lambda-project                   │
│                                                                             │
│  ├── test_common_framework/             ├── lambda_function.py              │
│  │   ├── __init__.py                    ├── src/                            │
│  │   ├── version.py                     ├── pyproject.toml  ◄── specifies  │
│  │   └── utils.py                       │                       version     │
│  ├── pyproject.toml                     └── .github/workflows/              │
│  └── .github/workflows/                     └── deploy.yml                  │
│      ├── ci.yml                                                             │
│      └── version-bump.yml                                                   │
│                                                                             │
│         │                                         │                         │
│         ▼                                         ▼                         │
│  On merge to main:                       On merge to main:                  │
│  - Runs tests                            - Builds layer (poetry install)    │
│  - Bumps version (0.1.4 → 0.1.5)         - Publishes layer to AWS           │
│  - Creates git tag (v0.1.5)              - Deploys Lambda function          │
│                                          - Attaches layer to Lambda         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### How It Works

1. **You update test_common_framework** → new version `v0.1.5` is created automatically
2. **You update Lambda project's `pyproject.toml`** → change `tag = "v0.1.5"`
3. **Lambda project CI/CD runs** → builds layer with new version, deploys Lambda

### Step 2: Lambda Project GitHub Actions Workflow

Create `.github/workflows/deploy.yml` in your **Lambda project repository**:

```yaml
name: Build Layer and Deploy Lambda

on:
  push:
    branches: [main]
  workflow_dispatch:  # Allow manual trigger

env:
  PYTHON_VERSION: "3.11"
  AWS_REGION: "us-east-1"
  LAYER_NAME: "common-framework-layer"
  FUNCTION_NAME: "my-lambda-function"

jobs:
  # ============================================
  # JOB 1: Build and Publish Lambda Layer
  # This pulls test_common_framework from GitHub
  # ============================================
  build-layer:
    runs-on: ubuntu-latest
    outputs:
      layer_arn: ${{ steps.publish-layer.outputs.layer_arn }}

    steps:
      - name: Checkout Lambda project code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: latest

      - name: Configure Git for GitHub repos
        run: |
          # This allows Poetry to pull test_common_framework from GitHub
          git config --global url."https://${{ secrets.GH_TOKEN }}@github.com/".insteadOf "https://github.com/"

      - name: Install all dependencies with Poetry
        run: |
          poetry config virtualenvs.in-project true
          poetry install --only main --no-interaction

          echo "=== All installed packages (including test_common_framework) ==="
          poetry show

      - name: Build Lambda Layer structure
        run: |
          mkdir -p layer/python/lib/python${{ env.PYTHON_VERSION }}/site-packages

          # Copy ALL packages from Poetry's venv to layer
          cp -r .venv/lib/python${{ env.PYTHON_VERSION }}/site-packages/* \
            layer/python/lib/python${{ env.PYTHON_VERSION }}/site-packages/

          # Remove unnecessary files to reduce layer size
          find layer -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
          find layer -type f -name "*.pyc" -delete 2>/dev/null || true
          find layer -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true

          echo "=== Layer contents ==="
          ls -la layer/python/lib/python${{ env.PYTHON_VERSION }}/site-packages/

      - name: Package Lambda Layer
        run: |
          cd layer && zip -r ../layer.zip python
          echo "=== Layer zip size ==="
          ls -lh ../layer.zip

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Publish Lambda Layer to AWS
        id: publish-layer
        run: |
          # Get test_common_framework version from Poetry
          FRAMEWORK_VERSION=$(poetry show test-common-framework 2>/dev/null | grep 'version' | awk '{print $3}' || echo "latest")
          echo "test_common_framework version: $FRAMEWORK_VERSION"

          LAYER_ARN=$(aws lambda publish-layer-version \
            --layer-name ${{ env.LAYER_NAME }} \
            --description "Dependencies including test_common_framework v${FRAMEWORK_VERSION}" \
            --zip-file fileb://layer.zip \
            --compatible-runtimes python${{ env.PYTHON_VERSION }} \
            --query 'LayerVersionArn' \
            --output text)

          echo "layer_arn=$LAYER_ARN" >> $GITHUB_OUTPUT
          echo "=== Published Layer ARN ==="
          echo "$LAYER_ARN"

  # ============================================
  # JOB 2: Deploy Lambda Function
  # Runs AFTER layer is built (needs: build-layer)
  # ============================================
  deploy-lambda:
    runs-on: ubuntu-latest
    needs: build-layer  # <-- Waits for layer to be ready

    steps:
      - name: Checkout Lambda project code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Package Lambda function code only
        run: |
          # Package only YOUR code (dependencies are in the layer)
          zip -r function.zip lambda_function.py src/
          echo "=== Function zip size ==="
          ls -lh function.zip

      - name: Deploy Lambda function code
        run: |
          aws lambda update-function-code \
            --function-name ${{ env.FUNCTION_NAME }} \
            --zip-file fileb://function.zip

          aws lambda wait function-updated \
            --function-name ${{ env.FUNCTION_NAME }}

      - name: Attach Layer to Lambda function
        run: |
          # Use the layer ARN from Job 1
          LAYER_ARN="${{ needs.build-layer.outputs.layer_arn }}"
          echo "Attaching layer: $LAYER_ARN"

          aws lambda update-function-configuration \
            --function-name ${{ env.FUNCTION_NAME }} \
            --layers "$LAYER_ARN"

      - name: Deployment Summary
        run: |
          echo "## Deployment Complete" >> $GITHUB_STEP_SUMMARY
          echo "**Function:** ${{ env.FUNCTION_NAME }}" >> $GITHUB_STEP_SUMMARY
          echo "**Layer:** ${{ needs.build-layer.outputs.layer_arn }}" >> $GITHUB_STEP_SUMMARY
```

### Workflow Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│           Lambda Project: .github/workflows/deploy.yml          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ JOB 1: build-layer                                        │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ 1. poetry install                                         │  │
│  │    ├── Pulls test_common_framework from GitHub (v0.1.5)   │  │
│  │    ├── Pulls requests from PyPI                           │  │
│  │    ├── Pulls watchtower from PyPI                         │  │
│  │    └── Pulls opencv-python-headless from PyPI             │  │
│  │                                                           │  │
│  │ 2. Copy .venv → layer/                                    │  │
│  │ 3. Zip layer                                              │  │
│  │ 4. aws lambda publish-layer-version                       │  │
│  │ 5. Output: layer_arn                                      │  │
│  └────────────────────────┬─────────────────────────────────┘  │
│                           │                                     │
│                           ▼ needs: build-layer                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ JOB 2: deploy-lambda                                      │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ 1. Zip lambda_function.py + src/ (code only, small!)      │  │
│  │ 2. aws lambda update-function-code                        │  │
│  │ 3. aws lambda update-function-configuration --layers      │  │
│  │    (uses layer_arn from Job 1)                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Step 4: Use in Your Lambda Code

```python
# lambda_function.py

# ============================================
# Import from test-common-framework (private)
# ============================================
from test_common_framework import __version__
from test_common_framework.utils import (
    setup_logger,
    safe_json_loads,
    retry,
    get_nested_value,
)

# ============================================
# Import from public packages (PyPI)
# ============================================
import requests
import watchtower
import cv2  # opencv-python-headless
import boto3
from pydantic import BaseModel

# Setup logger with CloudWatch via watchtower
import logging
logger = setup_logger("my_lambda")

# Add CloudWatch handler
cw_handler = watchtower.CloudWatchLogHandler(log_group="my-lambda-logs")
logger.addHandler(cw_handler)


def lambda_handler(event, context):
    logger.info(f"Using test-common-framework version: {__version__}")

    # Parse incoming JSON safely (from test-common-framework)
    body = safe_json_loads(event.get("body", "{}"), default={})

    # Get nested values safely (from test-common-framework)
    user_id = get_nested_value(body, "user.id", default="unknown")

    # Use requests (public package)
    response = requests.get("https://api.example.com/data")

    # Use opencv (public package)
    # cv2.imread(), cv2.resize(), etc.

    return {
        "statusCode": 200,
        "body": f"Processed request for user: {user_id}"
    }
```

### Important: Lambda Layer Size Limits

| Limit | Size |
|-------|------|
| Single layer (zipped) | 50 MB |
| Single layer (unzipped) | 250 MB |
| All layers combined (unzipped) | 250 MB |

**Note:** `opencv-python-headless` is large (~50MB). If you hit size limits:

1. **Split into multiple layers** - one for opencv, one for other packages
2. **Use Lambda container images** - no size limit for container-based Lambdas
3. **Remove unused packages** - only include what you need

### Required GitHub Secrets

Add these secrets to your Lambda project repository:

| Secret | Description |
|--------|-------------|
| `GH_TOKEN` | GitHub Personal Access Token with `repo` scope (for accessing test_common_framework) |
| `AWS_ACCESS_KEY_ID` | AWS IAM access key with Lambda permissions |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key |

### How to Create GH_TOKEN

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Copy and add as `GH_TOKEN` secret in your Lambda project

### Updating to a New Version

To update test-common-framework in your Lambda project:

```bash
# Update to a specific version
poetry add git+https://github.com/amithasarath/test_common_framework.git@v1.1.0

# Or update to latest main
poetry add git+https://github.com/amithasarath/test_common_framework.git@main
```

Then push to trigger the CI/CD pipeline which will rebuild the layer.

### Lambda Layer Directory Structure

```
layer.zip
└── python/
    └── lib/
        └── python3.11/
            └── site-packages/
                ├── test_common_framework/
                │   ├── __init__.py
                │   ├── version.py
                │   └── utils.py
                └── ... (other dependencies)
```

### Manual Layer Creation (Local)

```bash
# In your Lambda project directory

# Configure Poetry to create virtualenv in project
poetry config virtualenvs.in-project true

# Install dependencies (only main, no dev)
poetry install --only main

# Create layer structure
mkdir -p layer/python/lib/python3.11/site-packages

# Copy packages from Poetry's virtual environment
cp -r .venv/lib/python3.11/site-packages/* layer/python/lib/python3.11/site-packages/

# Remove unnecessary files to reduce size
find layer -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find layer -type f -name "*.pyc" -delete 2>/dev/null || true
find layer -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true

# Create zip
cd layer && zip -r ../layer.zip python

# Upload to AWS
aws lambda publish-layer-version \
  --layer-name common-framework-layer \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11
```
