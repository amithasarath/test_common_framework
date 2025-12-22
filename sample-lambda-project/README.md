# Sample Lambda Project

This is a sample Lambda project that uses **two separate layers**:
1. **PyPI Layer** - Public packages (requests, watchtower, opencv, etc.)
2. **Framework Layer** - Private package (test_common_framework from GitHub)

## Project Structure

```
sample-lambda-project/
├── lambda_function.py
├── src/
│   ├── __init__.py
│   └── helpers.py
├── pyproject.toml              # Two dependency groups (pypi + framework)
├── .gitignore
└── .github/
    └── workflows/
        ├── build-pypi-layer.yml      # Builds PyPI packages layer
        ├── build-framework-layer.yml # Builds framework layer
        └── deploy-lambda.yml         # Deploys Lambda, attaches BOTH layers
```

## Two-Layer Architecture

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

## pyproject.toml (Key File)

```toml
[tool.poetry.dependencies]
python = "^3.11"

# LAYER 1: PyPI packages
[tool.poetry.group.pypi]
optional = true

[tool.poetry.group.pypi.dependencies]
requests = "^2.31.0"
watchtower = "^3.0.1"
opencv-python-headless = "^4.8.0"
boto3 = "^1.34.0"
pydantic = "^2.5.0"

# LAYER 2: Framework (from GitHub)
[tool.poetry.group.framework]
optional = true

[tool.poetry.group.framework.dependencies]
test-common-framework = {git = "https://github.com/amithasarath/test_common_framework.git", tag = "v0.1.5"}
```

## Three Separate Workflows

| Workflow | File | Triggers On | What It Does |
|----------|------|-------------|--------------|
| **Build PyPI Layer** | `build-pypi-layer.yml` | `pyproject.toml` changes | Builds layer with PyPI packages |
| **Build Framework Layer** | `build-framework-layer.yml` | `pyproject.toml` changes | Builds layer with framework |
| **Deploy Lambda** | `deploy-lambda.yml` | `lambda_function.py` or `src/**` | Deploys code, attaches BOTH layers |

## Workflow Flow

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
│                              Lambda with BOTH layers                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Detailed Workflow Breakdown

### 1. build-pypi-layer.yml

Creates Lambda layer with public PyPI packages (requests, boto3, etc.)

```
┌─────────────────────────────────────────────────────────────────┐
│                  build-pypi-layer.yml                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TRIGGER:                                                       │
│  └── Push to main + pyproject.toml changed                      │
│  └── Manual trigger (workflow_dispatch)                         │
│                                                                 │
│  STEPS:                                                         │
│  1. Checkout code                                               │
│  2. Set up Python 3.11                                          │
│  3. Install Poetry                                              │
│  4. poetry install --only pypi  ← Only PyPI packages            │
│  5. Create layer folder structure                               │
│  6. Copy packages from .venv to layer/                          │
│  7. Remove __pycache__, .pyc, .dist-info                        │
│  8. Zip → pypi-layer.zip                                        │
│  9. Configure AWS credentials                                   │
│  10. aws lambda publish-layer-version  ← Upload to AWS          │
│                                                                 │
│  OUTPUT: pypi-dependencies-layer (new version in AWS)           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. build-framework-layer.yml

Creates Lambda layer with test_common_framework (private GitHub package)

```
┌─────────────────────────────────────────────────────────────────┐
│                  build-framework-layer.yml                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TRIGGER:                                                       │
│  └── Push to main + pyproject.toml changed                      │
│  └── Manual trigger (workflow_dispatch)                         │
│                                                                 │
│  STEPS:                                                         │
│  1. Checkout code                                               │
│  2. Set up Python 3.11                                          │
│  3. Install Poetry                                              │
│  4. Configure Git with GH_TOKEN  ← Access private repo          │
│  5. poetry install --only framework  ← Only framework           │
│  6. Create layer folder structure                               │
│  7. Copy packages from .venv to layer/                          │
│  8. Remove __pycache__, .pyc, .dist-info                        │
│  9. Zip → framework-layer.zip                                   │
│  10. Configure AWS credentials                                  │
│  11. aws lambda publish-layer-version  ← Upload to AWS          │
│                                                                 │
│  OUTPUT: framework-layer (new version in AWS)                   │
│                                                                 │
│  NOTE: Uses GH_TOKEN to access private GitHub repository        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3. deploy-lambda.yml

Deploys Lambda function code and attaches both layers

```
┌─────────────────────────────────────────────────────────────────┐
│                  deploy-lambda.yml                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TRIGGER:                                                       │
│  └── Push to main + lambda_function.py or src/** changed        │
│  └── Manual trigger (workflow_dispatch)                         │
│                                                                 │
│  STEPS:                                                         │
│  1. Checkout code                                               │
│  2. Configure AWS credentials                                   │
│  3. Get latest PyPI layer ARN (list-layer-versions)             │
│  4. Get latest Framework layer ARN (list-layer-versions)        │
│  5. Zip Lambda code → function.zip                              │
│  6. aws lambda update-function-code  ← Deploy code              │
│  7. aws lambda wait function-updated  ← Wait for completion     │
│  8. aws lambda update-function-configuration --layers           │
│     └── Attach BOTH layers to Lambda function                   │
│                                                                 │
│  OUTPUT: Lambda function updated with new code + both layers    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow Comparison

| Aspect | build-pypi-layer.yml | build-framework-layer.yml | deploy-lambda.yml |
|--------|---------------------|--------------------------|-------------------|
| **Trigger** | pyproject.toml change | pyproject.toml change | Code change (*.py) |
| **Installs** | `--only pypi` | `--only framework` | Nothing (just zips) |
| **Creates** | Layer zip | Layer zip | Function zip |
| **AWS Command** | `publish-layer-version` | `publish-layer-version` | `update-function-code` |
| **Needs GH_TOKEN** | ❌ No | ✅ Yes (private repo) | ❌ No |

### When Each Workflow Runs

| Changed File | build-pypi-layer | build-framework-layer | deploy-lambda |
|--------------|:----------------:|:---------------------:|:-------------:|
| `pyproject.toml` | ✅ | ✅ | ❌ |
| `lambda_function.py` | ❌ | ❌ | ✅ |
| `src/**` | ❌ | ❌ | ✅ |
| Both | ✅ | ✅ | ✅ |

## Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `GH_TOKEN` | GitHub Personal Access Token with `repo` scope (for framework layer) |
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |

## Local Development

```bash
# Install ALL dependencies (both groups)
poetry install --with pypi,framework

# Install only PyPI packages
poetry install --only pypi

# Install only framework
poetry install --only framework

# Run tests
poetry run pytest
```

## Updating Versions

### Update PyPI package version:
```toml
# In pyproject.toml
requests = "^2.32.0"  # Changed version
```
→ Push to main → `build-pypi-layer.yml` runs

### Update framework version:
```toml
# In pyproject.toml
test-common-framework = {git = "...", tag = "v0.1.6"}  # New tag
```
→ Push to main → `build-framework-layer.yml` runs

### Update Lambda code:
→ Push to main → `deploy-lambda.yml` runs (uses existing layers)
