from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from app.core.job_manager import manager as job_manager
import asyncio
from pathlib import Path
import uuid

from app.api.deps import get_db, CurrentUser, SessionDep
from app.models import Job, User
from app.schemas.job import JobCreate, JobRead, JobUpdate
from app.core.config import settings

router = APIRouter()


def _get_job(session: Session, job_id: str) -> Job | None:
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        return None
    return session.get(Job, job_uuid)


@router.post("/", response_model=JobRead)
def create_job(
    job_in: JobCreate,
    session: SessionDep,
    current_user: CurrentUser
):
    """Create a new conversion job."""
    job = Job(**job_in.dict(), user_id=current_user.id)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job
    

@router.get("/")
def list_jobs(
    session: SessionDep,
    current_user: CurrentUser,
    status: Optional[str] = None,
):
    """List jobs for the current user or all jobs for admins."""
    statement = select(Job)
    if not current_user.is_superuser:
        statement = statement.where(Job.user_id == current_user.id)
    if status:
        statement = statement.where(Job.status == status)
    jobs = session.exec(statement).all()
    return {"results": jobs}


@router.get("/{job_id}", response_model=JobRead)
def get_job(
    job_id: str,
    session: SessionDep,
    current_user: CurrentUser
):
    """Get a specific job."""
    job = _get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    return job


@router.post("/{job_id}/start", response_model=JobRead)
async def start_job(
    job_id: str,
    session: SessionDep,
    current_user: CurrentUser
):
    """Start processing a conversion job."""
    job = _get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    if job.status != "pending":
        raise HTTPException(status_code=400, detail=f"Cannot start job in {job.status} status")
    
    job.status = "processing"
    session.add(job)
    session.commit()
    session.refresh(job)
    
    # schedule job via shared manager
    job_manager.enqueue(job_id)
    return job


@router.get("/{job_id}/download/")
def download_job_result(
    job_id: str,
    session: SessionDep,
    current_user: CurrentUser
):
    """Download the converted file result."""
    job = _get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    if job.status != 'completed':
        raise HTTPException(status_code=400, detail='Job not completed')
    
    from fastapi.responses import FileResponse
    result_path = Path(settings.RESULTS_DIR) / str(job_id) / job.output_filename
    if not result_path.exists():
        raise HTTPException(status_code=404, detail='Result file not found')
    return FileResponse(str(result_path), filename=job.output_filename)


@router.post("/{job_id}/cancel")
def cancel_job(
    job_id: str,
    session: SessionDep,
    current_user: CurrentUser
):
    """Cancel a conversion job."""
    job = _get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    if job.status in ['completed', 'failed', 'cancelled']:
        raise HTTPException(status_code=400, detail=f'Cannot cancel job in {job.status} status')
    job.status = 'cancelled'
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@router.patch("/{job_id}", response_model=JobRead)
def update_job(
    job_id: str,
    job_update: JobUpdate,
    session: SessionDep,
    current_user: CurrentUser
):
    """Update a job's details."""
    job = _get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    for k, v in job_update.dict(exclude_none=True).items():
        setattr(job, k, v)
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@router.delete("/{job_id}")
def delete_job(
    job_id: str,
    session: SessionDep,
    current_user: CurrentUser
):
    """Delete a job and its associated files."""
    job = _get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Clean up files
    import shutil
    job_upload_dir = Path(settings.UPLOAD_DIR) / str(current_user.id) / str(job_id)
    if job_upload_dir.exists():
        shutil.rmtree(job_upload_dir)
    
    job_result_dir = Path(settings.RESULTS_DIR) / str(job_id)
    if job_result_dir.exists():
        shutil.rmtree(job_result_dir)
    
    # Delete from database
    session.delete(job)
    session.commit()
    
    return {"status": "deleted"}
