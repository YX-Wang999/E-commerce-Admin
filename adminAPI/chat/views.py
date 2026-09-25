"""Chat REST API views."""

import logging

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from chat.models import Conversation
from chat.permissions import HasChatRead, is_chat_staff
from chat.serializers import ConversationSerializer, MessageSerializer
from chat.services import (
    assign_conversation,
    can_access_conversation,
    close_conversation,
    create_chat_message,
    create_new_customer_conversation,
    filter_conversations_for_staff,
    get_or_create_customer_conversation,
    get_staff_unread_summary,
    get_workbench_stats,
    is_conversation_staff,
    is_tenant_staff,
    mark_conversation_read,
    mark_conversation_read_for_user,
    open_customer_conversation,
    open_platform_tenant_conversation,
    open_tenant_platform_conversation,
    notify_merchant_chat_started,
    serialize_message,
    touch_staff_presence,
)
from common.response import error_response, success_response
from customers.permissions import IsCustomerAuthenticated
from tenants.models import Tenant

logger = logging.getLogger(__name__)


def _parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, '', '0', 'false', 'False', 0):
        return False
    return bool(value)


class ConversationViewSet(viewsets.ViewSet):
    """Customer service conversation API with tenant isolation."""

    permission_classes = [IsAuthenticated]

    def _staff_queryset(self, request: Request):
        queryset = Conversation.objects.select_related('user', 'assigned_to', 'tenant').filter(
            status__in=[Conversation.STATUS_PENDING, Conversation.STATUS_ACTIVE],
        )
        tenant = getattr(request, 'tenant', None)
        if tenant is not None:
            if is_tenant_staff(request.user, tenant):
                return queryset.filter(tenant=tenant)
            if getattr(request.user, 'is_superuser', False):
                return queryset.filter(tenant=tenant)
            return queryset.none()
        return filter_conversations_for_staff(request.user, queryset)

    def get_conversation(self, request: Request, pk) -> Conversation | None:
        try:
            pk_int = int(pk)
        except (TypeError, ValueError):
            return None
        try:
            conversation = Conversation.objects.select_related(
                'user', 'assigned_to', 'tenant',
            ).get(pk=pk_int)
        except Conversation.DoesNotExist:
            return None
        customer = getattr(request, 'customer', None)
        if customer is not None:
            return conversation
        if is_chat_staff(request.user):
            scoped = self._staff_queryset(request).filter(pk=pk_int)
            if scoped.exists():
                return conversation
        elif getattr(request, 'tenant', None) and request.user.is_authenticated:
            from tenants.seller_permissions import is_tenant_staff_member
            if is_tenant_staff_member(request.user, request.tenant):
                if conversation.tenant_id == request.tenant.id:
                    return conversation
                scoped = self._staff_queryset(request).filter(pk=pk_int)
                if scoped.exists():
                    return conversation
        return None

    def list(self, request: Request) -> Response:
        customer = getattr(request, 'customer', None)
        if customer:
            queryset = Conversation.objects.select_related('user', 'assigned_to', 'tenant').filter(
                user=customer,
            )
        elif is_chat_staff(request.user):
            queryset = self._staff_queryset(request)
        elif getattr(request, 'tenant', None) and request.user.is_authenticated:
            from tenants.seller_permissions import is_tenant_staff_member
            if is_tenant_staff_member(request.user, request.tenant):
                queryset = Conversation.objects.select_related('user', 'assigned_to', 'tenant').filter(
                    tenant=request.tenant,
                    status__in=[Conversation.STATUS_PENDING, Conversation.STATUS_ACTIVE],
                ).filter(
                    conversation_type__in=[
                        Conversation.TYPE_B2C,
                        Conversation.TYPE_B2P,
                        Conversation.TYPE_P2B,
                    ],
                )
            else:
                return error_response('无权访问', http_status=403)
        else:
            return error_response('无权访问', http_status=403)
        serializer = ConversationSerializer(queryset, many=True, context={'request': request})
        return success_response(data=serializer.data)

    @action(detail=False, methods=['get', 'post'], url_path='mine', permission_classes=[IsCustomerAuthenticated])
    def mine(self, request: Request) -> Response:
        customer = request.customer
        context = {
            'tenant_id': request.data.get('tenant_id') or request.query_params.get('tenant_id'),
            'type': request.data.get('type') or request.query_params.get('type'),
            'transfer_platform': _parse_bool(
                request.data.get('transfer_platform', request.query_params.get('transfer_platform')),
            ),
            'is_complaint': _parse_bool(
                request.data.get('is_complaint', request.query_params.get('is_complaint')),
            ),
        }
        if context['tenant_id']:
            try:
                context['tenant_id'] = int(context['tenant_id'])
            except (TypeError, ValueError):
                return error_response('无效的商户 ID')
        if request.method == 'POST':
            conversation = create_new_customer_conversation(customer, context)
            message = '已创建新会话'
        else:
            conversation = get_or_create_customer_conversation(customer, context)
            message = 'success'
        conversation = Conversation.objects.select_related('user', 'assigned_to', 'tenant').get(
            pk=conversation.pk,
        )
        serializer = ConversationSerializer(conversation, context={'request': request})
        return success_response(data=serializer.data, message=message)

    @action(detail=False, methods=['post'], url_path='open', permission_classes=[IsAuthenticated])
    def open(self, request: Request) -> Response:
        tenant = getattr(request, 'tenant', None)
        tenant_id = request.data.get('tenant_id')
        from chat.permissions import is_chat_staff
        from tenants.seller_permissions import is_tenant_staff_member

        if tenant and is_tenant_staff_member(request.user, tenant):
            conversation = open_tenant_platform_conversation(tenant)
            message = '已连接平台客服'
            if (
                conversation.status == Conversation.STATUS_PENDING
                and not conversation.messages.exists()
            ):
                notify_merchant_chat_started(conversation)
        elif is_chat_staff(request.user) and tenant_id:
            target = Tenant.objects.filter(pk=tenant_id).first()
            if target is None:
                return error_response('商户不存在')
            conversation = open_platform_tenant_conversation(target)
            message = '已向商户发起会话'
        else:
            return error_response('无权发起该会话', http_status=403)

        conversation = Conversation.objects.select_related('user', 'assigned_to', 'tenant').get(pk=conversation.pk)
        return success_response(
            data=ConversationSerializer(conversation, context={'request': request}).data,
            message=message,
        )

    @action(detail=True, methods=['post'], url_path='transfer-platform', permission_classes=[IsCustomerAuthenticated])
    def transfer_platform(self, request: Request, pk: int | None = None) -> Response:
        conversation = self.get_conversation(request, pk)
        if conversation is None or conversation.user_id != request.customer.id:
            return error_response('会话不存在', http_status=404)
        new_conversation = open_customer_conversation(
            request.customer,
            {'transfer_platform': True},
        )
        new_conversation = Conversation.objects.select_related('user', 'assigned_to', 'tenant').get(
            pk=new_conversation.pk,
        )
        return success_response(
            data=ConversationSerializer(new_conversation, context={'request': request}).data,
            message='已转接平台客服',
        )

    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request: Request, pk: int | None = None) -> Response:
        conversation = self.get_conversation(request, pk)
        if conversation is None:
            return error_response('会话不存在', code=40404, http_status=404)
        customer = getattr(request, 'customer', None)
        if not can_access_conversation(
            user=request.user if request.user.is_authenticated else None,
            customer=customer,
            conversation=conversation,
        ):
            return error_response('无权访问该会话', code=40301, http_status=403)

        if request.method == 'POST':
            content = (request.data.get('content') or '').strip()
            if not content:
                return error_response('消息内容不能为空')
            staff = (
                request.user.is_authenticated
                and not customer
                and is_conversation_staff(request.user, conversation)
            )
            if customer and conversation.user_id != customer.id:
                return error_response('无权发送消息', code=40301, http_status=403)
            if not customer and not staff:
                return error_response('无权发送消息', code=40301, http_status=403)
            try:
                message = create_chat_message(
                    conversation,
                    content,
                    is_staff=staff,
                    staff_user=request.user if staff else None,
                    customer=customer if not staff else None,
                )
            except ValueError as exc:
                return error_response(str(exc))
            except Exception:
                logger.exception('Create chat message failed')
                return error_response('发送失败', code=50000, http_status=500)

            self._broadcast_chat_message(conversation.id, message)
            return success_response(
                data=MessageSerializer(message).data,
                message='发送成功',
                http_status=201,
            )

        if customer is not None:
            mark_conversation_read(conversation, reader_is_staff=False)
        elif request.user.is_authenticated:
            mark_conversation_read_for_user(conversation, request.user, request)
        else:
            mark_conversation_read(conversation, reader_is_staff=False)

        queryset = conversation.messages.select_related(
            'sender_staff', 'sender_user',
        ).order_by('created_at')
        serializer = MessageSerializer(queryset, many=True)
        return success_response(data=serializer.data)

    @staticmethod
    def _broadcast_chat_message(conversation_id: int, message) -> None:
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            if channel_layer is None:
                return
            payload = {
                'type': 'message',
                'data': serialize_message(message),
            }
            async_to_sync(channel_layer.group_send)(
                f'chat_{conversation_id}',
                {'type': 'chat.message', 'payload': payload},
            )
        except Exception:
            logger.exception('Broadcast chat message failed: conversation=%s', conversation_id)

    @action(
        detail=True,
        methods=['post'],
        url_path='assign',
        permission_classes=[IsAuthenticated],
    )
    def assign(self, request: Request, pk: int | None = None) -> Response:
        conversation = self.get_conversation(request, pk)
        if conversation is None:
            return error_response('会话不存在', code=40404, http_status=404)
        if conversation.status == Conversation.STATUS_CLOSED:
            return error_response('会话已关闭', code=40001)
        if not is_conversation_staff(request.user, conversation):
            return error_response('无权接入会话', code=40301, http_status=403)

        assign_conversation(conversation, request.user)
        conversation.refresh_from_db()
        serializer = ConversationSerializer(conversation, context={'request': request})
        return success_response(data=serializer.data, message='已接管会话')

    @action(detail=True, methods=['post'], url_path='close')
    def close(self, request: Request, pk: int | None = None) -> Response:
        conversation = self.get_conversation(request, pk)
        if conversation is None:
            return error_response('会话不存在', code=40404, http_status=404)
        if conversation.status == Conversation.STATUS_CLOSED:
            serializer = ConversationSerializer(conversation, context={'request': request})
            return success_response(data=serializer.data, message='会话已关闭')

        customer = getattr(request, 'customer', None)
        is_owner = customer is not None and conversation.user_id == customer.id
        if is_owner:
            close_conversation(conversation)
            conversation.refresh_from_db()
            serializer = ConversationSerializer(conversation, context={'request': request})
            return success_response(data=serializer.data, message='会话已关闭')

        user = request.user
        if is_conversation_staff(user, conversation):
            close_conversation(conversation)
            conversation.refresh_from_db()
            serializer = ConversationSerializer(conversation, context={'request': request})
            return success_response(data=serializer.data, message='会话已关闭')

        if not is_chat_staff(user):
            return error_response('无权关闭会话', code=40301, http_status=403)
        from feedback.permissions import user_has_permission

        if not (
            getattr(user, 'is_superuser', False)
            or user_has_permission(user, 'chat:close')
            or user_has_permission(user, 'chat:reply')
        ):
            return error_response('无关闭会话权限', code=40301, http_status=403)

        close_conversation(conversation)
        conversation.refresh_from_db()
        serializer = ConversationSerializer(conversation, context={'request': request})
        return success_response(data=serializer.data, message='会话已关闭')

    @action(detail=False, methods=['get'], url_path='stats', permission_classes=[IsAuthenticated, HasChatRead])
    def stats(self, request: Request) -> Response:
        tenant = getattr(request, 'tenant', None)
        return success_response(
            data=get_workbench_stats(user=request.user, tenant=tenant),
        )

    @action(detail=False, methods=['get'], url_path='unread-summary', permission_classes=[IsAuthenticated, HasChatRead])
    def unread_summary(self, request: Request) -> Response:
        tenant = getattr(request, 'tenant', None)
        return success_response(
            data=get_staff_unread_summary(user=request.user, tenant=tenant),
        )

    @action(detail=False, methods=['get'], url_path='staff-online', permission_classes=[IsCustomerAuthenticated])
    def staff_online(self, request: Request) -> Response:
        from chat.services import has_online_chat_staff

        return success_response(data={'online': has_online_chat_staff()})

    @action(detail=False, methods=['post'], url_path='presence', permission_classes=[IsAuthenticated, HasChatRead])
    def presence(self, request: Request) -> Response:
        online = bool(request.data.get('online', True))
        presence = touch_staff_presence(request.user, online=online)
        return success_response(
            data={
                'is_online': presence.is_online,
                'last_seen': presence.last_seen.isoformat(),
            },
        )
