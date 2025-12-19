"""Tests for utility functions."""

import pytest
from test_common_framework import __version__, utils


def test_version():
    """Test that version is accessible."""
    assert __version__ is not None
    assert isinstance(__version__, str)


def test_safe_json_loads():
    """Test safe JSON parsing."""
    assert utils.safe_json_loads('{"key": "value"}') == {"key": "value"}
    assert utils.safe_json_loads('invalid json', default={}) == {}


def test_safe_json_dumps():
    """Test safe JSON serialization."""
    assert utils.safe_json_dumps({"key": "value"}) == '{"key": "value"}'


def test_flatten_dict():
    """Test dictionary flattening."""
    nested = {"a": {"b": {"c": 1}}}
    assert utils.flatten_dict(nested) == {"a.b.c": 1}


def test_get_nested_value():
    """Test nested value retrieval."""
    d = {"level1": {"level2": {"key": "value"}}}
    assert utils.get_nested_value(d, "level1.level2.key") == "value"
    assert utils.get_nested_value(d, "nonexistent", default="default") == "default"


def test_chunk_list():
    """Test list chunking."""
    lst = [1, 2, 3, 4, 5]
    assert utils.chunk_list(lst, 2) == [[1, 2], [3, 4], [5]]
