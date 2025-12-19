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

### Step 2: Lambda Project GitHub Actions Workflows

Create **two separate workflows** in your Lambda project repository:

#### Workflow 1: build-layer.yml (Builds Lambda Layer)

**Triggers when:** `pyproject.toml` or `poetry.lock` changes

Create `.github/workflows/build-layer.yml`:

```yaml
name: Build and Publish Lambda Layer

on:
  push:
    branches: [main]
    paths:
      - 'pyproject.toml'      # Trigger when dependencies change
      - 'poetry.lock'
  workflow_dispatch:          # Allow manual trigger

env:
  PYTHON_VERSION: "3.11"
  AWS_REGION: "us-east-1"
  LAYER_NAME: "my-lambda-dependencies"

jobs:
  build-layer:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          version: latest

      - name: Configure Git for private GitHub repos
        run: |
          git config --global url."https://${{ secrets.GH_TOKEN }}@github.com/".insteadOf "https://github.com/"

      - name: Install dependencies with Poetry
        run: |
          poetry config virtualenvs.in-project true
          poetry install --only main --no-interaction

          echo "=== Installed packages ==="
          poetry show

      - name: Build Lambda Layer
        run: |
          mkdir -p layer/python/lib/python${{ env.PYTHON_VERSION }}/site-packages

          cp -r .venv/lib/python${{ env.PYTHON_VERSION }}/site-packages/* \
            layer/python/lib/python${{ env.PYTHON_VERSION }}/site-packages/

          # Remove unnecessary files
          find layer -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
          find layer -type f -name "*.pyc" -delete 2>/dev/null || true
          find layer -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true

      - name: Package Lambda Layer
        run: |
          cd layer && zip -r ../layer.zip python
          ls -lh ../layer.zip

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Publish Lambda Layer
        run: |
          FRAMEWORK_VERSION=$(poetry show test-common-framework 2>/dev/null | grep 'version' | awk '{print $3}' || echo "unknown")

          aws lambda publish-layer-version \
            --layer-name ${{ env.LAYER_NAME }} \
            --description "Dependencies with test_common_framework v${FRAMEWORK_VERSION}" \
            --zip-file fileb://layer.zip \
            --compatible-runtimes python${{ env.PYTHON_VERSION }}
```

#### Workflow 2: deploy-lambda.yml (Deploys Lambda Function)

**Triggers when:** `lambda_function.py` or `src/**` changes

Create `.github/workflows/deploy-lambda.yml`:

```yaml
name: Deploy Lambda Function

on:
  push:
    branches: [main]
    paths:
      - 'lambda_function.py'   # Trigger when Lambda code changes
      - 'src/**'
  workflow_dispatch:           # Allow manual trigger

env:
  PYTHON_VERSION: "3.11"
  AWS_REGION: "us-east-1"
  FUNCTION_NAME: "my-lambda-function"
  LAYER_NAME: "my-lambda-dependencies"

jobs:
  deploy-lambda:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Get latest layer version
        id: get-layer
        run: |
          LAYER_ARN=$(aws lambda list-layer-versions \
            --layer-name ${{ env.LAYER_NAME }} \
            --query 'LayerVersions[0].LayerVersionArn' \
            --output text)

          if [ "$LAYER_ARN" == "None" ] || [ -z "$LAYER_ARN" ]; then
            echo "ERROR: No layer found. Run build-layer workflow first."
            exit 1
          fi

          echo "layer_arn=$LAYER_ARN" >> $GITHUB_OUTPUT
          echo "Using layer: $LAYER_ARN"

      - name: Package Lambda function
        run: |
          zip -r function.zip lambda_function.py src/
          ls -lh function.zip

      - name: Deploy Lambda function
        run: |
          aws lambda update-function-code \
            --function-name ${{ env.FUNCTION_NAME }} \
            --zip-file fileb://function.zip

          aws lambda wait function-updated \
            --function-name ${{ env.FUNCTION_NAME }}

      - name: Attach Layer to Lambda
        run: |
          aws lambda update-function-configuration \
            --function-name ${{ env.FUNCTION_NAME }} \
            --layers "${{ steps.get-layer.outputs.layer_arn }}"
```

### Two Separate Workflows Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    LAMBDA PROJECT: Two Separate Workflows                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WORKFLOW 1: build-layer.yml              WORKFLOW 2: deploy-lambda.yml     │
│  ─────────────────────────────            ──────────────────────────────    │
│  Triggers: pyproject.toml changes         Triggers: lambda_function.py      │
│            poetry.lock changes                      src/** changes          │
│                                                                             │
│  ┌─────────────────────────────┐          ┌─────────────────────────────┐  │
│  │ 1. poetry install           │          │ 1. Get latest layer ARN     │  │
│  │    ├── test_common_framework│          │    from AWS                 │  │
│  │    ├── requests             │          │                             │  │
│  │    ├── watchtower           │          │ 2. Zip lambda code only     │  │
│  │    └── opencv-headless      │          │    (small package!)         │  │
│  │                             │          │                             │  │
│  │ 2. Copy .venv → layer/      │          │ 3. Deploy function code     │  │
│  │ 3. Zip layer                │          │                             │  │
│  │ 4. Publish layer to AWS     │          │ 4. Attach layer to Lambda   │  │
│  └─────────────────────────────┘          └─────────────────────────────┘  │
│              │                                         │                    │
│              ▼                                         ▼                    │
│     Layer ARN stored in AWS ◄──────────────── Fetches latest layer ARN     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### When Each Workflow Runs

| Change Made | Workflow Triggered | What Happens |
|-------------|-------------------|--------------|
| Update `pyproject.toml` (new framework version) | `build-layer.yml` | New layer published to AWS |
| Update `lambda_function.py` | `deploy-lambda.yml` | Lambda code deployed, uses existing layer |
| Update both | Both workflows run | Layer rebuilt, then Lambda deployed |

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
