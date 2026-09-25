"""Department views."""

import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.department_serializers import DepartmentListSerializer, DepartmentWriteSerializer
from accounts.models import Department
from accounts.utils import build_department_tree
from common.permissions import IsSuperAdminRole
from common.response import error_response, success_response

logger = logging.getLogger(__name__)


class DepartmentViewSet(viewsets.ModelViewSet):
    """Department CRUD — super admin only."""

    queryset = Department.objects.select_related('parent', 'manager').all()
    permission_classes = [IsAuthenticated, IsSuperAdminRole]

    def get_serializer_class(self):
        """Return serializer by action."""
        if self.action in ('create', 'update', 'partial_update'):
            return DepartmentWriteSerializer
        return DepartmentListSerializer

    def list(self, request: Request, *args, **kwargs) -> Response:
        """Return department tree."""
        queryset = self.filter_queryset(self.get_queryset()).order_by('id')
        flat_items = []
        for item in queryset:
            data = DepartmentListSerializer(item).data
            data['parent'] = item.parent_id
            flat_items.append(data)
        tree = build_department_tree(flat_items)
        return success_response(data=tree)

    def retrieve(self, request: Request, *args, **kwargs) -> Response:
        """Retrieve a department."""
        serializer = self.get_serializer(self.get_object())
        return success_response(data=serializer.data)

    def create(self, request: Request, *args, **kwargs) -> Response:
        """Create a department."""
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Create department failed')
            return error_response('创建部门失败', code=50000, http_status=500)
        return success_response(
            data=DepartmentListSerializer(instance).data,
            message='创建成功',
            http_status=status.HTTP_201_CREATED,
        )

    def update(self, request: Request, *args, **kwargs) -> Response:
        """Update a department."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            message = next(iter(serializer.errors.values()))[0]
            return error_response(str(message))
        try:
            instance = serializer.save()
        except Exception:
            logger.exception('Update department failed')
            return error_response('更新部门失败', code=50000, http_status=500)
        return success_response(data=DepartmentListSerializer(instance).data, message='更新成功')

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        """Delete a department."""
        instance = self.get_object()
        if instance.children.exists():
            return error_response('存在下级部门，无法删除')
        if instance.members.exists():
            return error_response('部门下仍有成员，无法删除')
        try:
            instance.delete()
        except Exception:
            logger.exception('Delete department failed')
            return error_response('删除部门失败', code=50000, http_status=500)
        return success_response(message='删除成功')

    @action(
        detail=False,
        methods=['get'],
        url_path='flat',
        permission_classes=[IsAuthenticated],
    )
    def flat_list(self, request: Request) -> Response:
        """Flat active department list for form selects."""
        queryset = Department.objects.filter(is_active=True).order_by('id')
        serializer = DepartmentListSerializer(queryset, many=True)
        return success_response(data=serializer.data)
