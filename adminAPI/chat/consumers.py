"""WebSocket chat consumer."""

import logging

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from chat.models import Conversation
from chat.services import (
    can_access_conversation,
    create_chat_message,
    has_online_chat_staff,
    is_conversation_staff,
    mark_conversation_read,
    serialize_message,
    touch_staff_presence,
)

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    conversation_id: int | None = None
    group_name: str | None = None

    async def connect(self):
        user = self.scope.get('user')
        customer = self.scope.get('customer')
        if (isinstance(user, AnonymousUser) or not user.is_authenticated) and not customer:
            await self.close(code=4401)
            return

        self.conversation_id = int(self.scope['url_route']['kwargs']['conversation_id'])
        conversation = await self._get_conversation(self.conversation_id)
        if conversation is None:
            await self.close(code=4404)
            return

        if not await self._can_access(user, customer, conversation):
            await self.close(code=4403)
            return

        self.group_name = f'chat_{self.conversation_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        if user and user.is_authenticated and await self._is_conversation_staff(user, conversation):
            await self._touch_presence(user, online=True)

        await self._mark_read(
            conversation,
            reader_is_staff=user.is_authenticated and await self._is_conversation_staff(user, conversation),
        )

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
        user = self.scope.get('user')
        if user and user.is_authenticated and self.conversation_id:
            conversation = await self._get_conversation(self.conversation_id)
            if conversation and await self._is_conversation_staff(user, conversation):
                await self._touch_presence(user, online=False)

    async def receive_json(self, content, **kwargs):
        message_type = content.get('type')
        if message_type == 'message':
            await self._handle_message(content)
        elif message_type == 'typing':
            await self._handle_typing(content)
        elif message_type == 'read':
            await self._handle_read()

    async def _handle_message(self, content):
        user = self.scope.get('user')
        customer = self.scope.get('customer')
        text = (content.get('content') or '').strip()
        if not text:
            await self.send_json({'type': 'error', 'message': '消息内容不能为空'})
            return

        conversation = await self._get_conversation(self.conversation_id)
        if conversation is None:
            return

        staff = user.is_authenticated and await self._is_conversation_staff(user, conversation)
        if staff and not await self._staff_can_reply(user, conversation):
            await self.send_json({'type': 'error', 'message': '无回复权限'})
            return

        try:
            message = await self._create_message(
                conversation,
                text,
                is_staff=staff,
                staff_user=user if staff else None,
                customer=customer if not staff else None,
            )
        except ValueError as exc:
            await self.send_json({'type': 'error', 'message': str(exc)})
            return

        payload = {
            'type': 'message',
            'data': serialize_message(message),
        }
        await self.channel_layer.group_send(
            self.group_name,
            {'type': 'chat.message', 'payload': payload},
        )

        if not staff and not await self._has_online_staff():
            await self.send_json({
                'type': 'staff_offline',
                'message': '客服暂不在线，我们将在 30 分钟内回复',
            })

    async def _handle_typing(self, content):
        user = self.scope.get('user')
        customer = self.scope.get('customer')
        conversation = await self._get_conversation(self.conversation_id)
        if conversation is None:
            return
        staff = user.is_authenticated and await self._is_conversation_staff(user, conversation)
        if staff:
            sender_name = user.nickname or user.username
            sender_id = user.id
        else:
            sender_name = customer.display_name if customer else '用户'
            sender_id = customer.id if customer else 0
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat.typing',
                'payload': {
                    'type': 'typing',
                    'data': {
                        'sender_id': sender_id,
                        'sender_name': sender_name,
                        'is_staff': staff,
                        'typing': bool(content.get('typing', True)),
                    },
                },
            },
        )

    async def _handle_read(self):
        conversation = await self._get_conversation(self.conversation_id)
        if conversation is None:
            return
        user = self.scope.get('user')
        staff = user.is_authenticated and await self._is_conversation_staff(user, conversation)
        await self._mark_read(conversation, reader_is_staff=staff)

    async def chat_message(self, event):
        await self.send_json(event['payload'])

    async def chat_typing(self, event):
        current_id = self.scope.get('customer').id if self.scope.get('customer') else self.scope['user'].id
        if event['payload']['data']['sender_id'] != current_id:
            await self.send_json(event['payload'])

    @database_sync_to_async
    def _get_conversation(self, conversation_id: int):
        try:
            return Conversation.objects.get(pk=conversation_id)
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def _can_access(self, user, customer, conversation) -> bool:
        return can_access_conversation(
            user=user if user and user.is_authenticated else None,
            customer=customer,
            conversation=conversation,
        )

    @database_sync_to_async
    def _is_conversation_staff(self, user, conversation) -> bool:
        return is_conversation_staff(user, conversation)

    @database_sync_to_async
    def _staff_can_reply(self, user, conversation) -> bool:
        from chat.permissions import is_admin_user
        from tenants.seller_permissions import is_tenant_staff_member

        if is_tenant_staff_member(user, conversation.tenant):
            return True
        if not is_admin_user(user):
            return False
        if getattr(user, 'is_superuser', False):
            return True
        return user.roles.filter(is_active=True, permissions__code='chat:reply').exists()

    @database_sync_to_async
    def _create_message(self, conversation, text, *, is_staff, staff_user=None, customer=None):
        return create_chat_message(
            conversation,
            text,
            is_staff=is_staff,
            staff_user=staff_user,
            customer=customer,
        )

    @database_sync_to_async
    def _mark_read(self, conversation, *, reader_is_staff: bool):
        mark_conversation_read(conversation, reader_is_staff=reader_is_staff)

    @database_sync_to_async
    def _touch_presence(self, user, *, online: bool):
        touch_staff_presence(user, online=online)

    @database_sync_to_async
    def _has_online_staff(self) -> bool:
        return has_online_chat_staff()
