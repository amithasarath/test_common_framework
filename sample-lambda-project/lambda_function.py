"""
Sample Lambda function using test_common_framework and other dependencies.

This file demonstrates how to use packages from the Lambda layer.
"""

# ============================================
# Imports from test_common_framework (private GitHub repo)
# ============================================
from test_common_framework import __version__ as framework_version
from test_common_framework.utils import (
    setup_logger,
    safe_json_loads,
    safe_json_dumps,
    retry,
    get_nested_value,
    flatten_dict,
)

# ============================================
# Imports from public packages (PyPI)
# ============================================
import requests
import watchtower
import boto3
from pydantic import BaseModel
# import cv2  # opencv-python-headless - uncomment if needed

# ============================================
# Setup logging with CloudWatch integration
# ============================================
import logging

logger = setup_logger("my_lambda", level=logging.INFO)

# Optional: Add CloudWatch handler for watchtower
# cw_handler = watchtower.CloudWatchLogHandler(log_group="/aws/lambda/my-lambda")
# logger.addHandler(cw_handler)


# ============================================
# Pydantic models for request/response validation
# ============================================
class UserRequest(BaseModel):
    user_id: str
    action: str
    data: dict = {}


class LambdaResponse(BaseModel):
    status_code: int
    message: str
    data: dict = {}


# ============================================
# Helper functions using test_common_framework
# ============================================
@retry(max_attempts=3, delay=1.0, backoff=2.0)
def call_external_api(url: str) -> dict:
    """Call external API with automatic retry on failure."""
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


def process_event_data(event: dict) -> dict:
    """Process incoming event using test_common_framework utilities."""

    # Safely parse JSON body
    body = event.get("body", "{}")
    if isinstance(body, str):
        body = safe_json_loads(body, default={})

    # Get nested values safely
    user_id = get_nested_value(body, "user.id", default="anonymous")
    action = get_nested_value(body, "request.action", default="unknown")

    # Flatten nested data for logging
    flat_data = flatten_dict(body)
    logger.info(f"Flattened request data: {flat_data}")

    return {
        "user_id": user_id,
        "action": action,
        "raw_body": body,
    }


# ============================================
# Main Lambda handler
# ============================================
def lambda_handler(event, context):
    """
    Main Lambda handler function.

    Args:
        event: AWS Lambda event object
        context: AWS Lambda context object

    Returns:
        dict: API Gateway compatible response
    """
    logger.info(f"Lambda started - test_common_framework version: {framework_version}")
    logger.info(f"Event: {safe_json_dumps(event)}")

    try:
        # Process the incoming event
        processed = process_event_data(event)

        logger.info(f"Processing request for user: {processed['user_id']}")
        logger.info(f"Action: {processed['action']}")

        # Example: Call external API with retry
        # api_data = call_external_api("https://api.example.com/data")

        # Build response
        response = LambdaResponse(
            status_code=200,
            message="Request processed successfully",
            data={
                "user_id": processed["user_id"],
                "action": processed["action"],
                "framework_version": framework_version,
            }
        )

        return {
            "statusCode": response.status_code,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": safe_json_dumps(response.model_dump()),
        }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": safe_json_dumps({
                "error": str(e),
                "message": "Internal server error",
            }),
        }
