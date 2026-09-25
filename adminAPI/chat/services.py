"""Chat business logic helpers."""

from django.contrib.auth import get_user_model
from django.db.models import Count, Q, QuerySet, Sum
from django.utils import timezone

from chat.models import Complaint, Conversation, Message, StaffPresence
from chat.router import chat_router
from customers.models import Customer
from tenants.models import Tenant

User = get_user_model()


def get_sender_display_name(message: Message) -> str:
    if message.sender_type == Message.SENDER_STAFF:
        sender = message.sender_staff
        return sender.nickname or sender.username if sender else '客服'
    if message.sender_user_id:
        customer = message.sender_user
        return customer.display_name if customer else '用户'
    return '用户'


def message_is_platform_staff(message: Message) -> bool:
    """Whether a staff message was sent by platform staff (vs merchant staff) in B2P."""
    if message.sender_type != Message.SENDER_STAFF or not message.sender_staff_id:
        return False
    conversation = message.conversation
    if not conversation.is_merchant_conversation:
        return True
    return _sender_is_platform_staff(message.sender_staff, conversation)


def serialize_message(message: Message) -> dict:
    is_platform_staff = message_is_platform_staff(message)
    return {
        'id': message.id,
        'conversation_id': message.conversation_id,
        'sender_id': message.sender_staff_id or message.sender_user_id,
        'sender_name': get_sender_display_name(message),
        'sender_type': message.sender_type,
        'is_staff': message.is_staff,
        'is_platform_staff': is_platform_staff,
        'content': message.content,
        'is_sensitive': message.is_sensitive,
        'created_at': message.created_at.isoformat(),
    }


def is_tenant_staff(user, tenant) -> bool:
    """Whether admin user belongs to the given tenant."""
    if not user or not user.is_authenticated or tenant is None:
        return False
    if getattr(user, 'is_superuser', False):
        return True
    return user.tenant_staffs.filter(tenant=tenant, is_active=True).exists()


def filter_conversations_for_staff(user, queryset: QuerySet | None = None) -> QuerySet:
    """Scope staff-visible conversations by role and conversation type."""
    if queryset is None:
        queryset = Conversation.all_objects.all()
    if not user or not user.is_authenticated:
        return queryset.none()
    if getattr(user, 'is_superuser', False):
        return queryset
    tenant_ids = list(
        user.tenant_staffs.filter(is_active=True).values_list('tenant_id', flat=True),
    )
    if tenant_ids:
        return queryset.filter(
            tenant_id__in=tenant_ids,
            conversation_type__in=[Conversation.TYPE_B2C, Conversation.TYPE_B2P, Conversation.TYPE_P2B],
        )
    from chat.permissions import is_chat_staff

    if is_chat_staff(user):
        return queryset.filter(
            Q(conversation_type__in=[Conversation.TYPE_C2P, Conversation.TYPE_B2P, Conversation.TYPE_P2B])
            | Q(conversation_type=Conversation.TYPE_B2C, tenant__isnull=True)
            | Q(conversation_type__isnull=True, tenant__isnull=True)
        )
    return queryset.none()


def can_access_conversation(*, user=None, customer=None, conversation: Conversation) -> bool:
    from chat.permissions import is_chat_staff
    from tenants.seller_permissions import is_tenant_staff_member

    if conversation.is_merchant_conversation:
        if user and user.is_authenticated:
            if is_chat_staff(user):
                return True
            if conversation.tenant_id and is_tenant_staff_member(user, conversation.tenant):
                return True
        return False

    if customer is not None:
        return conversation.user_id == customer.id
    if user and user.is_authenticated:
        if is_chat_staff(user):
            if conversation.tenant_id:
                return is_tenant_staff_member(user, conversation.tenant) or getattr(user, 'is_superuser', False)
            return True
        if conversation.tenant_id and is_tenant_staff_member(user, conversation.tenant):
            return conversation.conversation_type == Conversation.TYPE_B2C
    return False


def is_conversation_staff(user, conversation: Conversation) -> bool:
    """Whether user acts as staff in this conversation (platform or tenant)."""
    from chat.permissions import is_chat_staff
    from tenants.seller_permissions import is_tenant_staff_member

    if not user or not user.is_authenticated:
        return False
    if conversation.is_merchant_conversation:
        if is_chat_staff(user):
            return True
        return bool(conversation.tenant_id and is_tenant_staff_member(user, conversation.tenant))
    if is_chat_staff(user):
        if conversation.tenant_id:
            return is_tenant_staff_member(user, conversation.tenant) or getattr(user, 'is_superuser', False)
        return True
    if conversation.tenant_id and is_tenant_staff_member(user, conversation.tenant):
        return conversation.conversation_type == Conversation.TYPE_B2C
    return False


def _sender_is_platform_staff(user, conversation: Conversation) -> bool:
    from chat.permissions import is_chat_staff
    from tenants.seller_permissions import is_tenant_staff_member

    if not user or not is_chat_staff(user):
        return False
    if conversation.is_merchant_conversation:
        # Platform operators (incl. superuser) reply on the platform side even if
        # the same account is also registered as tenant staff for the merchant.
        if getattr(user, 'is_superuser', False):
            return True
        if conversation.tenant_id and is_tenant_staff_member(user, conversation.tenant):
            return False
        return True
    if conversation.tenant_id and is_tenant_staff_member(user, conversation.tenant):
        return False
    return True


def find_active_conversation(**filters) -> Conversation | None:
    return (
        Conversation.objects.filter(
            **filters,
            status__in=[Conversation.STATUS_PENDING, Conversation.STATUS_ACTIVE],
        )
        .order_by('-updated_at')
        .first()
    )


def create_routed_conversation(**kwargs) -> Conversation:
    conversation_type = kwargs['conversation_type']
    tenant_id = kwargs.get('tenant_id')
    user = kwargs.get('user')
    complaint = kwargs.get('complaint')

    lookup = {'conversation_type': conversation_type}
    if tenant_id is not None:
        lookup['tenant_id'] = tenant_id
    else:
        lookup['tenant__isnull'] = True
    if user is not None:
        lookup['user'] = user
    else:
        lookup['user__isnull'] = True

    existing = find_active_conversation(**lookup)
    if existing:
        return existing

    tenant = Tenant.objects.filter(pk=tenant_id).first() if tenant_id else None
    return Conversation.objects.create(
        conversation_type=conversation_type,
        tenant=tenant,
        user=user,
        complaint=complaint,
        status=Conversation.STATUS_PENDING,
    )


def open_customer_conversation(customer: Customer, context: dict | None = None) -> Conversation:
    route = chat_router.route_customer(context or {})
    tenant_id = route.get('tenant_id')
    complaint = None
    if route['conversation_type'] == Conversation.TYPE_C2P_B and context:
        complaint = context.get('complaint')
    return create_routed_conversation(
        conversation_type=route['conversation_type'],
        tenant_id=tenant_id,
        user=customer,
        complaint=complaint,
    )


def open_tenant_platform_conversation(tenant: Tenant) -> Conversation:
    route = chat_router.route_tenant_staff(tenant.id)
    return create_routed_conversation(
        conversation_type=route['conversation_type'],
        tenant_id=route['tenant_id'],
        user=None,
    )


def open_platform_tenant_conversation(tenant: Tenant) -> Conversation:
    route = chat_router.route_platform_staff({'tenant_id': tenant.id})
    return create_routed_conversation(
        conversation_type=route['conversation_type'],
        tenant_id=route['tenant_id'],
        user=None,
    )


def create_complaint_with_conversation(
    *,
    customer: Customer,
    tenant: Tenant,
    category: str,
    content: str,
    attachments: list | None = None,
    order_id: int | None = None,
) -> tuple[Complaint, Conversation]:
    complaint = Complaint.objects.create(
        customer=customer,
        tenant=tenant,
        order_id=order_id,
        category=category,
        content=content,
        attachments=attachments or [],
    )
    conversation = open_customer_conversation(
        customer,
        {
            'tenant_id': tenant.id,
            'is_complaint': True,
            'complaint': complaint,
        },
    )
    if conversation.complaint_id != complaint.id:
        conversation.complaint = complaint
        conversation.save(update_fields=['complaint', 'updated_at'])
    Message.objects.create(
        conversation=conversation,
        sender_type=Message.SENDER_SYSTEM,
        content=f'客户提交投诉：{complaint.get_category_display()}。{content[:200]}',
    )
    conversation.unread_count_staff += 1
    conversation.updated_at = timezone.now()
    conversation.save(update_fields=['unread_count_staff', 'updated_at'])
    return complaint, conversation


def resolve_conversation_tenant(customer: Customer):
    """Resolve tenant for a new conversation."""
    if customer.tenant_id:
        return customer.tenant
    from tenants.context import get_current_tenant

    return get_current_tenant()


def get_or_create_customer_conversation(customer: Customer, context: dict | None = None) -> Conversation:
    if context:
        return open_customer_conversation(customer, context)
    tenant = resolve_conversation_tenant(customer)
    route_context = {'tenant_id': tenant.id if tenant else None}
    return open_customer_conversation(customer, route_context)


def create_new_customer_conversation(customer: Customer, context: dict | None = None) -> Conversation:
    if context:
        closed_filters = {'user': customer}
        route = chat_router.route_customer(context)
        if route.get('tenant_id'):
            closed_filters['tenant_id'] = route['tenant_id']
            closed_filters['conversation_type'] = route['conversation_type']
        Conversation.objects.filter(**closed_filters, status=Conversation.STATUS_ACTIVE).update(
            status=Conversation.STATUS_CLOSED,
        )
        return open_customer_conversation(customer, context)
    return open_customer_conversation(customer, {'tenant_id': resolve_conversation_tenant(customer).id if resolve_conversation_tenant(customer) else None})


def create_chat_message(
    conversation: Conversation,
    content: str,
    *,
    is_staff: bool,
    staff_user=None,
    customer: Customer | None = None,
) -> Message:
    content = (content or '').strip()
    if not content:
        raise ValueError('消息内容不能为空')
    if conversation.status == Conversation.STATUS_CLOSED:
        raise ValueError('会话已关闭')
    if is_staff and staff_user is None:
        raise ValueError('客服消息缺少发送者')
    if not is_staff and customer is None:
        raise ValueError('用户消息缺少发送者')

    sender_type = Message.SENDER_STAFF if is_staff else Message.SENDER_USER
    message = Message(
        conversation=conversation,
        sender_type=sender_type,
        sender_staff=staff_user if is_staff else None,
        sender_user=customer if not is_staff else None,
        content=content,
    )
    message.save()

    conversation.updated_at = timezone.now()

    if conversation.is_merchant_conversation:
        if is_staff and _sender_is_platform_staff(staff_user, conversation):
            conversation.unread_count_user += 1
        elif is_staff:
            conversation.unread_count_staff += 1
        else:
            pass
        if conversation.status == Conversation.STATUS_PENDING:
            conversation.status = Conversation.STATUS_ACTIVE
        if (
            is_staff
            and not conversation.assigned_to_id
            and _sender_is_platform_staff(staff_user, conversation)
        ):
            conversation.assigned_to = staff_user
    elif is_staff:
        conversation.unread_count_user += 1
        if conversation.status == Conversation.STATUS_PENDING:
            conversation.status = Conversation.STATUS_ACTIVE
        if not conversation.assigned_to_id:
            conversation.assigned_to = staff_user
    else:
        conversation.unread_count_staff += 1

    conversation.save(
        update_fields=[
            'updated_at',
            'unread_count_user',
            'unread_count_staff',
            'status',
            'assigned_to',
        ],
    )
    if conversation.is_merchant_conversation and is_staff and not message_is_platform_staff(message):
        _notify_platform_merchant_chat(conversation, message)
    elif (
        not is_staff
        and conversation.conversation_type in {Conversation.TYPE_C2P, Conversation.TYPE_C2P_B}
    ):
        _notify_platform_customer_chat(conversation, message)
    elif (
        not is_staff
        and conversation.conversation_type == Conversation.TYPE_B2C
        and conversation.tenant_id
    ):
        _notify_merchant_customer_chat(conversation, message)
    elif conversation.is_merchant_conversation and is_staff and message_is_platform_staff(message):
        from tenants.notify import push_seller_notify

        if conversation.tenant_id:
            push_seller_notify(
                conversation.tenant_id,
                {
                    'type': 'chat_message',
                    'level': 'urgent',
                    'title': '平台客服发来新消息',
                    'content': (message.content or '')[:200],
                    'conversation_id': conversation.id,
                    'timestamp': message.created_at.isoformat(),
                },
            )
    return message


def mark_conversation_read(conversation: Conversation, *, reader_is_staff: bool) -> None:
    now = timezone.now()
    unread_filter = Q(read_at__isnull=True)
    if conversation.is_merchant_conversation:
        if reader_is_staff:
            unread_filter &= Q(sender_type=Message.SENDER_STAFF)
            conversation.unread_count_staff = 0
            update_fields = ['unread_count_staff']
        else:
            unread_filter &= Q(sender_type=Message.SENDER_STAFF)
            conversation.unread_count_user = 0
            update_fields = ['unread_count_user']
    elif reader_is_staff:
        unread_filter &= Q(sender_type=Message.SENDER_USER)
        conversation.unread_count_staff = 0
        update_fields = ['unread_count_staff']
    else:
        unread_filter &= Q(sender_type=Message.SENDER_STAFF)
        conversation.unread_count_user = 0
        update_fields = ['unread_count_user']

    conversation.messages.filter(unread_filter).update(read_at=now)
    conversation.save(update_fields=update_fields)


def mark_conversation_read_for_user(conversation: Conversation, user, request=None) -> None:
    from chat.permissions import is_chat_staff

    if conversation.is_merchant_conversation and user and user.is_authenticated:
        tenant = getattr(request, 'tenant', None) if request is not None else None
        if is_chat_staff(user) and tenant is None:
            mark_conversation_read(conversation, reader_is_staff=True)
        elif _sender_is_platform_staff(user, conversation):
            mark_conversation_read(conversation, reader_is_staff=True)
        else:
            mark_conversation_read(conversation, reader_is_staff=False)
        return
    if user and user.is_authenticated:
        mark_conversation_read(
            conversation,
            reader_is_staff=is_conversation_staff(user, conversation),
        )
    else:
        mark_conversation_read(conversation, reader_is_staff=False)


def assign_conversation(conversation: Conversation, staff_user) -> Conversation:
    conversation.assigned_to = staff_user
    if conversation.status == Conversation.STATUS_PENDING:
        conversation.status = Conversation.STATUS_ACTIVE
    conversation.save(update_fields=['assigned_to', 'status', 'updated_at'])
    return conversation


def close_conversation(conversation: Conversation) -> Conversation:
    now = timezone.now()
    conversation.status = Conversation.STATUS_CLOSED
    conversation.unread_count_user = 0
    conversation.unread_count_staff = 0
    conversation.messages.filter(read_at__isnull=True).update(read_at=now)
    conversation.save(
        update_fields=['status', 'unread_count_user', 'unread_count_staff', 'updated_at'],
    )
    return conversation


def _notify_merchant_customer_chat(conversation: Conversation, message: Message) -> None:
    """Alert merchant staff when a customer sends a B2C message."""
    from tenants.notify import push_seller_notify

    if not conversation.tenant_id:
        return
    customer_name = get_sender_display_name(message)
    push_seller_notify(
        conversation.tenant_id,
        {
            'type': 'chat_message',
            'level': 'urgent',
            'title': f'【客户咨询】{customer_name} 发来新消息',
            'content': (message.content or '')[:200],
            'conversation_id': conversation.id,
            'target_url': '/chat',
            'timestamp': message.created_at.isoformat(),
        },
    )


def _notify_platform_customer_chat(conversation: Conversation, message: Message) -> None:
    """Alert platform staff when a customer sends a C2P / complaint chat message."""
    from tenants.notify import push_admin_alert

    customer_name = '用户'
    if conversation.user_id:
        customer_name = conversation.user.display_name or conversation.user.phone or customer_name
    tenant_suffix = ''
    if conversation.conversation_type == Conversation.TYPE_C2P_B and conversation.tenant_id:
        tenant_suffix = f'（投诉 {conversation.tenant.name}）'
    push_admin_alert(
        {
            'type': 'system_alert',
            'level': 'urgent',
            'title': f'【商城客服】{customer_name}{tenant_suffix} 发来新消息',
            'content': (message.content or '')[:200],
            'target_url': '/customers/chat',
            'conversation_id': conversation.id,
            'tenant_id': conversation.tenant_id,
            'timestamp': message.created_at.isoformat(),
        },
    )


def _notify_platform_merchant_chat(conversation: Conversation, message: Message) -> None:
    """Alert platform staff when a merchant sends a B2P message."""
    if not conversation.is_merchant_conversation:
        return
    if message.sender_type != Message.SENDER_STAFF:
        return
    if message_is_platform_staff(message):
        return
    from tenants.notify import push_admin_alert

    tenant_name = conversation.tenant.name if conversation.tenant_id else '商户'
    push_admin_alert(
        {
            'type': 'system_alert',
            'level': 'urgent',
            'title': f'【商户客服】{tenant_name} 发来新消息',
            'content': (message.content or '')[:200],
            'target_url': '/tenants/chat',
            'conversation_id': conversation.id,
            'tenant_id': conversation.tenant_id,
            'timestamp': message.created_at.isoformat(),
        },
    )


def notify_merchant_chat_started(conversation: Conversation) -> None:
    """Alert platform when a merchant opens B2P support."""
    if not conversation.is_merchant_conversation or not conversation.tenant_id:
        return
    if conversation.unread_count_staff <= 0:
        conversation.unread_count_staff = 1
        conversation.save(update_fields=['unread_count_staff', 'updated_at'])
    from tenants.notify import push_admin_alert

    push_admin_alert(
        {
            'type': 'system_alert',
            'level': 'urgent',
            'title': f'【商户客服】{conversation.tenant.name} 发起了在线客服',
            'content': '请及时接入会话',
            'target_url': '/tenants/chat',
            'conversation_id': conversation.id,
            'tenant_id': conversation.tenant_id,
            'timestamp': timezone.now().isoformat(),
        },
    )


def touch_staff_presence(user, *, online: bool = True) -> StaffPresence:
    presence, _ = StaffPresence.objects.get_or_create(user=user)
    presence.is_online = online
    presence.last_seen = timezone.now()
    presence.save(update_fields=['is_online', 'last_seen'])
    return presence


def has_online_chat_staff() -> bool:
    cutoff = timezone.now() - timezone.timedelta(seconds=90)
    return StaffPresence.objects.filter(
        Q(is_online=True) | Q(last_seen__gte=cutoff),
    ).exists()


def get_staff_unread_summary(*, user=None, tenant=None) -> dict:
    detailed = get_staff_unread_summary_detailed(user=user, tenant=tenant)
    return {
        'unread_total': detailed['unread_total'],
        'unreplied_conversations': detailed['unreplied_conversations'],
        **detailed,
    }


def _aggregate_unread(queryset):
    aggregated = queryset.aggregate(
        unread_total=Sum('unread_count_staff'),
        unreplied_conversations=Count('id'),
    )
    unread_total = int(aggregated['unread_total'] or 0)
    unreplied_conversations = int(aggregated['unreplied_conversations'] or 0)
    if unread_total <= 0:
        unreplied_conversations = 0
    return unread_total, unreplied_conversations


def get_staff_unread_summary_detailed(*, user=None, tenant=None) -> dict:
    from tenants.models import TenantAppeal

    Conversation.all_objects.filter(
        status=Conversation.STATUS_CLOSED,
    ).filter(
        Q(unread_count_staff__gt=0) | Q(unread_count_user__gt=0),
    ).update(unread_count_staff=0, unread_count_user=0)

    queryset = Conversation.all_objects.filter(
        status__in=[Conversation.STATUS_PENDING, Conversation.STATUS_ACTIVE],
        unread_count_staff__gt=0,
    )
    if tenant is not None:
        queryset = queryset.filter(tenant=tenant)
    elif user is not None:
        queryset = filter_conversations_for_staff(user, queryset)

    customer_qs = queryset.exclude(
        conversation_type__in=[Conversation.TYPE_B2P, Conversation.TYPE_P2B],
    )
    merchant_qs = queryset.filter(
        conversation_type__in=[Conversation.TYPE_B2P, Conversation.TYPE_P2B],
    )

    customer_unread, customer_unreplied = _aggregate_unread(customer_qs)
    merchant_unread, merchant_unreplied = _aggregate_unread(merchant_qs)
    unread_total = customer_unread + merchant_unread
    unreplied_conversations = customer_unreplied + merchant_unreplied

    pending_appeals = 0
    if user is not None and tenant is None:
        pending_appeals = TenantAppeal.objects.filter(
            status__in=[TenantAppeal.STATUS_PENDING, TenantAppeal.STATUS_PROCESSING],
        ).count()

    return {
        'customer_unread_total': customer_unread,
        'customer_unreplied_conversations': customer_unreplied,
        'merchant_unread_total': merchant_unread,
        'merchant_unreplied_conversations': merchant_unreplied,
        'pending_tenant_appeals': pending_appeals,
        'unread_total': unread_total,
        'unreplied_conversations': unreplied_conversations,
    }


def get_workbench_stats(*, user=None, tenant=None) -> dict:
    today = timezone.localdate()
    online_staff = StaffPresence.objects.filter(is_online=True).count()
    conversations = Conversation.objects.filter(
        status__in=[Conversation.STATUS_PENDING, Conversation.STATUS_ACTIVE],
    )
    if tenant is not None:
        conversations = conversations.filter(tenant=tenant)
    elif user is not None:
        conversations = filter_conversations_for_staff(user, conversations)
    pending_count = conversations.filter(status=Conversation.STATUS_PENDING).count()
    today_messages = Message.objects.filter(created_at__date=today).count()
    unread_summary = get_staff_unread_summary(user=user, tenant=tenant)
    return {
        'online_staff': online_staff,
        'pending_conversations': pending_count,
        'today_messages': today_messages,
        'unread_total': unread_summary['unread_total'],
        'unreplied_conversations': unread_summary['unreplied_conversations'],
    }


def get_online_staff_users():
    cutoff = timezone.now() - timezone.timedelta(seconds=90)
    return StaffPresence.objects.filter(
        Q(is_online=True) | Q(last_seen__gte=cutoff),
    ).select_related('user')
