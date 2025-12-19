"""
Version information for test_common_framework.

This file is the single source of truth for the package version.
- On main branch: Uses rounded versions (e.g., 1.0.0, 1.1.0, 2.0.0)
- On feature branches: Uses sub-versions (e.g., 1.0.0-dev.1, 1.0.0-alpha.1)
"""

__version__ = "0.3.11"

# Version components for programmatic access
VERSION_MAJOR = 0
VERSION_MINOR = 3
VERSION_PATCH = 11
VERSION_SUFFIX = ""  # e.g., "dev.1", "alpha.1", "rc.1" for non-main branches


def get_version() -> str:
    """Return the full version string."""
    return __version__


def get_version_tuple() -> tuple:
    """Return version as a tuple (major, minor, patch, suffix)."""
    return (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH, VERSION_SUFFIX)
