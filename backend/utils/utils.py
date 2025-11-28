from utils.models import AuditLog


def log_audit(user=None, action='', resource_type='', resource_id='', details=None, ip_address='', user_agent=''):
    """Log an audit event"""
    AuditLog.objects.create(
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else ''
    )


def get_supported_formats():
    """Return all supported conversion formats"""
    return {
        'audio': {
            'input': ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'opus'],
            'output': ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'opus']
        },
        'video': {
            'input': ['mp4', 'mkv', 'avi', 'mov', 'flv', 'wmv', 'webm', 'ts', 'mts'],
            'output': ['mp4', 'mkv', 'avi', 'webm', 'mov']
        },
        'image': {
            'input': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'ico', 'svg'],
            'output': ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff']
        },
        'document': {
            'input': ['pdf', 'docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt', 'odt', 'ods', 'odp', 'rtf', 'txt', 'md'],
            'output': ['pdf', 'docx', 'xlsx', 'pptx', 'odt', 'ods', 'odp', 'txt', 'md']
        },
        'ebook': {
            'input': ['epub', 'mobi', 'azw', 'azw3', 'pdf', 'txt'],
            'output': ['epub', 'mobi', 'azw3', 'pdf']
        },
        'archive': {
            'input': ['zip', '7z', 'rar', 'tar', 'gz', 'tar.gz', 'bz2', 'tar.bz2', 'xz', 'tar.xz'],
            'output': ['zip', '7z', 'tar', 'tar.gz', 'tar.bz2', 'tar.xz']
        },
        'pdf': {
            'input': ['pdf'],
            'output': ['pdf']
        },
        'ocr': {
            'input': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'pdf'],
            'output': ['pdf', 'txt']
        }
    }
