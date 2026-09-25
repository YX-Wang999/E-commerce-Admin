"""Common URL routes."""

from django.urls import path

from common.views import ImageUploadView

urlpatterns = [
    path('image/', ImageUploadView.as_view(), name='upload-image'),
]
