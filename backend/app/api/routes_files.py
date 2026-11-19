"""
ScriptForge AI — File Routes
Endpoints for uploading and retrieving uploaded files.
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.config import settings
from app.database import get_db
from app.models.schemas import FileResponse
from app.modules.file_ingestion import get_file_preview, validate_file

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/files", tags=["Files"])


@router.post("/upload", response_model=list[FileResponse], status_code=status.HTTP_201_CREATED)
async def upload_files(files: list[UploadFile] = File(...)):
    """Upload one or more files for analysis and script generation."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided.",
        )

    if len(files) > settings.MAX_FILES_PER_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many files. Maximum is {settings.MAX_FILES_PER_UPLOAD}.",
        )

    responses: list[FileResponse] = []

    for upload_file in files:
        filename = upload_file.filename or "unnamed_file.txt"
        file_bytes = await upload_file.read()
        file_size = len(file_bytes)

        # Validate file size and extension
        is_valid, error_msg = validate_file(filename, file_size)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File validation failed for '{filename}': {error_msg}",
            )

        file_id = uuid4().hex
        ext = Path(filename).suffix.lower()
        safe_name = f"{file_id}{ext}"
        saved_path = settings.UPLOAD_DIR / safe_name

        # Save to disk
        try:
            with open(saved_path, "wb") as f:
                f.write(file_bytes)
        except Exception as e:
            logger.error("Failed to save file %s: %s", filename, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file '{filename}' on server.",
            )

        # Detect text preview
        preview_text = ""
        encoding = "utf-8"
        for enc in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
            try:
                decoded = file_bytes.decode(enc)
                preview_text = get_file_preview(decoded)
                encoding = enc
                break
            except (UnicodeDecodeError, AttributeError):
                continue

        now_str = datetime.now(timezone.utc).isoformat()

        # Save record in database
        with get_db() as db:
            db.execute(
                """
                INSERT INTO files (id, filename, original_name, content_type, file_size, file_path, encoding, upload_time, content_preview)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    file_id,
                    safe_name,
                    filename,
                    upload_file.content_type or "text/plain",
                    file_size,
                    str(saved_path),
                    encoding,
                    now_str,
                    preview_text,
                ),
            )

        responses.append(
            FileResponse(
                id=file_id,
                filename=safe_name,
                original_name=filename,
                content_type=upload_file.content_type,
                file_size=file_size,
                upload_time=now_str,
                preview=preview_text,
            )
        )
        logger.info("Uploaded file %s as %s (size %d)", filename, file_id, file_size)

    return responses


@router.get("/{file_id}", response_model=FileResponse)
def get_file_details(file_id: str):
    """Get metadata and preview of an uploaded file."""
    with get_db() as db:
        row = db.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File '{file_id}' not found.",
            )
        return FileResponse(
            id=row["id"],
            filename=row["filename"],
            original_name=row["original_name"],
            content_type=row["content_type"],
            file_size=row["file_size"],
            upload_time=row["upload_time"],
            preview=row["content_preview"],
        )
