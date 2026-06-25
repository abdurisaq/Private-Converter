from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pathlib import Path
from fastapi.responses import FileResponse
import shutil
import uuid
from sqlmodel import Session
from app.core.config import settings
from app.schemas.file import UploadResponse
from app.api.deps import CurrentUser, get_db
from app.models import Job
import uuid

router = APIRouter()


def _get_job(session: Session, job_id: str) -> Job | None:
    try:
        return session.get(Job, uuid.UUID(job_id))
    except ValueError:
        return None



def _user_upload_dir(user_id: str) -> Path:
    """Get user's upload directory."""
    p = settings.UPLOAD_DIR / str(user_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _job_upload_dir(user_id: str, job_id: str) -> Path:
    """Get job-specific upload directory."""
    p = settings.UPLOAD_DIR / str(user_id) / str(job_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


@router.post("/", response_model=UploadResponse)
def upload_file(file: UploadFile = File(...), current_user=Depends(CurrentUser)):
    """Upload a file to user's upload directory."""
    # store uploads in a per-user directory and enforce MAX_FILE_SIZE
    user_dir = _user_upload_dir(str(current_user.id))
    out_path = user_dir / file.filename

    written = 0
    with out_path.open("wb") as buffer:
        for chunk in iter(lambda: file.file.read(1024 * 64), b""):
            written += len(chunk)
            if written > settings.MAX_FILE_SIZE:
                buffer.close()
                out_path.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail="File too large")
            buffer.write(chunk)

    return UploadResponse(filename=str(out_path.name), size=written)


@router.post("/{job_id}", response_model=UploadResponse)
def upload_file_for_job(
    job_id: str,
    file: UploadFile = File(...),
    current_user=Depends(CurrentUser),
    session: Session = Depends(get_db)
):
    """Upload a file for a specific conversion job."""
    # Verify job exists and belongs to user
    job = _get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Store file in job-specific directory
    job_dir = _job_upload_dir(str(current_user.id), str(job_id))
    out_path = job_dir / file.filename

    written = 0
    with out_path.open("wb") as buffer:
        for chunk in iter(lambda: file.file.read(1024 * 64), b""):
            written += len(chunk)
            if written > settings.MAX_FILE_SIZE:
                buffer.close()
                out_path.unlink(missing_ok=True)
                raise HTTPException(status_code=400, detail="File too large")
            buffer.write(chunk)

    return UploadResponse(filename=str(out_path.name), size=written)


@router.get("/", response_model=list[UploadResponse])
def list_user_files(current_user=Depends(CurrentUser)):
    """List all files in user's upload directory."""
    user_dir = _user_upload_dir(str(current_user.id))
    files = []
    if user_dir.exists():
        for p in user_dir.rglob("*"):
            if p.is_file():
                files.append(UploadResponse(filename=p.name, size=p.stat().st_size))
    return files


@router.get("/{filename}", response_model=UploadResponse)
def get_file_info(filename: str, current_user=Depends(CurrentUser)):
    """Get file info."""
    user_dir = _user_upload_dir(str(current_user.id))
    target = user_dir / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return UploadResponse(filename=target.name, size=target.stat().st_size)


@router.delete("/{filename}")
def delete_file(filename: str, current_user=Depends(CurrentUser)):
    """Delete a file from user's upload directory."""
    user_dir = _user_upload_dir(str(current_user.id))
    target = user_dir / filename
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")
    target.unlink()
    return {"status": "deleted"}
