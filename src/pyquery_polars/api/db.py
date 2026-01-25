from typing import Optional, List, Dict, Any

import sqlite3
import os
import time
import uuid

DB_PATH = os.path.join(os.getcwd(), "workspace", "api_jobs.db")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Jobs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_jobs (
            job_id TEXT PRIMARY KEY,
            status TEXT,
            dataset_name TEXT,
            exporter_name TEXT,
            file_path TEXT,
            duration REAL,
            error TEXT,
            file_size TEXT,
            created_at REAL,
            updated_at REAL
        )
    ''')

    # Uploads Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_uploads (
            upload_id TEXT PRIMARY KEY,
            filename TEXT,
            size_bytes INTEGER,
            checksum TEXT,
            uploaded_at REAL,
            status TEXT
        )
    ''')

    # Downloads Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_downloads (
            download_id TEXT PRIMARY KEY,
            filename TEXT,
            requested_at REAL,
            client_ip TEXT
        )
    ''')

    conn.commit()
    conn.close()

# --- Jobs ---


def create_job(job_id: str, dataset_name: str, exporter_name: str, file_path: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO api_jobs (job_id, status, dataset_name, exporter_name, file_path, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (job_id, "RUNNING", dataset_name, exporter_name, file_path, time.time(), time.time()))
    conn.commit()
    conn.close()


def update_job_status(job_id: str, status: str, duration: float = 0.0, error: Optional[str] = None, file_size: Optional[str] = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    updates = ["status = ?", "updated_at = ?"]
    params = [status, time.time()]

    if duration > 0:
        updates.append("duration = ?")
        params.append(duration)
    if error:
        updates.append("error = ?")
        params.append(error)
    if file_size:
        updates.append("file_size = ?")
        params.append(file_size)

    params.append(job_id)

    sql = f"UPDATE api_jobs SET {', '.join(updates)} WHERE job_id = ?"
    cursor.execute(sql, tuple(params))
    conn.commit()
    conn.close()


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM api_jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return dict(row)
    return None


def list_jobs(limit: int = 50) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM api_jobs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# --- Files ---


def create_upload(upload_id: str, filename: str, size_bytes: int, checksum: Optional[str] = None, status: str = "COMPLETED"):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO api_uploads (upload_id, filename, size_bytes, checksum, uploaded_at, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (upload_id, filename, size_bytes, checksum, time.time(), status))
    conn.commit()
    conn.close()


def update_upload(upload_id: str, status: str, size_bytes: Optional[int] = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    updates = ["status = ?"]
    params: List[Any] = [status]

    if size_bytes is not None:
        updates.append("size_bytes = ?")
        params.append(size_bytes)

    params.append(upload_id)

    sql = f"UPDATE api_uploads SET {', '.join(updates)} WHERE upload_id = ?"
    cursor.execute(sql, tuple(params))
    conn.commit()
    conn.close()


def create_download(filename: str, client_ip: str = "unknown"):
    download_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO api_downloads (download_id, filename, requested_at, client_ip)
        VALUES (?, ?, ?, ?)
    ''', (download_id, filename, time.time(), client_ip))
    conn.commit()
    conn.close()
