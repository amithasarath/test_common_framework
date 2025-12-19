"""
Common utility functions for reuse across projects.

Add your common utility functions here.
"""

import json
import logging
from typing import Any, Dict, Optional
from functools import wraps
import time


def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up a logger with consistent formatting.

    Args:
        name: Logger name
        level: Logging level (default: INFO)
        format_string: Custom format string (optional)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)

        if format_string is None:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """
    Safely parse JSON string, returning default on failure.

    Args:
        json_string: JSON string to parse
        default: Value to return if parsing fails

    Returns:
        Parsed JSON object or default value
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Safely serialize object to JSON string.

    Args:
        obj: Object to serialize
        default: Value to return if serialization fails

    Returns:
        JSON string or default value
    """
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying a function with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff

            raise last_exception

        return wrapper
    return decorator


def flatten_dict(
    d: Dict[str, Any],
    parent_key: str = "",
    separator: str = "."
) -> Dict[str, Any]:
    """
    Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Prefix for keys (used in recursion)
        separator: Separator between nested keys

    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{separator}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, separator).items())
        else:
            items.append((new_key, v))
    return dict(items)


def get_nested_value(
    d: Dict[str, Any],
    key_path: str,
    default: Any = None,
    separator: str = "."
) -> Any:
    """
    Get a value from a nested dictionary using dot notation.

    Args:
        d: Dictionary to search
        key_path: Path to the value (e.g., "level1.level2.key")
        default: Value to return if path not found
        separator: Separator used in key_path

    Returns:
        Value at the path or default
    """
    keys = key_path.split(separator)
    result = d

    for key in keys:
        if isinstance(result, dict) and key in result:
            result = result[key]
        else:
            return default

    return result


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Split a list into chunks of specified size.

    Args:
        lst: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
