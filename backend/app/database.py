"""
ScriptForge AI — Database Layer
SQLite database with schema management and connection helper.
"""

import sqlite3
from contextlib import contextmanager
from .config import settings

DB_PATH = str(settings.DB_PATH)

SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    original_name TEXT NOT NULL,
    content_type TEXT,
    file_size INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    encoding TEXT DEFAULT 'utf-8',
    upload_time TEXT NOT NULL,
    content_preview TEXT
);

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'uploaded',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    task_type TEXT,
    recommended_language TEXT,
    analysis_json TEXT,
    execution_plan_json TEXT,
    generated_script TEXT,
    script_language TEXT,
    validation_json TEXT,
    execution_result_json TEXT,
    error_log TEXT,
    repair_attempts INTEGER DEFAULT 0,
    version_history_json TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS task_files (
    task_id TEXT NOT NULL,
    file_id TEXT NOT NULL,
    PRIMARY KEY (task_id, file_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS execution_logs (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    event_type TEXT NOT NULL,
    details TEXT,
    stdout TEXT,
    stderr TEXT,
    exit_code INTEGER,
    duration_ms INTEGER,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_task_files_task ON task_files(task_id);
CREATE INDEX IF NOT EXISTS idx_execution_logs_task ON execution_logs(task_id);
"""


def init_db():
    """Initialize the database schema."""
    with get_db() as db:
        db.executescript(SCHEMA)


@contextmanager
def get_db():
    """Context manager for database connections with auto-commit/rollback."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
