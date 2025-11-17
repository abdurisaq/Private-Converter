from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.conf import settings
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from .models import User
import os
from django.http import FileResponse
# Create your views here.


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    """Register new user"""
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        # First user becomes admin
        if User.objects.count() == 1:
            user.role = 'admin'
            user.save()
        
        refresh = RefreshToken.for_user(user)
        
        
        return Response({
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    """Login user"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        
        try:

            user_obj = User.objects.get(email=email)
            user = authenticate(username=user_obj.username, password=password)
           
            if user and user.is_active:
                refresh = RefreshToken.for_user(user)
                
                return Response({
                    'user': UserSerializer(user).data,
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }, status=status.HTTP_200_OK)
            else:
                raise User.DoesNotExist
        except User.DoesNotExist:
            pass
        
        return Response(
            {'detail': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
