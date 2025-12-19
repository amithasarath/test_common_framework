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

| Branch | Version Format | Example |
|--------|----------------|---------|
| `main` | Rounded version | `1.0.0`, `1.1.0`, `2.0.0` |
| `dev` / `develop` | Alpha version | `1.0.0-alpha.1`, `1.0.0-alpha.2` |
| `feature/*` | Feature version | `1.0.0-feature.1`, `1.0.0-feature.2` |

### Automatic Version Bumping

When you push to `main`, the version is **automatically bumped** based on your commit message prefix:

| Commit Message Prefix | Bump Type | Example |
|----------------------|-----------|---------|
| `fix:`, `docs:`, `chore:`, etc. | **PATCH** | 0.1.5 → 0.1.6 |
| `feat:` or `feature:` | **MINOR** | 0.1.5 → 0.2.0 |
| `breaking:` or `major:` | **MAJOR** | 0.1.5 → 1.0.0 |

### Examples

```bash
# PATCH bump (0.1.5 → 0.1.6)
git commit -m "fix: resolve logging issue"
git commit -m "docs: update readme"
git commit -m "chore: cleanup code"

# MINOR bump (0.1.5 → 0.2.0)
git commit -m "feat: add new retry decorator"
git commit -m "feature: add JSON utilities"

# MAJOR bump (0.1.5 → 1.0.0)
git commit -m "breaking: remove deprecated functions"
git commit -m "major: redesign API"
```

### What Happens Automatically

1. `version-bump.yml` workflow triggers on push to `main`
2. Reads current version from `version.py`
3. Determines bump type from commit message
4. Updates `version.py` and `pyproject.toml`
5. Creates and pushes git tag (e.g., `v0.1.6`)

### Version Access

```python
>>> from test_common_framework import __version__
>>> print(__version__)
'0.1.6'
```

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

### Step 2: Lambda Project - Two Separate Layers

Use **two separate layers** for better separation:
1. **PyPI Layer** - Public packages (rarely changes)
2. **Framework Layer** - test_common_framework (changes when version updated)

#### pyproject.toml with Two Dependency Groups

```toml
[tool.poetry.dependencies]
python = "^3.11"

# LAYER 1: PyPI packages (public)
[tool.poetry.group.pypi]
optional = true

[tool.poetry.group.pypi.dependencies]
requests = "^2.31.0"
watchtower = "^3.0.1"
opencv-python-headless = "^4.8.0"
boto3 = "^1.34.0"
pydantic = "^2.5.0"

# LAYER 2: Framework (private GitHub)
[tool.poetry.group.framework]
optional = true

[tool.poetry.group.framework.dependencies]
test-common-framework = {git = "https://github.com/amithasarath/test_common_framework.git", tag = "v0.1.5"}
```

#### Three Separate Workflows

| Workflow | File | Triggers On | What It Does |
|----------|------|-------------|--------------|
| **Build PyPI Layer** | `build-pypi-layer.yml` | `pyproject.toml` changes | `poetry install --only pypi` → Layer 1 |
| **Build Framework Layer** | `build-framework-layer.yml` | `pyproject.toml` changes | `poetry install --only framework` → Layer 2 |
| **Deploy Lambda** | `deploy-lambda.yml` | `lambda_function.py` or `src/**` | Deploys code, attaches BOTH layers |

#### Two-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LAMBDA FUNCTION                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐   ┌─────────────────────────────┐         │
│  │  LAYER 1: PyPI packages     │   │  LAYER 2: Framework         │         │
│  │  pypi-dependencies-layer    │   │  framework-layer            │         │
│  ├─────────────────────────────┤   ├─────────────────────────────┤         │
│  │  ├── requests/              │   │  └── test_common_framework/ │         │
│  │  ├── watchtower/            │   │      ├── __init__.py        │         │
│  │  ├── opencv-python-headless/│   │      ├── version.py         │         │
│  │  ├── boto3/                 │   │      └── utils.py           │         │
│  │  └── pydantic/              │   │                             │         │
│  │                             │   │                             │         │
│  │  Rarely changes             │   │  Changes when framework     │         │
│  │  (stable versions)          │   │  version is updated         │         │
│  └─────────────────────────────┘   └─────────────────────────────┘         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Workflow Execution Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THREE SEPARATE WORKFLOWS                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  WORKFLOW 1                    WORKFLOW 2                 WORKFLOW 3        │
│  build-pypi-layer.yml          build-framework-layer.yml  deploy-lambda.yml │
│  ────────────────────          ───────────────────────    ─────────────────│
│  Trigger: pyproject.toml       Trigger: pyproject.toml    Trigger: code    │
│                                                                             │
│  ┌───────────────────┐         ┌───────────────────┐     ┌───────────────┐ │
│  │ poetry install    │         │ poetry install    │     │ Get both      │ │
│  │ --only pypi       │         │ --only framework  │     │ layer ARNs    │ │
│  │                   │         │                   │     │               │ │
│  │ Build layer       │         │ Build layer       │     │ Zip code      │ │
│  │ Publish to AWS    │         │ Publish to AWS    │     │ Deploy        │ │
│  └───────────────────┘         └───────────────────┘     │ Attach layers │ │
│           │                             │                └───────────────┘ │
│           ▼                             ▼                        │         │
│  pypi-dependencies-layer       framework-layer                   │         │
│           │                             │                        │         │
│           └─────────────────────────────┴────────────────────────┘         │
│                                         │                                   │
│                                         ▼                                   │
│                              Lambda with BOTH layers attached               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### When Each Workflow Runs

| Change Made | Workflow Triggered | What Happens |
|-------------|-------------------|--------------|
| Update PyPI package version | `build-pypi-layer.yml` | PyPI layer rebuilt |
| Update framework version tag | `build-framework-layer.yml` | Framework layer rebuilt |
| Update `lambda_function.py` | `deploy-lambda.yml` | Code deployed, uses existing layers |

**See `sample-lambda-project/` for complete workflow files.**

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
