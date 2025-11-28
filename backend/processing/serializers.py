from rest_framework import serializers
from .models import Job
from django.contrib.auth.password_validation import validate_password

class JobSerializer(serializers.ModelSerializer):
    """Job model serializer"""
    user_email = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = [
            'id', 'user', 'user_email', 'input_filename', 'output_filename',
            'input_format', 'output_format', 'status', 'progress', 'file_size',
            'error_message', 'tool_used', 'created_at', 'started_at', 'completed_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'started_at', 'completed_at']
    
    def get_user_email(self, obj):
        return obj.user.email

class ConversionFormatsSerializer(serializers.Serializer):
    """Serializer for supported conversion formats"""
    audio = serializers.DictField()
    video = serializers.DictField()
    image = serializers.DictField()
    document = serializers.DictField()
    ebook = serializers.DictField()
    archive = serializers.DictField()
    pdf = serializers.DictField()
    ocr = serializers.DictField()
