"""Announcement views."""

import logging

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from announcement.models import Announcement
from announcement.permissions import (
    HasAnnouncementCreate,
    HasAnnouncementDelete,
    HasAnnouncementPublish,
    HasAnnouncementRead,
    HasAnnouncementUpdate,
)
from announcement.serializers import (
    AnnouncementPublicSerializer,
    AnnouncementSerializer,
    AnnouncementWriteSerializer,
)
from announcement.services import filter_banner_announcements, filter_visible_announcements, order_banner_announcements
from common.pagination import StandardPagination
from common.response import error_response, success_response

logger = logging.getLogger(__name__)


class AnnouncementViewSet(viewsets.ModelViewSet):
    """Admin announcement management."""

    queryset = Announcement.objects.prefetch_related('target_roles', 'target_departments').select_related(
        'publisher',
    ).all()
    pagination_class = StandardPagination
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        """Return serializer by action."""
        if self.action in ('create', 'update', 'partial_update'):
            return AnnouncementWriteSerializer
        return AnnouncementSerializer

    def get_permissions(self):
        """Permission by action."""
        if self.action in ('list', 'retrieve'):
            return [IsAuthenticated(), HasAnnouncementRead()]
        if self.action == 'create':
            return [IsAuthenticated(), HasAnnouncementCreate()]
        if self.action in ('update', 'partial_update'):
            return [IsAuthenticated(), HasAnnouncementUpdate()]
        if self.action == 'destroy':
            return [IsAuthenticated(), HasAnnouncementDelete()]
        if self.action in ('publish', 'offline'):
            return [IsAuthenticated(), HasAnnouncementPublish()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """Filter management list."""
        queryset = super().get_queryset()
        status_param = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        keyword = self.request.query_params.get('keyword')
        if status_param:
            queryset = queryset.filter(status=status_param)
        if priority:
            queryset = queryset.filter(priority=priority)
        if keyword:
            queryset = queryset.filter(title__icontains=keyword)
        return queryset

    def list(self, request: Request, *args, **kwargs) -> Response:
        """List announcements for management."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Retrieve announcement detail."""
        return success_response(data=self.get_serializer(self.get_object()).data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create announcement."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Create announcement failed')
            return error_response('创建失败', code=50000, http_status=500)
        if instance.status == Announcement.STATUS_PUBLISHED:
            try:
                from announcement.notify import notify_announcement_published

                notify_announcement_published(instance)
            except Exception:
                logger.exception('Announcement WS notify failed')
        return success_response(
            data=AnnouncementSerializer(instance).data,
            message='创建成功',
            http_status=status.HTTP_201_CREATED,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update announcement."""
        instance = self.get_object()
        if instance.status == Announcement.STATUS_PUBLISHED:
            return error_response('已发布公告请先下线后再编辑')
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Update announcement failed')
            return error_response('更新失败', code=50000, http_status=500)
        return success_response(data=AnnouncementSerializer(instance).data, message='更新成功')

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Delete announcement."""
        try:
            self.get_object().delete()
        except Exception:
            logger.exception('Delete announcement failed')
            return error_response('删除失败', code=50000, http_status=500)
        return success_response(message='删除成功')

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request: Request, pk: int | None = None) -> Response:
        """Publish announcement."""
        instance = self.get_object()
        if instance.status == Announcement.STATUS_PUBLISHED:
            return error_response('公告已发布')
        try:
            instance.status = Announcement.STATUS_PUBLISHED
            instance.publisher = request.user
            instance.published_at = timezone.now()
            instance.save(update_fields=['status', 'publisher', 'published_at'])
        except Exception:
            logger.exception('Publish announcement failed')
            return error_response('发布失败', code=50000, http_status=500)
        try:
            from announcement.notify import notify_announcement_published

            notify_announcement_published(instance)
        except Exception:
            logger.exception('Announcement WS notify failed')
        return success_response(
            data=AnnouncementSerializer(instance).data,
            message='发布成功',
        )

    @action(detail=True, methods=['post'], url_path='offline')
    def offline(self, request: Request, pk: int | None = None) -> Response:
        """Take announcement offline."""
        instance = self.get_object()
        if instance.status != Announcement.STATUS_PUBLISHED:
            return error_response('仅已发布公告可下线')
        try:
            instance.status = Announcement.STATUS_OFFLINE
            instance.save(update_fields=['status'])
        except Exception:
            logger.exception('Offline announcement failed')
            return error_response('下线失败', code=50000, http_status=500)
        return success_response(
            data=AnnouncementSerializer(instance).data,
            message='下线成功',
        )


class AnnouncementBannerView(APIView):
    """Top banner announcements (A 类公开接口，游客可访问)."""

    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:
        """Return urgent/important visible announcements."""
        user = request.user if getattr(request.user, 'is_authenticated', False) else None
        queryset = filter_banner_announcements(Announcement.objects.all(), user)
        queryset = order_banner_announcements(queryset)[:5]
        return success_response(data=AnnouncementPublicSerializer(queryset, many=True).data)


class AnnouncementLatestView(APIView):
    """Latest announcements for dashboard."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return latest visible announcements."""
        limit = int(request.query_params.get('limit', 5))
        queryset = filter_visible_announcements(Announcement.objects.all(), request.user)
        queryset = queryset.order_by('-is_pinned', '-published_at', '-id')[:limit]
        return success_response(data=AnnouncementPublicSerializer(queryset, many=True).data)


class AnnouncementVisibleView(APIView):
    """Paginated visible announcements for announcement center."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """Return paginated visible announcements."""
        queryset = filter_visible_announcements(Announcement.objects.all(), request.user)
        queryset = queryset.order_by('-is_pinned', '-published_at', '-id')
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AnnouncementPublicSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
