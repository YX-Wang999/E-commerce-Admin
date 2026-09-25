"""WebSocket consumer for global notifications (customer + seller + admin)."""

from urllib.parse import unquote

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from chat.permissions import is_chat_staff
from tenants.models import Tenant
from tenants.seller_permissions import is_tenant_staff_member


class NotifyConsumer(AsyncJsonWebsocketConsumer):
    """Push real-time events: notifications, orders, chat, cart updates."""

    groups: list[str] = []

    async def connect(self):
        user = self.scope.get('user')
        customer = self.scope.get('customer')
        self.groups = []

        if customer is not None:
            group = f'customer_notify_{customer.id}'
            await self.channel_layer.group_add(group, self.channel_name)
            self.groups.append(group)
            await self.accept()
            await self.send_json({'type': 'connected', 'groups': self.groups})
            return

        if isinstance(user, AnonymousUser) or not user.is_authenticated:
            await self.close(code=4401)
            return

        tenant = await self._resolve_tenant(user)
        if tenant and await self._is_tenant_member(user, tenant):
            group = f'seller_notify_{tenant.id}'
            await self.channel_layer.group_add(group, self.channel_name)
            self.groups.append(group)

        if await self._is_admin_notifier(user):
            await self.channel_layer.group_add('admin_notify', self.channel_name)
            self.groups.append('admin_notify')
            staff_group = f'staff_notify_{user.id}'
            await self.channel_layer.group_add(staff_group, self.channel_name)
            self.groups.append(staff_group)

        if not self.groups:
            await self.close(code=4403)
            return

        await self.accept()
        await self.send_json({'type': 'connected', 'groups': self.groups})

    async def disconnect(self, close_code):
        for group in self.groups:
            await self.channel_layer.group_discard(group, self.channel_name)

    async def notify_event(self, event):
        await self.send_json(event.get('payload') or {})

    @database_sync_to_async
    def _resolve_tenant(self, user):
        query = self.scope.get('query_string', b'').decode()
        params = {}
        for part in query.split('&'):
            if '=' in part:
                key, value = part.split('=', 1)
                params[key] = value
        tenant_code = unquote((params.get('tenant_code') or '').strip())
        if tenant_code:
            return Tenant.objects.filter(code__iexact=tenant_code).first()
        staff = user.tenant_staffs.filter(is_active=True).select_related('tenant').first()
        return staff.tenant if staff else None

    @database_sync_to_async
    def _is_tenant_member(self, user, tenant) -> bool:
        return is_tenant_staff_member(user, tenant)

    @database_sync_to_async
    def _is_admin_notifier(self, user) -> bool:
        if getattr(user, 'is_superuser', False):
            return True
        if is_chat_staff(user):
            return True
        order_roles = {
            'warehouse_manager',
            'ops_manager',
            'ops_director',
            'ops_staff',
            'super_admin',
        }
        if user.roles.filter(is_active=True, code__in=order_roles).exists():
            return True
        return user.roles.filter(
            is_active=True,
            permissions__code__in=[
                'tenant:appeal',
                'tenant:change:view',
                'tenant:view',
                'order:read',
                'order:ship',
            ],
        ).exists()
