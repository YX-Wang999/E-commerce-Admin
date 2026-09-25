"""Notification API views."""

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardPagination
from common.response import error_response, success_response
from customers.permissions import IsCustomerAuthenticated
from notification.models import Notification
from notification.serializers import NotificationSerializer
from tenants.seller_permissions import IsTenantStaffMember


class _NotificationMixin:
    recipient_type: str = ''

    def _recipient_id(self, request: Request) -> int | None:
        raise NotImplementedError

    def _queryset(self, request: Request):
        recipient_id = self._recipient_id(request)
        if not recipient_id:
            return Notification.objects.none()
        return Notification.objects.filter(
            recipient_type=self.recipient_type,
            recipient_id=recipient_id,
        )


class StaffNotificationListView(_NotificationMixin, APIView):
    permission_classes = [IsAuthenticated]
    recipient_type = Notification.RECIPIENT_STAFF

    def _recipient_id(self, request: Request) -> int | None:
        return request.user.id if request.user.is_authenticated else None

    def get(self, request: Request) -> Response:
        queryset = self._queryset(request)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class StaffNotificationUnreadCountView(_NotificationMixin, APIView):
    permission_classes = [IsAuthenticated]
    recipient_type = Notification.RECIPIENT_STAFF

    def _recipient_id(self, request: Request) -> int | None:
        return request.user.id if request.user.is_authenticated else None

    def get(self, request: Request) -> Response:
        count = self._queryset(request).filter(is_read=False).count()
        return success_response(data={'count': count})


class StaffNotificationReadView(_NotificationMixin, APIView):
    permission_classes = [IsAuthenticated]
    recipient_type = Notification.RECIPIENT_STAFF

    def _recipient_id(self, request: Request) -> int | None:
        return request.user.id if request.user.is_authenticated else None

    def post(self, request: Request, pk: int) -> Response:
        notification = self._queryset(request).filter(pk=pk).first()
        if notification is None:
            return error_response('通知不存在', http_status=404)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])
        return success_response(data=NotificationSerializer(notification).data)


class StaffNotificationReadAllView(_NotificationMixin, APIView):
    permission_classes = [IsAuthenticated]
    recipient_type = Notification.RECIPIENT_STAFF

    def _recipient_id(self, request: Request) -> int | None:
        return request.user.id if request.user.is_authenticated else None

    def post(self, request: Request) -> Response:
        now = timezone.now()
        updated = self._queryset(request).filter(is_read=False).update(is_read=True, read_at=now)
        return success_response(data={'updated': updated}, message='已全部标记为已读')


class SellerNotificationListView(_NotificationMixin, APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]
    recipient_type = Notification.RECIPIENT_TENANT

    def _recipient_id(self, request: Request) -> int | None:
        tenant = getattr(request, 'tenant', None)
        return tenant.id if tenant else None

    def get(self, request: Request) -> Response:
        queryset = self._queryset(request)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class SellerNotificationUnreadCountView(_NotificationMixin, APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]
    recipient_type = Notification.RECIPIENT_TENANT

    def _recipient_id(self, request: Request) -> int | None:
        tenant = getattr(request, 'tenant', None)
        return tenant.id if tenant else None

    def get(self, request: Request) -> Response:
        count = self._queryset(request).filter(is_read=False).count()
        return success_response(data={'count': count})


class SellerNotificationReadView(_NotificationMixin, APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]
    recipient_type = Notification.RECIPIENT_TENANT

    def _recipient_id(self, request: Request) -> int | None:
        tenant = getattr(request, 'tenant', None)
        return tenant.id if tenant else None

    def post(self, request: Request, pk: int) -> Response:
        notification = self._queryset(request).filter(pk=pk).first()
        if notification is None:
            return error_response('通知不存在', http_status=404)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])
        return success_response(data=NotificationSerializer(notification).data)


class SellerNotificationReadAllView(_NotificationMixin, APIView):
    permission_classes = [IsAuthenticated, IsTenantStaffMember]
    recipient_type = Notification.RECIPIENT_TENANT

    def _recipient_id(self, request: Request) -> int | None:
        tenant = getattr(request, 'tenant', None)
        return tenant.id if tenant else None

    def post(self, request: Request) -> Response:
        now = timezone.now()
        updated = self._queryset(request).filter(is_read=False).update(is_read=True, read_at=now)
        return success_response(data={'updated': updated}, message='已全部标记为已读')


class CustomerNotificationListView(_NotificationMixin, APIView):
    permission_classes = [IsCustomerAuthenticated]
    recipient_type = Notification.RECIPIENT_CUSTOMER

    def _recipient_id(self, request: Request) -> int | None:
        customer = getattr(request, 'customer', None)
        return customer.id if customer else None

    def get(self, request: Request) -> Response:
        queryset = self._queryset(request)
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = NotificationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class CustomerNotificationUnreadCountView(_NotificationMixin, APIView):
    permission_classes = [IsCustomerAuthenticated]
    recipient_type = Notification.RECIPIENT_CUSTOMER

    def _recipient_id(self, request: Request) -> int | None:
        customer = getattr(request, 'customer', None)
        return customer.id if customer else None

    def get(self, request: Request) -> Response:
        count = self._queryset(request).filter(is_read=False).count()
        return success_response(data={'count': count})


class CustomerNotificationReadView(_NotificationMixin, APIView):
    permission_classes = [IsCustomerAuthenticated]
    recipient_type = Notification.RECIPIENT_CUSTOMER

    def _recipient_id(self, request: Request) -> int | None:
        customer = getattr(request, 'customer', None)
        return customer.id if customer else None

    def post(self, request: Request, pk: int) -> Response:
        notification = self._queryset(request).filter(pk=pk).first()
        if notification is None:
            return error_response('通知不存在', http_status=404)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=['is_read', 'read_at'])
        return success_response(data=NotificationSerializer(notification).data)


class CustomerNotificationReadAllView(_NotificationMixin, APIView):
    permission_classes = [IsCustomerAuthenticated]
    recipient_type = Notification.RECIPIENT_CUSTOMER

    def _recipient_id(self, request: Request) -> int | None:
        customer = getattr(request, 'customer', None)
        return customer.id if customer else None

    def post(self, request: Request) -> Response:
        now = timezone.now()
        updated = self._queryset(request).filter(is_read=False).update(is_read=True, read_at=now)
        return success_response(data={'updated': updated}, message='已全部标记为已读')
