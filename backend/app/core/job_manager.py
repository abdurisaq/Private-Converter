import asyncio
import os
import shutil
import logging
import uuid
from typing import Optional
from datetime import datetime
from sqlmodel import Session, select
from app.core.db import engine
from app.models import Job
from app.core.config import settings
from app.core.converters import get_converter

logger = logging.getLogger(__name__)


class JobManager:
    def __init__(self, concurrency: Optional[int] = None):
        self.concurrency = concurrency or settings.MAX_CONCURRENT_PROCESSES
        self.queue: asyncio.Queue[str] = None  # Will be initialized on startup
        self.workers: list[asyncio.Task] = []
        self._running = False

    async def _worker(self, worker_id: int):
        logger.info(f"Worker {worker_id} started")
        while self._running:
            try:
                job_id = await self.queue.get()
                logger.info(f"Worker {worker_id} processing job {job_id}")
                try:
                    await self._process(job_id)
                except Exception as e:
                    logger.error(f"Worker {worker_id} error processing {job_id}: {str(e)}", exc_info=True)
                    # For now, we just mark as failed and continue
                    try:
                        with Session(engine) as session:
                            job_uuid = uuid.UUID(job_id) if isinstance(job_id, str) else job_id
                            job = session.get(Job, job_uuid)
                            if job:
                                job.status = "failed"
                                job.error_message = str(e)
                                session.add(job)
                                session.commit()
                    except Exception as db_error:
                        logger.error(f"Failed to update job status: {str(db_error)}")
                finally:
                    self.queue.task_done()
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break

    async def _process(self, job_id: str):
        """Process a file conversion job."""
        try:
            # Convert job_id to UUID
            job_uuid = uuid.UUID(job_id) if isinstance(job_id, str) else job_id
            
            logger.info(f"Processing job {job_id}")
            # Update job status to processing
            with Session(engine) as s:
                job = s.get(Job, job_uuid)
                if not job:
                    logger.error(f"Job {job_id} not found in database")
                    return
                logger.info(f"Job {job_id} details: input_format={job.input_format}, output_format={job.output_format}, input_file={job.input_filename}")
                job.status = "processing"
                job.started_at = datetime.utcnow()
                s.add(job)
                s.commit()
                s.refresh(job)

            # Get file paths
            upload_dir = os.path.join(str(settings.UPLOAD_DIR), str(job_id))
            result_dir = os.path.join(str(settings.RESULTS_DIR), str(job_id))
            os.makedirs(result_dir, exist_ok=True)
            
            input_path = os.path.join(upload_dir, job.input_filename)
            output_path = os.path.join(result_dir, job.output_filename)
            
            logger.info(f"Job {job_id} paths: input={input_path}, output={output_path}")

            # Verify input file exists
            if not os.path.exists(input_path):
                raise FileNotFoundError(f"Input file not found: {input_path}")
            
            logger.info(f"Job {job_id} input file exists, size: {os.path.getsize(input_path)} bytes")

            # Get appropriate converter
            converter = get_converter(job.input_format, job.output_format)
            if not converter:
                raise ValueError(f"No converter available for {job.input_format} -> {job.output_format}")
            
            logger.info(f"Job {job_id} using converter: {converter.__name__}")

            # Execute conversion
            logger.info(f"Job {job_id} starting conversion")
            success = converter(input_path, output_path)
            logger.info(f"Job {job_id} conversion result: {success}")

            # Update job status
            with Session(engine) as s:
                job = s.get(Job, job_uuid)
                if not job:
                    logger.error(f"Job {job_id} disappeared during processing")
                    return
                
                # Check if job was cancelled during processing
                if job.status == "cancelled":
                    logger.info(f"Job {job_id} was cancelled during processing")
                    return

                if success and os.path.exists(output_path):
                    job.status = "completed"
                    job.progress = 100
                    job.completed_at = datetime.utcnow()
                    job.tool_used = converter.__name__.replace("convert_", "")
                    logger.info(f"Job {job_id} marked as completed")
                else:
                    job.status = "failed"
                    job.error_message = "Conversion failed: output file not created"
                    logger.error(f"Job {job_id} conversion failed: output file does not exist at {output_path}")
                
                s.add(job)
                s.commit()
                s.refresh(job)

        except Exception as e:
            logger.error(f"Job {job_id} processing error: {str(e)}", exc_info=True)
            # Mark job as failed
            try:
                job_uuid = uuid.UUID(job_id) if isinstance(job_id, str) else job_id
                with Session(engine) as s:
                    job = s.get(Job, job_uuid)
                    if job:
                        job.status = "failed"
                        job.error_message = str(e)
                        job.completed_at = datetime.utcnow()
                        s.add(job)
                        s.commit()
            except Exception as db_error:
                logger.error(f"Failed to mark job {job_id} as failed: {str(db_error)}")

    async def start(self):
        if self._running:
            return
        self._running = True
        self.queue = asyncio.Queue()  # Initialize queue in async context
        for i in range(self.concurrency):
            task = asyncio.create_task(self._worker(i))
            self.workers.append(task)

    async def stop(self):
        self._running = False
        # wait for queue to drain
        await self.queue.join()
        for w in self.workers:
            w.cancel()

    def enqueue(self, job_id: str):
        """Enqueue a job for processing (can be called from sync context)."""
        if self.queue is None:
            logger.error(f"Job manager not started, cannot enqueue job {job_id}")
            raise RuntimeError("Job manager not started")
        logger.info(f"Enqueueing job {job_id}")
        self.queue.put_nowait(job_id)


# module level manager instance
manager = JobManager()
