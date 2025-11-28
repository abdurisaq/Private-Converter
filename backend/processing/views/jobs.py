from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate
from django.conf import settings
from ..models import  Job
from ..serializers import JobSerializer
from utils.utils import log_audit
import os
from django.http import FileResponse
from utils.views import get_client_ip

class JobViewSet(viewsets.ReadOnlyModelViewSet):
    """Job management endpoints"""
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status']
    ordering_fields = ['-created_at']
    
    def get_queryset(self):
        """Users see only their jobs, admins see all"""
        if self.request.user.role == 'admin':
            return Job.objects.all()
        return Job.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download conversion result"""
        job = self.get_object()
        
        if job.status != 'completed':
            return Response(
                {'detail': 'Job not completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result_file = os.path.join(settings.RESULTS_DIR, str(job.id), job.output_filename)
        if not os.path.exists(result_file):
            return Response(
                {'detail': 'Result file not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        log_audit(
            user=request.user,
            action='download',
            resource_type='job',
            resource_id=str(job.id),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Use FileResponse instead of DRF Response
        return FileResponse(open(result_file, 'rb'), as_attachment=True, filename=job.output_filename)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel conversion job"""
        job = self.get_object()
        
        if job.status in ['completed', 'failed', 'cancelled']:
            return Response(
                {'detail': f'Cannot cancel job in {job.status} status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.status = 'cancelled'
        job.save()
        
        log_audit(
            user=request.user,
            action='admin_action',
            resource_type='job',
            resource_id=str(job.id),
            details={'action': 'cancel'},
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response(JobSerializer(job).data)