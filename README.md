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

## Using in AWS Lambda Projects via CI/CD

### Method 1: Direct Git Dependency in Lambda Project

In your Lambda project's `pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.9"
test-common-framework = {git = "https://github.com/amitha/test_common_framework.git", tag = "v1.0.0"}

# Or use main branch for latest
# test-common-framework = {git = "https://github.com/amitha/test_common_framework.git", branch = "main"}
```

### Method 2: GitHub Actions Workflow for Lambda Deployment

Create `.github/workflows/deploy-lambda.yml` in your Lambda project:

```yaml
name: Deploy Lambda

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install Poetry
        uses: snok/install-poetry@v1

      - name: Configure Git for private repos (if needed)
        run: |
          git config --global url."https://${{ secrets.GH_TOKEN }}@github.com/".insteadOf "https://github.com/"

      - name: Install dependencies
        run: |
          poetry config virtualenvs.create false
          poetry install --no-dev

      - name: Package for Lambda
        run: |
          mkdir -p package
          cp -r $(poetry env info --path)/lib/python*/site-packages/* package/ 2>/dev/null || \
          pip install -t package -r <(poetry export -f requirements.txt --without-hashes)
          cp -r your_lambda_code/* package/
          cd package && zip -r ../lambda.zip .

      - name: Deploy to AWS Lambda
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Update Lambda function
        run: |
          aws lambda update-function-code \
            --function-name your-lambda-function \
            --zip-file fileb://lambda.zip
```

### Method 3: Using Poetry Export for Lambda Layers

```yaml
# In your Lambda project's CI/CD
- name: Create Lambda Layer
  run: |
    poetry export -f requirements.txt --without-hashes > requirements.txt
    pip install -t python/lib/python3.11/site-packages -r requirements.txt
    zip -r layer.zip python
    aws lambda publish-layer-version \
      --layer-name common-framework-layer \
      --zip-file fileb://layer.zip \
      --compatible-runtimes python3.11
```

### Required GitHub Secrets

For private repositories, add these secrets to your Lambda project:

- `GH_TOKEN`: GitHub Personal Access Token with repo access
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key

### Alternative: Using SSH Deploy Key

For private repos, you can also use SSH:

```toml
[tool.poetry.dependencies]
test-common-framework = {git = "ssh://git@github.com/amitha/test_common_framework.git", tag = "v1.0.0"}
```

Add SSH key to GitHub Actions:

```yaml
- name: Setup SSH
  uses: webfactory/ssh-agent@v0.8.0
  with:
    ssh-private-key: ${{ secrets.DEPLOY_KEY }}
```
