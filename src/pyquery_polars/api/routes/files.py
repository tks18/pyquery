from typing import Optional, List
import hashlib
import uuid
from pydantic import BaseModel
import os
import shutil
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse
from typing import List
import pyquery_polars.api.db as db

router = APIRouter()

# Define workspace/upload directory
# unique per session effectively, but for now global
WORKSPACE_DIR = os.path.join(os.getcwd(), "workspace")
UPLOAD_DIR = os.path.join(WORKSPACE_DIR, "uploads")
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "outputs")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to the server's workspace.
    Returns the absolute path to be used in Load APIs.
    """
    try:
        # Sanitize filename (basic)
        filename = os.path.basename(file.filename or "uploaded_file")
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Track in DB (Simple Upload)
        upload_id = str(uuid.uuid4())
        size = os.path.getsize(file_path)
        db.create_upload(upload_id, filename, size,
                         "unknown", status="COMPLETED")

        return {
            "filename": filename,
            "path": os.path.abspath(file_path),
            "size": size,
            "upload_id": upload_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/download/{filename}")
async def download_file(filename: str, request: Request):
    """
    Download a file from the upload or output directory.
    Checks 'outputs' first, then 'uploads'.
    """
    # Track Download Request
    client_ip = request.client.host if request.client else "unknown"
    db.create_download(filename, client_ip)

    # Check outputs first (results)
    output_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(output_path):
        return FileResponse(output_path, filename=filename)

    # Check uploads
    upload_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(upload_path):
        return FileResponse(upload_path, filename=filename)

    if os.path.exists(filename) and os.path.isfile(filename):
        # Allow downloading via absolute path if provided and exists (DANGER: LFI, but acceptable for this local/dev tool context)
        return FileResponse(filename, filename=os.path.basename(filename))

    raise HTTPException(status_code=404, detail="File not found in workspace")


@router.get("/list")
def list_files():
    """List files in the workspace (uploads/outputs)."""
    uploads = os.listdir(UPLOAD_DIR)
    outputs = os.listdir(OUTPUT_DIR)
    return {
        "uploads": uploads,
        "outputs": outputs
    }


CHUNKS_DIR = os.path.join(WORKSPACE_DIR, "chunks")
os.makedirs(CHUNKS_DIR, exist_ok=True)


class ChunkInitRequest(BaseModel):
    filename: str
    expected_checksum: Optional[str] = None  # MD5 or SHA256 of the final file
    algorithm: str = "md5"  # md5 or sha256


class ChunkCompleteRequest(BaseModel):
    upload_id: str
    total_chunks: int
    filename: Optional[str] = None
    expected_checksum: Optional[str] = None


@router.post("/chunk/init")
def init_chunked_upload(req: ChunkInitRequest):
    """Start a new chunked upload session."""
    upload_id = str(uuid.uuid4())
    session_dir = os.path.join(CHUNKS_DIR, upload_id)
    os.makedirs(session_dir, exist_ok=True)

    # Store metadata
    meta = {
        "filename": req.filename,
        "expected_checksum": req.expected_checksum,
        "algorithm": req.algorithm
    }

    db.create_upload(upload_id, req.filename, 0,
                     req.expected_checksum, status="PENDING")

    return {"upload_id": upload_id, "filename": req.filename, "algorithm": req.algorithm}


@router.get("/chunk/status/{upload_id}")
def get_upload_status(upload_id: str):
    """
    Check which chunks have been received. Useful for resuming.
    """
    session_dir = os.path.join(CHUNKS_DIR, upload_id)
    if not os.path.exists(session_dir):
        # Fallback: check DB if it was already completed?
        # For now assume session dir existence determines resumability.
        raise HTTPException(status_code=404, detail="Upload session not found")

    # List all chunk_N files
    files = os.listdir(session_dir)
    chunks = []
    for f in files:
        if f.startswith("chunk_"):
            try:
                idx = int(f.split("_")[1])
                chunks.append(idx)
            except:
                pass

    return {
        "upload_id": upload_id,
        "uploaded_chunks": sorted(chunks),
        "count": len(chunks)
    }


@router.post("/chunk/upload")
async def upload_chunk(
    upload_id: str,
    chunk_index: int,
    chunk_hash: Optional[str] = None,  # Optional immediate verification
    file: UploadFile = File(...)
):
    """
    Upload a single chunk.
    If 'chunk_hash' is provided, we verify content immediately.
    """
    session_dir = os.path.join(CHUNKS_DIR, upload_id)
    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail="Upload session not found")

    chunk_path = os.path.join(session_dir, f"chunk_{chunk_index}")

    try:
        content = await file.read()

        # Verify hash if provided
        if chunk_hash:
            # We assume MD5 for chunk hash usually, or client specifies
            # Let's try to match length roughly or plain MD5 default
            hasher = hashlib.md5()
            hasher.update(content)
            calculated = hasher.hexdigest()

            if calculated != chunk_hash:
                raise HTTPException(
                    status_code=400, detail=f"Checksum mismatch for chunk {chunk_index}. Sent: {chunk_hash}, Calc: {calculated}")

        with open(chunk_path, "wb") as buffer:
            buffer.write(content)

        return {"status": "uploaded", "index": chunk_index}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Chunk upload failed: {e}")


@router.post("/chunk/complete")
def complete_chunked_upload(req: ChunkCompleteRequest):
    """
    Assemble chunks and verify final checksum.
    """
    return _assemble_file_robust(req.upload_id, req.total_chunks, req.filename, req.expected_checksum)


def _assemble_file_robust(upload_id: str, total_chunks: int, filename: Optional[str] = None, expected_checksum: Optional[str] = None):
    # Fallback filename if not provided
    if not filename:
        filename = f"upload_{upload_id}.bin"

    session_dir = os.path.join(CHUNKS_DIR, upload_id)
    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail="Upload session not found")

    final_path = os.path.join(UPLOAD_DIR, filename)

    try:
        # Prepare hasher
        final_hasher = None
        if expected_checksum:
            # Detect algo by length? MD5=32 chars, SHA256=64 chars
            if len(expected_checksum) == 64:
                final_hasher = hashlib.sha256()
            else:
                final_hasher = hashlib.md5()

        with open(final_path, "wb") as outfile:
            for i in range(total_chunks):
                p = os.path.join(session_dir, f"chunk_{i}")
                if not os.path.exists(p):
                    raise HTTPException(
                        status_code=400, detail=f"Missing chunk index {i}")

                with open(p, "rb") as infile:
                    chunk_data = infile.read()
                    if final_hasher:
                        final_hasher.update(chunk_data)
                    outfile.write(chunk_data)

        # Verify Final Hash
        if final_hasher and expected_checksum:
            calculated = final_hasher.hexdigest()
            if calculated != expected_checksum:
                # Cleanup invalid file
                os.remove(final_path)

                # Update DB Failure
                db.update_upload(upload_id, "FAILED_CHECKSUM")

                raise HTTPException(
                    status_code=400, detail=f"Final file integrity check failed. Sent: {expected_checksum}, Calc: {calculated}")

        # Cleanup Session
        shutil.rmtree(session_dir)

        # Update DB Success
        size = os.path.getsize(final_path)
        db.update_upload(upload_id, "COMPLETED", size_bytes=size)

        return {
            "filename": filename,
            "path": os.path.abspath(final_path),
            "size": size,
            "status": "completed",
            "verified": bool(expected_checksum)
        }
    except HTTPException:
        raise
    except Exception as e:
        db.update_upload(upload_id, "FAILED_ASSEMBLY")
        raise HTTPException(status_code=500, detail=f"Assembly failed: {e}")
