"""Image upload validation helpers."""

import logging
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


def validate_image_file(uploaded_file) -> None:
    """Validate uploaded image extension and size."""
    if not uploaded_file:
        raise ValidationError('请选择要上传的图片')

    ext = Path(uploaded_file.name).suffix.lower().lstrip('.')
    allowed = getattr(settings, 'ALLOWED_IMAGE_EXTENSIONS', {'jpg', 'jpeg', 'png', 'gif', 'webp'})
    if ext not in allowed:
        raise ValidationError(f'仅支持 {", ".join(sorted(allowed))} 格式')

    max_size = getattr(settings, 'MAX_UPLOAD_IMAGE_SIZE', 2 * 1024 * 1024)
    if uploaded_file.size > max_size:
        raise ValidationError('图片大小不能超过 2MB')

    try:
        from PIL import Image

        image = Image.open(uploaded_file)
        image.verify()
        uploaded_file.seek(0)
    except Exception:
        logger.warning('Invalid image content: %s', uploaded_file.name)
        raise ValidationError('图片文件无效或已损坏') from None
