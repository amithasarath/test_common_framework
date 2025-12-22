# test-common-framework

Common utility functions for reuse across projects.

## Installation

### From GitHub (via Poetry)

```bash
# Add to the project's pyproject.toml
poetry add git+https://github.com/org/test_common_framework.git

# Or with a specific version/tag
poetry add git+https://github.com/org/test_common_framework.git@v1.0.0

# Or with a specific branch
poetry add git+https://github.com/org/test_common_framework.git@main
```

### For Development

```bash
git clone https://github.com/org/test_common_framework.git
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
| `dev` | Alpha version | `1.0.0-alpha.1`, `1.0.0-alpha.2` |
| `stg` | Beta version | `1.0.0-beta.1`, `1.0.0-beta.2` |
| `feature/*` | Feature version | `1.0.0-feature.1`, `1.0.0-feature.2` |

### Automatic Version Bumping

On push to `main`, the version is **automatically bumped** based on the commit message prefix:

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
3. Determines bump type from **last commit message**
4. Updates `version.py` and `pyproject.toml`
5. Creates and pushes git tag (e.g., `v0.1.6`)

### Multiple Commits in One Push

The workflow reads only the **last commit message**. If a PR has multiple commits with different prefixes, only the last one is used.

**Recommended:** Use **Squash Merge** in GitHub when merging PRs. This combines all commits into one with a single message.

```
PR commits:
  - fix: bug 1
  - fix: bug 2
  - feat: new feature

Squash merge with message:
  "feat: add new feature with bug fixes"

Result: MINOR bump (feat: prefix used)
```

### Version Access

```python
>>> from test_common_framework import __version__
>>> print(__version__)
'0.1.6'
```

### GitHub Actions Workflows

This repository uses 3 workflow files located in `.github/workflows/`:

| File | Purpose |
|------|---------|
| **ci.yml** | Validates build by running `poetry install` |
| **version-bump.yml** | Bumps version, updates `version.py`, creates git tag (main only) |
| **dev-version.yml** | Creates pre-release versions and tags (dev/stg/feature branches) |

#### Why Two Version YAML Files?

| Aspect | dev-version.yml | version-bump.yml |
|--------|-----------------|------------------|
| **Trigger** | All branches except main | Main only |
| **Version format** | `1.0.0-alpha.1` (with suffix) | `1.0.0` (clean) |
| **Creates git tag?** | ✅ Yes (`v1.0.0-alpha.1`) | ✅ Yes (`v1.0.0`) |
| **Reads commit prefix?** | ❌ No | ✅ Yes (fix/feat/breaking) |

Different logic required for pre-release vs production versions, so kept separate for clarity.

#### Workflow Triggers

Each workflow defines when it runs in the `on:` section:

```yaml
# ci.yml
on:
  push:
    branches: [main, dev, stg]
  pull_request:
    branches: [main]

# version-bump.yml
on:
  push:
    branches: [main]

# dev-version.yml
on:
  push:
    branches-ignore: [main]
```

**Note:** `branches-ignore: [main]` means "run on ALL branches EXCEPT main". This automatically covers `dev`, `stg`, `feature/*`, and any other branch without needing to list them explicitly.

The `dev-version.yml` workflow determines the version prefix based on branch name:

| Branch | Version Prefix | Example |
|--------|---------------|---------|
| `feature/*` | feature | `0.3.4-feature.1` |
| `dev` | alpha | `0.3.4-alpha.1` |
| `stg` | beta | `0.3.4-beta.1` |
| any other | alpha | `0.3.4-alpha.1` |

#### When Each Workflow Runs

Since `main` branch is protected (PR only), the actual execution is:

| Action | ci.yml | version-bump.yml | dev-version.yml |
|--------|:------:|:----------------:|:---------------:|
| Push to `feature/*` | - | - | ✅ |
| Push to `dev` | ✅ | - | ✅ |
| Push to `stg` | ✅ | - | ✅ |
| Open PR to `main` | ✅ | - | - |
| Merge PR to `main` | ✅ | ✅ | - |

#### Workflow Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                  WORKFLOW EXECUTION (PR-based)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. PUSH TO feature/xyz                                         │
│     └──► dev-version.yml                                        │
│         └── Creates version: 0.3.4-feature.1                    │
│                                                                 │
│  2. PUSH TO dev                                                 │
│     ├──► ci.yml (validates build)                               │
│     └──► dev-version.yml                                        │
│         └── Creates version: 0.3.4-alpha.1                      │
│                                                                 │
│  3. PUSH TO stg                                                 │
│     ├──► ci.yml (validates build)                               │
│     └──► dev-version.yml                                        │
│         └── Creates version: 0.3.4-beta.1                       │
│                                                                 │
│  4. OPEN PR TO main                                             │
│     └──► ci.yml (validates code before review)                  │
│                                                                 │
│  5. MERGE PR TO main                                            │
│     ├──► ci.yml (validates build)                               │
│     └──► version-bump.yml                                       │
│         ├── Bumps version: 0.3.4 → 0.3.5                        │
│         ├── Updates version.py                                  │
│         └── Creates tag: v0.3.5                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Typical Development Flow

```
feature/new-util ──► dev ──► stg ──► PR to main ──► main
       │              │       │            │           │
       ▼              ▼       ▼            ▼           ▼
  0.3.4-feature.1  alpha.2  beta.1    (validates)   v0.3.5
```

## Using in AWS Lambda Projects

### Step 1: Add Dependency to Lambda Project

**This specifies which version of test-common-framework the Lambda will use.**

In the Lambda project, create or update `pyproject.toml`:

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
# Change "v0.1.1" to the required version
test-common-framework = {git = "https://github.com/org/test_common_framework.git", tag = "v0.1.1"}

# ============================================
# Public packages from PyPI
# ============================================
requests = "^2.31.0"
watchtower = "^3.0.1"
opencv-python-headless = "^4.8.0"    # Use headless for Lambda (no GUI dependencies)
boto3 = "^1.34.0"
pydantic = "^2.5.0"

# Add any other required packages...

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
│  github.com/org/                        github.com/org/                     │
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

1. **Update test_common_framework** → new version `v0.1.5` is created automatically
2. **Update Lambda project's `pyproject.toml`** → change `tag = "v0.1.5"`
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
test-common-framework = {git = "https://github.com/org/test_common_framework.git", tag = "v0.1.5"}
```

#### Three Separate Workflows

| Workflow | File | Triggers On | What It Does |
|----------|------|-------------|--------------|
| **Build PyPI Layer** | `build-pypi-layer.yml` | `pyproject.toml` changes | `poetry install --only pypi` → Layer 1 |
| **Build Framework Layer** | `build-framework-layer.yml` | `pyproject.toml` changes | `poetry install --only framework` → Layer 2 |
| **Deploy Lambda** | `deploy-lambda.yml` | `lambda_function.py` or `src/**` | Deploys code, attaches BOTH layers |

#### How Layer is Created Automatically

Each layer workflow runs on a **GitHub Actions runner** (temporary Ubuntu VM) and performs these steps:

```
┌─────────────────────────────────────────────────────────────────┐
│                  GITHUB ACTIONS RUNNER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ubuntu-latest (temporary VM)                                   │
│                                                                 │
│  /home/runner/work/project/                                     │
│  ├── pyproject.toml                                             │
│  ├── .venv/                    ← Created by Poetry              │
│  │   └── lib/python3.11/site-packages/                          │
│  │       ├── requests/                                          │
│  │       └── boto3/                                             │
│  └── layer/                    ← Created by workflow            │
│      └── python/lib/python3.11/site-packages/                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Workflow steps:**

```
┌─────────────────────────────────────────────────────────────────┐
│                  AUTOMATIC LAYER CREATION                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: Configure Poetry                                       │
│  └── poetry config virtualenvs.in-project true                  │
│      └── Tells Poetry to create .venv inside project folder     │
│                                                                 │
│  Step 2: Install packages                                       │
│  └── poetry install --only <group>                              │
│      └── Packages installed to: .venv/lib/python3.11/site-packages/│
│                                                                 │
│  Step 3: Create Lambda layer folder structure                   │
│  └── Creates: layer/python/lib/python3.11/site-packages/        │
│                                                                 │
│  Step 4: Copy packages to layer folder                          │
│  └── Copies all packages from .venv to layer folder             │
│                                                                 │
│  Step 5: Clean up unnecessary files                             │
│  └── Removes __pycache__, .pyc, .dist-info to reduce size       │
│                                                                 │
│  Step 6: Create zip file                                        │
│  └── Zips the python/ folder → layer.zip                        │
│                                                                 │
│  Step 7: Publish to AWS Lambda                                  │
│  └── Uploads layer.zip and creates new layer version            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Note:** The `.venv` and `layer/` folders exist only during the workflow run. After the layer is uploaded to AWS, the runner VM is destroyed.

**Final Layer Structure (uploaded to AWS):**

```
layer.zip
└── python/
    └── lib/
        └── python3.11/
            └── site-packages/
                ├── requests/
                ├── boto3/
                └── ... (all packages)
```

**Note:** PyPI layer is created once and rarely changes. Framework layer rebuilds when version tag is updated.

#### Layer Versioning (How Updates Work)

AWS Lambda layers use **versioning**. Each update creates a new version (old versions are kept):

```
┌─────────────────────────────────────────────────────────────────┐
│                  LAYER VERSIONING                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer: pypi-dependencies-layer                                 │
│                                                                 │
│  Version 1 (old)     arn:aws:lambda:...:layer:1  ← Still exists │
│  Version 2 (old)     arn:aws:lambda:...:layer:2  ← Still exists │
│  Version 3 (new)     arn:aws:lambda:...:layer:3  ← Lambda uses  │
│                                                                 │
│  Lambda function updated to point to → Version 3                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**No deletion happens.** Each `publish-layer-version` creates a new version number. Lambda is updated to use the latest version.

#### When New Layer is Created vs Reused

The workflow is **trigger-based**, not **content-based**:

| Scenario | Result |
|----------|--------|
| `pyproject.toml` unchanged | Workflow doesn't run, existing layer used |
| `pyproject.toml` changed | NEW layer version created |
| `pyproject.toml` reverted to old version | NEW layer version created (even if same content) |

```
┌─────────────────────────────────────────────────────────────────┐
│                  LAYER CREATION BEHAVIOR                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  pyproject.toml changed → workflow runs → NEW layer created     │
│                                                                 │
│  Example (even if reverted to same packages):                   │
│  Version 1: requests==2.31.0                                    │
│  Version 2: requests==2.32.0  (updated)                         │
│  Version 3: requests==2.31.0  (reverted) ← Still creates NEW    │
│                                                                 │
│  No "smart check" for duplicate content.                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**To reuse a specific layer version:** Manually specify the layer ARN in `deploy-lambda.yml` instead of auto-fetching latest.

#### How GitHub Actions Controls AWS

GitHub Actions connects to AWS using credentials stored as secrets:

```
┌─────────────────────────────────────────────────────────────────┐
│                  GITHUB → AWS CONNECTION                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GitHub Secrets (configured in repo settings):                  │
│  ├── AWS_ACCESS_KEY_ID      ← IAM user access key               │
│  └── AWS_SECRET_ACCESS_KEY  ← IAM user secret key               │
│                                                                 │
│  Workflow steps:                                                │
│  1. configure-aws-credentials  ← Authenticates with AWS         │
│  2. aws lambda publish-layer-version  ← Uploads layer           │
│  3. aws lambda update-function-configuration  ← Attaches layer  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### CLI vs Infrastructure-as-Code

| Approach | Tool | What It Does |
|----------|------|--------------|
| **Current (CLI)** | AWS CLI in GitHub Actions | Updates existing Lambda and layers |
| **IaC** | Terraform, CloudFormation, CDK | Creates and manages entire infrastructure |

**Current approach assumes Lambda function already exists in AWS.** For full infrastructure management, use Terraform or CloudFormation.

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

### Step 4: Use in Lambda Code

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

**Note:** `opencv-python-headless` is large (~50MB). If size limits are exceeded:

1. **Split into multiple layers** - one for opencv, one for other packages
2. **Use Lambda container images** - no size limit for container-based Lambdas
3. **Remove unused packages** - only include required packages

### Required GitHub Secrets

Add these secrets to the Lambda project repository:

| Secret | Description |
|--------|-------------|
| `GH_TOKEN` | GitHub Personal Access Token with `repo` scope (for accessing test_common_framework) |
| `AWS_ACCESS_KEY_ID` | AWS IAM access key with Lambda permissions |
| `AWS_SECRET_ACCESS_KEY` | AWS IAM secret key |

### How to Create GH_TOKEN

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token with `repo` scope
3. Copy and add as `GH_TOKEN` secret in the Lambda project

### Updating to a New Version

To update test-common-framework in the Lambda project:

```bash
# Update to a specific version
poetry add git+https://github.com/org/test_common_framework.git@v1.1.0

# Or update to latest main
poetry add git+https://github.com/org/test_common_framework.git@main
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

To create a Lambda layer manually without CI/CD:

1. **Configure Poetry** - Set Poetry to create the virtual environment inside the project folder
2. **Install dependencies** - Install only the required dependency group (e.g., `pypi` or `framework`)
3. **Create layer folder structure** - Create `layer/python/lib/python3.11/site-packages/`
4. **Copy packages** - Copy all installed packages from `.venv/lib/python3.11/site-packages/` to the layer folder
5. **Clean up** - Remove `__pycache__`, `.pyc` files, and `.dist-info` folders to reduce size
6. **Create zip** - Zip the `python` folder inside the layer directory
7. **Upload to AWS** - Use AWS CLI or Console to publish the layer with the zip file

### Adding a New Layer (Future Packages)

To add more PyPI packages as a **separate layer**, follow these 3 steps:

#### Step 1: Add New Dependency Group in pyproject.toml

```toml
# Existing layers
[tool.poetry.group.pypi]
optional = true

[tool.poetry.group.pypi.dependencies]
requests = "^2.31.0"

# NEW LAYER: Add new group
[tool.poetry.group.ml]
optional = true

[tool.poetry.group.ml.dependencies]
numpy = "^1.26.0"
pandas = "^2.1.0"
scikit-learn = "^1.3.0"
```

#### Step 2: Create New Workflow for the Layer

Create `.github/workflows/build-ml-layer.yml`:

```yaml
name: Build ML Layer

on:
  push:
    branches: [main]
    paths:
      - 'pyproject.toml'
  workflow_dispatch:

env:
  PYTHON_VERSION: "3.11"
  AWS_REGION: "us-east-1"
  LAYER_NAME: "ml-dependencies-layer"

jobs:
  build-ml-layer:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      - uses: snok/install-poetry@v1

      - name: Install ML dependencies only
        run: |
          poetry config virtualenvs.in-project true
          poetry install --only ml --no-interaction

      - name: Build Lambda Layer
        run: |
          mkdir -p layer/python/lib/python${{ env.PYTHON_VERSION }}/site-packages
          cp -r .venv/lib/python${{ env.PYTHON_VERSION }}/site-packages/* \
            layer/python/lib/python${{ env.PYTHON_VERSION }}/site-packages/
          find layer -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
          find layer -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
          cd layer && zip -r ../ml-layer.zip python

      - uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Publish Layer
        run: |
          aws lambda publish-layer-version \
            --layer-name ${{ env.LAYER_NAME }} \
            --description "ML packages: numpy, pandas, scikit-learn" \
            --zip-file fileb://ml-layer.zip \
            --compatible-runtimes python${{ env.PYTHON_VERSION }}
```

#### Step 3: Update deploy-lambda.yml to Attach New Layer

```yaml
env:
  PYPI_LAYER_NAME: "pypi-dependencies-layer"
  FRAMEWORK_LAYER_NAME: "framework-layer"
  ML_LAYER_NAME: "ml-dependencies-layer"      # Add new layer

# Add step to get new layer ARN
- name: Get ML layer version
  id: get-ml-layer
  run: |
    LAYER_ARN=$(aws lambda list-layer-versions \
      --layer-name ${{ env.ML_LAYER_NAME }} \
      --query 'LayerVersions[0].LayerVersionArn' \
      --output text)
    echo "ml_layer_arn=$LAYER_ARN" >> $GITHUB_OUTPUT

# Update attach step to include all layers
- name: Attach all layers to Lambda
  run: |
    aws lambda update-function-configuration \
      --function-name ${{ env.FUNCTION_NAME }} \
      --layers \
        "${{ steps.get-pypi-layer.outputs.pypi_layer_arn }}" \
        "${{ steps.get-framework-layer.outputs.framework_layer_arn }}" \
        "${{ steps.get-ml-layer.outputs.ml_layer_arn }}"
```

#### Summary: Adding New Layer

```
┌─────────────────────────────────────────────────────────────────┐
│  To Add a New Layer:                                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. pyproject.toml                                              │
│     └── Add [tool.poetry.group.NEW_NAME.dependencies]           │
│                                                                 │
│  2. .github/workflows/build-NEW_NAME-layer.yml                  │
│     └── poetry install --only NEW_NAME                          │
│                                                                 │
│  3. .github/workflows/deploy-lambda.yml                         │
│     └── Add new layer ARN to --layers                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Key Poetry Commands

```bash
# Install only specific group
poetry install --only ml

# Install multiple groups
poetry install --only pypi,framework,ml

# Install all groups
poetry install --with pypi,framework,ml
```
