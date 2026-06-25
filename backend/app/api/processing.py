from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Body, status
from sqlmodel import Session
from typing import List, Optional
from pydantic import BaseModel, validator
from app.api.deps import SessionDep, CurrentUser
from app.core.config import settings
from app.core.utils import get_supported_formats
from app.models import Job
from app.core.job_manager import manager as job_manager
import os
import uuid


def _get_job(session: Session, job_id: str) -> Job | None:
    try:
        return session.get(Job, uuid.UUID(job_id))
    except ValueError:
        return None


router = APIRouter()


class PdfCrop(BaseModel):
    x: float
    y: float
    width: float
    height: float


class PdfTransformation(BaseModel):
    rotate: int = 0
    crop: Optional[PdfCrop] = None

    @validator("rotate")
    def validate_rotate(cls, value):
        if value not in [0, 90, 180, 270]:
            raise ValueError("Rotation must be 0, 90, 180, or 270 degrees.")
        return value


class PdfPageRecipe(BaseModel):
    sourceFileId: str
    sourcePageIndex: int
    transformations: PdfTransformation


class PdfMergeRecipe(BaseModel):
    jobId: str
    outputFilename: str
    pages: List[PdfPageRecipe]


class ProcessOperationPayload(BaseModel):
    input: str
    output: Optional[str] = None
    type: str
    outputFormat: Optional[str] = None

@router.post('/pdf/merge', status_code=status.HTTP_200_OK)
async def merge_pdf(
    current_user: CurrentUser,
    session: Session = Depends(SessionDep),
    recipe: PdfMergeRecipe = Body(...),
):
    """Create a new PDF merge job from a recipe."""
    print(f"Received merge request from user {current_user.id}")
    print(f"Output filename: {recipe.outputFilename}")
    print(f"Number of pages to merge: {len(recipe.pages)}")
    
    # Create a NEW job for the merge operation
    job = Job(
        input_filename="merge_operation",  # Generic name since merging multiple files
        output_filename=recipe.outputFilename,
        input_format="pdf",
        output_format="pdf",
        user_id=current_user.id,
        status='pending',
        progress=0
    )
    
    # Store the merge recipe as JSON in the job (optional - for processing later)
    job.metadata = {
        "type": "merge",
        "recipe": recipe.dict(),
        "source_files": list(set(p.sourceFileId for p in recipe.pages))
    }
    
    session.add(job)
    session.commit()
    session.refresh(job)
    
    # Enqueue for background processing
    job_manager.enqueue(str(job.id))
    
    return {
        'jobId': str(job.id),
        'status': 'QUEUED',
        'message': 'PDF merge job started successfully.'
    }


@router.post('/upload')
def upload_file(
    current_user: CurrentUser,
    session: Session = Depends(SessionDep),
    file: UploadFile = File(...),
):
    # store into TEMP_DIR
    if not file:
        raise HTTPException(status_code=400, detail='No file')
    file_id = str(uuid.uuid4())
    target = settings.TEMP_DIR / file_id
    os.makedirs(target, exist_ok=True)
    path = target / file.filename
    with path.open('wb') as buffer:
        for chunk in iter(lambda: file.file.read(1024*64), b''):
            buffer.write(chunk)
    return {'fileId': file_id, 'filename': file.filename}


@router.get('/operations')
def get_operations(type: str):
    # return operations per type
    formats = get_supported_formats()
    type = type.lower()
    if type not in formats:
        return []
    if type == 'pdf':
        return ['merge', 'split', 'compress']
    if type == 'image':
        return ['resize', 'compress', 'convert']
    return ['convert']


@router.post('/{operation}')
def process_operation(
    operation: str,
    current_user: CurrentUser,
    session: Session = Depends(SessionDep),
    payload: ProcessOperationPayload = Body(...),
):
    # create a job that will be processed by the job manager
    input_filename = payload.input
    output_filename = payload.output if payload.output else f"{input_filename.rsplit('.',1)[0]}_{operation}.out"
    
    job = Job(
        input_filename=input_filename, 
        output_filename=output_filename, 
        input_format=payload.type,
        output_format=payload.outputFormat if payload.outputFormat else '', 
        user_id=current_user.id
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    job_manager.enqueue(str(job.id))
    return {'data': {'jobId': str(job.id)}}


@router.get('/jobs/{job_id}')
def processing_job_status(
    job_id: str, 
    current_user: CurrentUser, 
    session: Session = Depends(SessionDep)
):
    job = _get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    return job


@router.get('/jobs/{job_id}/download')
def processing_job_download(
    job_id: str, 
    current_user: CurrentUser, 
    session: Session = Depends(SessionDep)
):
    from fastapi.responses import FileResponse
    from pathlib import Path
    
    job = _get_job(session, job_id)
    if not job:
        raise HTTPException(status_code=404, detail='Job not found')
    if job.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail='Not authorized')
    
    result_path = Path(settings.RESULTS_DIR) / str(job_id) / job.output_filename
    if not result_path.exists():
        raise HTTPException(status_code=404, detail='Result not found')
    
    return FileResponse(str(result_path), filename=result_path.name)