"""
ScriptForge AI — Unit Tests for File Ingestion Module
"""

import asyncio
import os
import tempfile
import pytest

from app.config import settings
from app.modules.file_ingestion import get_file_preview, ingest_file, validate_file


def test_validate_file_extensions():
    # Allowed
    valid, msg = validate_file("test.py.txt", 100)
    assert valid is True
    assert msg == ""

    valid, msg = validate_file("data.json", 500)
    assert valid is True

    valid, msg = validate_file("notes.md", 200)
    assert valid is True

    valid, msg = validate_file("config.yaml", 300)
    assert valid is True

    # Disallowed
    valid, msg = validate_file("malicious.exe", 100)
    assert valid is False
    assert "not supported" in msg

    valid, msg = validate_file("script.sh", 100)
    assert valid is False


def test_validate_file_size():
    valid, msg = validate_file("test.txt", 0)
    assert valid is False
    assert "empty" in msg

    # Large file limit
    valid, msg = validate_file("test.txt", 100 * 1024 * 1024)
    assert valid is False
    assert "exceeds maximum" in msg


def test_get_file_preview():
    short = "Hello world"
    assert get_file_preview(short) == short

    long_str = "x" * 5000
    preview = get_file_preview(long_str, max_chars=100)
    assert len(preview) > 100
    assert "[truncated" in preview


def test_ingest_json_file():
    content = '{"name": "ScriptForge", "type": "agent", "version": 1}'
    test_path = settings.UPLOAD_DIR / "test_sample.json"
    test_path.write_text(content, encoding="utf-8")

    try:
        result = asyncio.run(ingest_file(str(test_path), "sample.json"))
        assert result["file_type"] == "json"
        assert result["parsed_data"]["name"] == "ScriptForge"
        assert result["content"] == content
    finally:
        if test_path.exists():
            test_path.unlink()


def test_ingest_csv_file():
    content = "id,name,role\n1,Alice,Engineer\n2,Bob,Architect"
    test_path = settings.UPLOAD_DIR / "test_team.csv"
    test_path.write_text(content, encoding="utf-8")

    try:
        result = asyncio.run(ingest_file(str(test_path), "team.csv"))
        assert result["file_type"] == "csv"
        assert len(result["parsed_data"]) == 2
        assert result["parsed_data"][0]["name"] == "Alice"
        assert result["metadata"]["columns"] == ["id", "name", "role"]
    finally:
        if test_path.exists():
            test_path.unlink()
