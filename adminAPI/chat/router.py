"""Conversation routing for multi-party customer service."""

from __future__ import annotations

from typing import Any


class ChatRouter:
    """Route conversations by initiator and context."""

    TYPE_B2C = 'b2c'
    TYPE_C2P = 'c2p'
    TYPE_B2P = 'b2p'
    TYPE_P2B = 'p2b'
    TYPE_C2P_B = 'c2p_b'

    CUSTOMER_TYPES = {TYPE_B2C, TYPE_C2P, TYPE_C2P_B}
    TENANT_TYPES = {TYPE_B2C, TYPE_B2P, TYPE_P2B, TYPE_C2P_B}
    PLATFORM_TYPES = {TYPE_C2P, TYPE_B2P, TYPE_P2B, TYPE_C2P_B}

    def route_customer(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        tenant_id = context.get('tenant_id')
        if context.get('is_complaint') or context.get('type') == 'complaint':
            if not tenant_id:
                raise ValueError('投诉必须指定商户')
            # 投诉先由商户处理，会话仅商户可见；用户申请平台介入后再走仲裁流程
            return {'conversation_type': self.TYPE_B2C, 'tenant_id': tenant_id}
        if context.get('transfer_platform') or context.get('type') == 'c2p':
            return {'conversation_type': self.TYPE_C2P, 'tenant_id': None}
        if tenant_id:
            return {'conversation_type': self.TYPE_B2C, 'tenant_id': tenant_id}
        return {'conversation_type': self.TYPE_C2P, 'tenant_id': None}

    def route_tenant_staff(self, tenant_id: int, context: dict[str, Any] | None = None) -> dict[str, Any]:
        _ = context
        return {'conversation_type': self.TYPE_B2P, 'tenant_id': tenant_id}

    def route_platform_staff(self, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        tenant_id = context.get('tenant_id')
        if tenant_id:
            return {'conversation_type': self.TYPE_P2B, 'tenant_id': tenant_id}
        return {'conversation_type': self.TYPE_C2P, 'tenant_id': None}


chat_router = ChatRouter()
