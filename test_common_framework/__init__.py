"""
test_common_framework - Common utility functions for reuse across projects.

Usage:
    >>> import test_common_framework
    >>> print(test_common_framework.__version__)
    '0.1.0'

    >>> from test_common_framework import __version__
    >>> print(__version__)
    '0.1.0'
"""

from test_common_framework.version import __version__, get_version, get_version_tuple

# Import utility modules for easy access
from test_common_framework import utils

__all__ = [
    "__version__",
    "get_version",
    "get_version_tuple",
    "utils",
]
