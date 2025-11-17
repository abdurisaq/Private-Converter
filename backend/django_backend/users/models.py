
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
import uuid


class User(AbstractUser):
    """Extended User model with storage quota"""
    ROLE_CHOICES = [
        ('user', 'Regular User'),
        ('admin', 'Administrator'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=True)
    storage_quota = models.BigIntegerField(
        default=10737418240,  # 10GB
        validators=[MinValueValidator(0)]
    )  # in bytes
    storage_used = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Override M2M field related_name to avoid clash with django.contrib.auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='core_user_set',
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='core_user_set',
        blank=True,
    )
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.email} ({self.role})"

