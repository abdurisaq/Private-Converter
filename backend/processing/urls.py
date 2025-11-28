from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.jobs import JobViewSet
from .views.uploads import ConversionUploadViewSet, get_formats

router = DefaultRouter()
router.register(r'conversions', ConversionUploadViewSet, basename='conversion')
router.register(r'jobs', JobViewSet, basename='job')
urlpatterns = [
    path('', include(router.urls)),
    path('conversions/formats/', get_formats, name='get-formats'),
]
