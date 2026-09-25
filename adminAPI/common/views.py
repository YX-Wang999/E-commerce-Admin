"""Common API views."""

import logging
import time

from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.image_validators import validate_image_file
from common.media_utils import to_relative_media_url
from common.response import error_response, success_response
from common.upload import generate_upload_filename

logger = logging.getLogger(__name__)


class ImageUploadView(APIView):
    """Upload product image to local media storage."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request: Request) -> Response:
        """Handle multipart image upload."""
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return error_response('请选择要上传的图片')

        try:
            validate_image_file(uploaded_file)
        except Exception as exc:
            return error_response(str(exc))

        scope = str(request.data.get('scope', 'products')).strip().lower()
        if scope not in {'products', 'brands', 'complaints', 'reviews'}:
            scope = 'products'
        subdir = timezone.now().strftime(f'{scope}/%Y/%m')
        filename = generate_upload_filename(uploaded_file.name)
        relative_path = default_storage.save(f'{subdir}/{filename}', uploaded_file)
        media_url = settings.MEDIA_URL
        if not media_url.endswith('/'):
            media_url = f'{media_url}/'
        url = to_relative_media_url(f'{media_url}{relative_path}', int(time.time()))
        return success_response(data={'url': url}, message='上传成功')
