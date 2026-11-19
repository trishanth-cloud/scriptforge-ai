"""
ScriptForge AI — File Ingestion Module
Read files, detect encoding, parse by extension.
"""

import csv
import io
import json
import logging
from pathlib import Path
from typing import Any

import yaml
import defusedxml.ElementTree as ET

from app.config import settings

logger = logging.getLogger(__name__)

# Extension categories
PARSEABLE_JSON = {".json"}
PARSEABLE_CSV = {".csv"}
PARSEABLE_XML = {".xml"}
PARSEABLE_YAML = {".yaml", ".yml"}
PLAIN_TEXT = {".txt", ".md", ".log"}


async def ingest_file(file_path: str, original_name: str) -> dict:
    """
    Read a file from disk, detect its encoding, and parse based on extension.
    Returns dict with: content, encoding, parsed_data, file_type, metadata.
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    content = ""
    encoding = "utf-8"
    parsed_data: Any = None
    metadata: dict[str, Any] = {"original_name": original_name, "size": path.stat().st_size}
    raw = path.read_bytes()
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            content = raw.decode(enc)
            encoding = enc
            break
        except (UnicodeDecodeError, ValueError):
            continue
    else:
        content = raw.decode("utf-8", errors="replace")
        encoding = "utf-8"

    # Parse based on extension
    file_type = _extension_to_type(ext)
    try:
        if ext in PARSEABLE_JSON:
            parsed_data = json.loads(content)
        elif ext in PARSEABLE_CSV:
            reader = csv.DictReader(io.StringIO(content))
            parsed_data = list(reader)
            metadata["row_count"] = len(parsed_data)
            metadata["columns"] = reader.fieldnames or []
        elif ext in PARSEABLE_XML:
            root = ET.fromstring(content)
            parsed_data = _xml_to_dict(root)
        elif ext in PARSEABLE_YAML:
            parsed_data = yaml.safe_load(content)
        else:
            parsed_data = None
    except Exception as exc:
        logger.warning("Failed to parse %s as %s: %s", original_name, file_type, exc)
        parsed_data = None

    metadata["line_count"] = content.count("\n") + 1

    return {
        "content": content,
        "encoding": encoding,
        "parsed_data": parsed_data,
        "file_type": file_type,
        "metadata": metadata,
    }


def get_file_preview(content: str, max_chars: int = 2000) -> str:
    """Return the first max_chars characters of content with truncation indicator if needed."""
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + f"\n... [truncated, {len(content) - max_chars} more characters]"


def validate_file(filename: str, file_size: int) -> tuple[bool, str]:
    """Validate filename extension and file size against config limits."""
    if file_size <= 0:
        return False, "File is empty (0 bytes)."
    ext = Path(filename).suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        return False, f"File extension '{ext}' is not supported. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
    if file_size > settings.MAX_FILE_SIZE:
        max_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        return False, f"File size ({file_size} bytes) exceeds maximum limit of {max_mb:.1f} MB."
    return True, ""


def _extension_to_type(ext: str) -> str:
    """Map file extension to a human-readable type."""
    mapping = {
        ".json": "json",
        ".csv": "csv",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".txt": "text",
        ".md": "markdown",
        ".log": "log",
    }
    return mapping.get(ext, "unknown")


def _xml_to_dict(element) -> dict:
    """Recursively convert an XML element to a dict."""
    result: dict[str, Any] = {"tag": element.tag}
    if element.attrib:
        result["attributes"] = dict(element.attrib)
    children = list(element)
    if children:
        result["children"] = [_xml_to_dict(c) for c in children]
    if element.text and element.text.strip():
        result["text"] = element.text.strip()
    return result
