import os
import subprocess
import logging
from celery import shared_task
from django.conf import settings
from django.utils import timezone
from ..models import Job
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task
def process_conversion(job_id):
    """Main task to process file conversion"""
    try:
        job = Job.objects.get(id=job_id)
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save()
        
        logger.info(f"Starting conversion job {job_id}: {job.input_format} -> {job.output_format}")
        
        # Get input file path
        input_dir = os.path.join(settings.UPLOAD_DIR, str(job.id))
        input_file = os.path.join(input_dir, job.input_filename)
        
        # Create output directory
        output_dir = os.path.join(settings.RESULTS_DIR, str(job.id))
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, job.output_filename)
        
        # Select appropriate converter
        converter = get_converter(job.input_format, job.output_format)
        if not converter:
            raise ValueError(f"No converter found for {job.input_format} -> {job.output_format}")
        
        # Execute conversion
        success = converter(input_file, output_file, job)
        
        if success:
            job.status = 'completed'
            job.progress = 100
            job.completed_at = timezone.now()
            
            # Update user storage used
            output_size = os.path.getsize(output_file)
            job.user.storage_used += output_size
            job.user.save()
            
            logger.info(f"Conversion completed: {job_id}")
        else:
            job.status = 'failed'
            job.error_message = 'Conversion failed'
            logger.error(f"Conversion failed: {job_id}")
        
        job.save()
        
    except Job.DoesNotExist:
        logger.error(f"Job not found: {job_id}")
    except Exception as e:
        logger.error(f"Conversion error for {job_id}: {str(e)}")
        try:
            job = Job.objects.get(id=job_id)
            job.status = 'failed'
            job.error_message = str(e)
            job.save()
        except:
            pass


def get_converter(input_format, output_format):
    """Select appropriate converter based on format pair"""
    input_format = input_format.lower()
    output_format = output_format.lower()
    
    # Audio
    if input_format in ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'opus']:
        return convert_audio
    
    # Video
    if input_format in ['mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'webm', 'ts', 'mts']:
        return convert_video
    
    # Image
    if input_format in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'ico', 'svg']:
        return convert_image
    
    # Document
    if input_format in ['pdf', 'docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'odt', 'ods', 'odp', 'rtf', 'txt', 'md']:
        return convert_document
    
    # Ebook
    if input_format in ['epub', 'mobi', 'azw', 'azw3']:
        return convert_ebook
    
    # Archive
    if input_format in ['zip', '7z', 'rar', 'tar', 'gz', 'bz2', 'xz']:
        return convert_archive
    
    # OCR
    if output_format in ['pdf', 'txt'] and input_format in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']:
        return convert_ocr
    
    return None


def convert_audio(input_file, output_file, job):
    """Convert audio files using FFmpeg"""
    try:
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-acodec', 'libmp3lame' if job.output_format == 'mp3' else 'pcm_s16le',
            '-ab', '192k',
            '-ar', '44100',
            output_file,
            '-y'  # Overwrite
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=settings.PROCESS_TIMEOUT)
        job.tool_used = 'ffmpeg'
        return os.path.exists(output_file)
    except Exception as e:
        logger.error(f"Audio conversion error: {str(e)}")
        return False


def convert_video(input_file, output_file, job):
    """Convert video files using FFmpeg"""
    try:
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-c:v', 'libx264' if job.output_format in ['mp4', 'mkv'] else 'copy',
            '-preset', 'fast',
            '-c:a', 'aac',
            output_file,
            '-y'
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=settings.PROCESS_TIMEOUT)
        job.tool_used = 'ffmpeg'
        return os.path.exists(output_file)
    except Exception as e:
        logger.error(f"Video conversion error: {str(e)}")
        return False


def convert_image(input_file, output_file, job):
    """Convert image files using ImageMagick"""
    try:
        cmd = [
            'convert',
            input_file,
            '-quality', '85',
            output_file
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=settings.PROCESS_TIMEOUT)
        job.tool_used = 'imagemagick'
        return os.path.exists(output_file)
    except Exception as e:
        logger.error(f"Image conversion error: {str(e)}")
        return False


def convert_document(input_file, output_file, job):
    """Convert document files using Pandoc"""
    try:
        cmd = [
            'pandoc',
            input_file,
            '-o', output_file,
            f'--to={job.output_format}'
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=settings.PROCESS_TIMEOUT)
        job.tool_used = 'pandoc'
        return os.path.exists(output_file)
    except Exception as e:
        logger.error(f"Document conversion error: {str(e)}")
        return False


def convert_ebook(input_file, output_file, job):
    """Convert ebook files using Calibre"""
    try:
        cmd = [
            'ebook-convert',
            input_file,
            output_file
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=settings.PROCESS_TIMEOUT)
        job.tool_used = 'calibre'
        return os.path.exists(output_file)
    except Exception as e:
        logger.error(f"Ebook conversion error: {str(e)}")
        return False


def convert_archive(input_file, output_file, job):
    """Convert archive files"""
    try:
        if job.output_format == 'zip':
            cmd = ['zip', '-r', output_file, input_file]
        elif job.output_format == '7z':
            cmd = ['7z', 'a', output_file, input_file]
        elif job.output_format == 'tar':
            cmd = ['tar', '-cf', output_file, input_file]
        elif job.output_format == 'tar.gz':
            cmd = ['tar', '-czf', output_file, input_file]
        else:
            return False
        
        subprocess.run(cmd, check=True, capture_output=True, timeout=settings.PROCESS_TIMEOUT)
        job.tool_used = 'archive-tools'
        return os.path.exists(output_file)
    except Exception as e:
        logger.error(f"Archive conversion error: {str(e)}")
        return False


def convert_ocr(input_file, output_file, job):
    """OCR conversion using Tesseract"""
    try:
        cmd = [
            'tesseract',
            input_file,
            output_file.replace(f'.{job.output_format}', ''),
            f'pdf' if job.output_format == 'pdf' else 'txt'
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=settings.PROCESS_TIMEOUT)
        job.tool_used = 'tesseract'
        return os.path.exists(output_file)
    except Exception as e:
        logger.error(f"OCR conversion error: {str(e)}")
        return False


@shared_task
def cleanup_old_jobs():
    """Clean up old job files"""
    try:
        # Delete jobs older than 30 days
        cutoff_date = timezone.now() - timedelta(days=30)
        old_jobs = Job.objects.filter(created_at__lt=cutoff_date, status__in=['completed', 'failed', 'cancelled'])
        
        for job in old_jobs:
            # Delete upload files
            upload_dir = os.path.join(settings.UPLOAD_DIR, str(job.id))
            if os.path.exists(upload_dir):
                import shutil
                shutil.rmtree(upload_dir)
            
            # Delete result files
            result_dir = os.path.join(settings.RESULTS_DIR, str(job.id))
            if os.path.exists(result_dir):
                import shutil
                shutil.rmtree(result_dir)
        
        old_jobs.delete()
        logger.info(f"Cleaned up {old_jobs.count()} old jobs")
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
