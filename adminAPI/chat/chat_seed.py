"""Chat permissions seed data."""

CHAT_PERMISSIONS: list[tuple[str, str, str, str]] = [
    ('在线客服查看', 'chat:read', '在线客服', 'read'),
    ('在线客服回复', 'chat:reply', '在线客服', 'reply'),
    ('在线客服分配', 'chat:assign', '在线客服', 'assign'),
    ('在线客服关闭', 'chat:close', '在线客服', 'close'),
]
