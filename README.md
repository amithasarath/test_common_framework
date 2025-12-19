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

# Option A: Pin to specific version (RECOMMENDED for production)
# Change "v0.1.1" to the version you need
test-common-framework = {git = "https://github.com/amithasarath/test_common_framework.git", tag = "v0.1.1"}

# Option B: Use latest from main branch
# test-common-framework = {git = "https://github.com/amithasarath/test_common_framework.git", branch = "main"}

# Option C: Use specific commit
# test-common-framework = {git = "https://github.com/amithasarath/test_common_framework.git", rev = "abc123"}

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### Step 2: Create Lambda Layer via GitHub Actions

Create `.github/workflows/build-layer.yml` in your Lambda project:

```yaml
name: Build and Deploy Lambda Layer

on:
  push:
    branches: [main]
  workflow_dispatch:  # Allow manual trigger

env:
  PYTHON_VERSION: "3.11"
  AWS_REGION: "us-east-1"
  LAYER_NAME: "common-framework-layer"

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

      - name: Configure Git for GitHub repos
        run: |
          git config --global url."https://${{ secrets.GH_TOKEN }}@github.com/".insteadOf "https://github.com/"

      - name: Export dependencies to requirements.txt
        run: |
          poetry export -f requirements.txt --without-hashes --output requirements.txt
          echo "=== requirements.txt ==="
          cat requirements.txt

      - name: Build Lambda Layer structure
        run: |
          # Lambda layers require this exact directory structure
          mkdir -p layer/python/lib/python${{ env.PYTHON_VERSION }}/site-packages

          # Install dependencies into layer directory
          pip install \
            --target layer/python/lib/python${{ env.PYTHON_VERSION }}/site-packages \
            --requirement requirements.txt \
            --no-cache-dir

          # Show what's installed
          echo "=== Installed packages ==="
          ls -la layer/python/lib/python${{ env.PYTHON_VERSION }}/site-packages/

      - name: Package Lambda Layer
        run: |
          cd layer
          zip -r ../layer.zip python
          cd ..
          echo "=== Layer zip size ==="
          ls -lh layer.zip

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Publish Lambda Layer
        id: publish-layer
        run: |
          # Get version from test-common-framework
          FRAMEWORK_VERSION=$(grep "test-common-framework" requirements.txt | grep -oP '@v\K[0-9.]+' || echo "latest")

          # Publish layer with description
          LAYER_ARN=$(aws lambda publish-layer-version \
            --layer-name ${{ env.LAYER_NAME }} \
            --description "Common framework v${FRAMEWORK_VERSION}" \
            --zip-file fileb://layer.zip \
            --compatible-runtimes python${{ env.PYTHON_VERSION }} \
            --query 'LayerVersionArn' \
            --output text)

          echo "layer_arn=$LAYER_ARN" >> $GITHUB_OUTPUT
          echo "=== Published Layer ARN ==="
          echo "$LAYER_ARN"

      - name: Output Layer ARN
        run: |
          echo "## Lambda Layer Published" >> $GITHUB_STEP_SUMMARY
          echo "**Layer ARN:** \`${{ steps.publish-layer.outputs.layer_arn }}\`" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "Add this layer to your Lambda function to use test-common-framework." >> $GITHUB_STEP_SUMMARY
```

### Step 3: Deploy Lambda Function with Layer

Create `.github/workflows/deploy-lambda.yml`:

```yaml
name: Deploy Lambda Function

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'lambda_function.py'

env:
  PYTHON_VERSION: "3.11"
  AWS_REGION: "us-east-1"
  FUNCTION_NAME: "my-lambda-function"
  LAYER_NAME: "common-framework-layer"

jobs:
  deploy:
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
          echo "layer_arn=$LAYER_ARN" >> $GITHUB_OUTPUT
          echo "Using layer: $LAYER_ARN"

      - name: Package Lambda function
        run: |
          # Package only your Lambda code (dependencies are in the layer)
          zip -r function.zip lambda_function.py src/

      - name: Deploy Lambda function
        run: |
          # Update function code
          aws lambda update-function-code \
            --function-name ${{ env.FUNCTION_NAME }} \
            --zip-file fileb://function.zip

          # Wait for update to complete
          aws lambda wait function-updated \
            --function-name ${{ env.FUNCTION_NAME }}

          # Attach the layer
          aws lambda update-function-configuration \
            --function-name ${{ env.FUNCTION_NAME }} \
            --layers ${{ steps.get-layer.outputs.layer_arn }}
```

### Step 4: Use in Your Lambda Code

```python
# lambda_function.py
from test_common_framework import __version__
from test_common_framework.utils import (
    setup_logger,
    safe_json_loads,
    retry,
    get_nested_value,
)

# Setup logger
logger = setup_logger("my_lambda")

def lambda_handler(event, context):
    logger.info(f"Using test-common-framework version: {__version__}")

    # Parse incoming JSON safely
    body = safe_json_loads(event.get("body", "{}"), default={})

    # Get nested values safely
    user_id = get_nested_value(body, "user.id", default="unknown")

    return {
        "statusCode": 200,
        "body": f"Processed request for user: {user_id}"
    }
```

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
poetry export -f requirements.txt --without-hashes -o requirements.txt

# Create layer structure
mkdir -p layer/python/lib/python3.11/site-packages
pip install -t layer/python/lib/python3.11/site-packages -r requirements.txt

# Create zip
cd layer && zip -r ../layer.zip python

# Upload to AWS
aws lambda publish-layer-version \
  --layer-name common-framework-layer \
  --zip-file fileb://layer.zip \
  --compatible-runtimes python3.11
```
