from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    """User model serializer"""
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role', 'is_active', 'storage_quota', 'storage_used', 'created_at']
        read_only_fields = ['id', 'storage_used', 'created_at']


class RegisterSerializer(serializers.ModelSerializer):
    """Minimal registration serializer with email and password"""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ['email', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError({'password': "Passwords don't match."})
        return data

    def create(self, validated_data):
        # auto-generate username from email
        validated_data['username'] = validated_data['email'].split('@')[0]
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Login serializer"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
