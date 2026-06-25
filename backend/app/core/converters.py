"""File conversion utilities for various file types."""
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Callable
from app.core.config import settings

try:
    from PIL import Image
except ImportError:
    Image = None

logger = logging.getLogger(__name__)


def get_converter(input_format: str, output_format: str) -> Optional[Callable]:
    """Select appropriate converter based on format pair."""
    input_format = input_format.lower()
    output_format = output_format.lower()
    logger.info(f"Getting converter for: {input_format} -> {output_format}")
    
    # Audio formats
    if input_format in ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'opus']:
        logger.info(f"Selected audio converter for {input_format}")
        return convert_audio
    
    # Video formats
    if input_format in ['mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'webm', 'ts', 'mts']:
        logger.info(f"Selected video converter for {input_format}")
        return convert_video
    
    # Image formats
    if input_format in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'tif', 'ico', 'svg']:
        logger.info(f"Selected image converter for {input_format}")
        return convert_image
    
    # Document formats
    if input_format in ['pdf', 'docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'odt', 'ods', 'odp', 'rtf', 'txt', 'md']:
        logger.info(f"Selected document converter for {input_format}")
        return convert_document
    
    # Ebook formats
    if input_format in ['epub', 'mobi', 'azw', 'azw3']:
        logger.info(f"Selected ebook converter for {input_format}")
        return convert_ebook
    
    # Archive formats
    if input_format in ['zip', '7z', 'rar', 'tar', 'gz', 'bz2', 'xz']:
        logger.info(f"Selected archive converter for {input_format}")
        return convert_archive
    
    # OCR (image to text/pdf)
    if output_format in ['pdf', 'txt'] and input_format in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'tif']:
        logger.info(f"Selected OCR converter for {input_format} -> {output_format}")
        return convert_ocr
    
    logger.warning(f"No converter found for {input_format} -> {output_format}")
    return None


def convert_audio(input_file: str, output_file: str) -> bool:
    """Convert audio files using FFmpeg."""
    try:
        logger.info(f"Starting audio conversion: {input_file} -> {output_file}")
        output_format = Path(output_file).suffix[1:].lower()
        codec = 'libmp3lame' if output_format == 'mp3' else 'pcm_s16le'
        
        cmd = [
            'ffmpeg',
            '-i', input_file,
            '-acodec', codec,
            '-ab', '192k',
            '-ar', '44100',
            output_file,
            '-y'  # Overwrite
        ]
        logger.info(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, timeout=settings.PROCESS_TIMEOUT)
        output_exists = os.path.exists(output_file)
        logger.info(f"Audio conversion completed: {output_exists}")
        return output_exists
    except subprocess.CalledProcessError as e:
        logger.error(f"Audio conversion error: Command failed with exit code {e.returncode}")
        logger.error(f"stderr: {e.stderr.decode() if e.stderr else 'No stderr'}")
        return False
    except Exception as e:
        logger.error(f"Audio conversion error: {str(e)}")
        return False


def convert_video(input_file: str, output_file: str) -> bool:
    """Convert video files using FFmpeg."""
    try:
        logger.info(f"Starting video conversion: {input_file} -> {output_file}")
        output_format = Path(output_file).suffix[1:].lower()
        
        # Build command based on output format
        cmd = ['ffmpeg', '-i', input_file]
        
        # Only use encoding if format requires it, otherwise copy streams
        if output_format in ['mp4', 'mkv']:
            cmd.extend(['-c:v', 'libx264', '-preset', 'fast', '-c:a', 'aac'])
        elif output_format in ['webm']:
            cmd.extend(['-c:v', 'libvpx', '-b:v', '1M', '-c:a', 'libopus'])
        else:
            # For unknown formats, try to copy streams
            cmd.extend(['-c:v', 'copy', '-c:a', 'copy'])
        
        cmd.extend([output_file, '-y'])
        
        logger.info(f"Executing command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, timeout=settings.PROCESS_TIMEOUT)
        output_exists = os.path.exists(output_file)
        logger.info(f"Video conversion completed: {output_exists}")
        return output_exists
    except subprocess.CalledProcessError as e:
        logger.error(f"Video conversion error: Command failed with exit code {e.returncode}")
        logger.error(f"stderr: {e.stderr.decode() if e.stderr else 'No stderr'}")
        return False
    except Exception as e:
        logger.error(f"Video conversion error: {str(e)}")
        return False


def convert_image(input_file: str, output_file: str) -> bool:
    output_format = Path(output_file).suffix[1:].lower()
    if Image is not None:
        try:
            with Image.open(input_file) as img:
                if img.mode in ('RGBA', 'P') and output_format in ['jpg', 'jpeg']:
                    img = img.convert('RGB')
                elif img.mode == 'P':
                    img = img.convert('RGBA')
                save_kwargs = {}
                if output_format in ['jpg', 'jpeg']:
                    save_kwargs['quality'] = 85
                img.save(output_file, **save_kwargs)
            return os.path.exists(output_file)
        except Exception as e:
            logger.error(f"Image conversion error via Pillow: {str(e)}")
            if output_format in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'webp']:
                pass
            else:
                return False
    try:
        cmd = [
            'magick' if os.name == 'nt' else 'convert',
            input_file,
            '-quality', '85',
            output_file
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=settings.PROCESS_TIMEOUT)
        return os.path.exists(output_file)
    except subprocess.CalledProcessError as e:
        logger.error(f"Image conversion error: Command failed with exit code {e.returncode}")
        logger.error(f"stderr: {e.stderr.decode() if e.stderr else 'No stderr'}")
        return False
    except Exception as e:
        logger.error(f"Image conversion error: {str(e)}")
        return False


def convert_document(input_file: str, output_file: str) -> bool:
    """Convert document files using Pandoc."""
    try:
        output_format = Path(output_file).suffix[1:].lower()
        
        cmd = [
            'pandoc',
            input_file,
            '-o', output_file,
            f'--to={output_format}'
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=settings.PROCESS_TIMEOUT)
        return os.path.exists(output_file)
    except Exception as e:
        logger.error(f"Document conversion error: {str(e)}")
        return False


def convert_ebook(input_file: str, output_file: str) -> bool:
    """Convert ebook files using Calibre."""
    try:
        cmd = [
            'ebook-convert',
            input_file,
            output_file
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=settings.PROCESS_TIMEOUT)
        return os.path.exists(output_file)
    except Exception as e:
        logger.error(f"Ebook conversion error: {str(e)}")
        return False


def convert_archive(input_file: str, output_file: str) -> bool:
    """Convert archive files."""
    try:
        output_format = Path(output_file).suffix[1:].lower()
        
        if output_format == 'zip':
            cmd = ['zip', '-r', output_file, input_file]
        elif output_format == '7z':
            cmd = ['7z', 'a', output_file, input_file]
        elif output_format == 'tar':
            cmd = ['tar', '-cf', output_file, input_file]
        elif output_format in ['gz', 'tar.gz']:
            cmd = ['tar', '-czf', output_file, input_file]
        else:
            return False
        
        subprocess.run(cmd, check=True, capture_output=True, timeout=settings.PROCESS_TIMEOUT)
        return os.path.exists(output_file)
    except Exception as e:
        logger.error(f"Archive conversion error: {str(e)}")
        return False


def convert_ocr(input_file: str, output_file: str) -> bool:
    """OCR conversion using Tesseract."""
    try:
        output_format = Path(output_file).suffix[1:].lower()
        output_base = str(Path(output_file).with_suffix(''))
        
        cmd = [
            'tesseract',
            input_file,
            output_base,
            'pdf' if output_format == 'pdf' else 'txt'
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=settings.PROCESS_TIMEOUT)
        return os.path.exists(output_file)
    except Exception as e:
        logger.error(f"OCR conversion error: {str(e)}")
        return False
