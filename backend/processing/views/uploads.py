from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from django.conf import settings
from processing.models import Job
from ..serializers import JobSerializer
from ..serializers import ConversionFormatsSerializer
from utils.views import get_client_ip
from utils.utils import get_supported_formats, log_audit
from ..tasks.converter import process_conversion
import os


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_formats(request):
    """Get supported conversion formats"""
    formats = get_supported_formats()
    serializer = ConversionFormatsSerializer(formats)
    return Response(serializer.data)


class ConversionUploadViewSet(viewsets.ViewSet):
    """Handle file uploads and conversion jobs"""
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request):
        """Upload file and create conversion job"""
        file = request.FILES.get('file')
        input_format = request.data.get('inputFormat', '').lower()
        output_format = request.data.get('outputFormat', '').lower()
        
        if not file or not input_format or not output_format:
            return Response(
                {'detail': 'Missing required fields'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check file size
        if file.size > settings.MAX_FILE_SIZE:
            return Response(
                {'detail': f'File too large. Max size: {settings.MAX_FILE_SIZE} bytes'},
                status=status.HTTP_413_PAYLOAD_TOO_LARGE
            )
        
        # Check user storage quota
        if request.user.storage_used + file.size > request.user.storage_quota:
            return Response(
                {'detail': 'Storage quota exceeded'},
                status=status.HTTP_413_PAYLOAD_TOO_LARGE
            )
        
        # Create job
        job = Job.objects.create(
            user=request.user,
            input_filename=file.name,
            output_filename=f"{file.name.rsplit('.', 1)[0]}.{output_format}",
            input_format=input_format,
            output_format=output_format,
            file_size=file.size,
        )
        
        # Save uploaded file
        upload_path = os.path.join(settings.UPLOAD_DIR, str(job.id))
        os.makedirs(upload_path, exist_ok=True)
        
        with open(os.path.join(upload_path, file.name), 'wb') as f:
            for chunk in file.chunks():
                f.write(chunk)
        
        # Queue conversion task
        process_conversion.delay(str(job.id))
        
        # Log audit
        log_audit(
            user=request.user,
            action='upload',
            resource_type='job',
            resource_id=str(job.id),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(
            JobSerializer(job).data,
            status=status.HTTP_201_CREATED
        )
