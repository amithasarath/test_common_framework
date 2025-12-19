"""
Helper functions for the Lambda project.
"""

from test_common_framework.utils import get_nested_value, safe_json_dumps


def format_response(status_code: int, body: dict) -> dict:
    """Format a standard API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": safe_json_dumps(body),
    }


def extract_user_info(event: dict) -> dict:
    """Extract user information from the event."""
    return {
        "user_id": get_nested_value(event, "requestContext.authorizer.claims.sub", default="anonymous"),
        "email": get_nested_value(event, "requestContext.authorizer.claims.email", default=""),
    }
