"""Approval serializers."""

from rest_framework import serializers

from approval.models import Approval, ApprovalLog


class ApprovalLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApprovalLog
        fields = ['id', 'action', 'operator_id', 'operator_name', 'remark', 'created_at']


class ApprovalSerializer(serializers.ModelSerializer):
    approval_type_label = serializers.CharField(source='get_approval_type_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    priority_label = serializers.CharField(source='get_priority_display', read_only=True)
    reviewer_name = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Approval
        fields = [
            'id',
            'approval_type',
            'approval_type_label',
            'business_type',
            'business_id',
            'title',
            'summary',
            'application_data',
            'action_url',
            'applicant_type',
            'applicant_id',
            'status',
            'status_label',
            'reviewer',
            'reviewer_name',
            'reviewed_at',
            'reject_reason',
            'review_remark',
            'priority',
            'priority_label',
            'timeout_at',
            'is_overdue',
            'created_at',
            'updated_at',
        ]

    def get_reviewer_name(self, obj: Approval) -> str:
        if not obj.reviewer_id:
            return ''
        reviewer = getattr(obj, 'reviewer', None)
        if reviewer is None:
            return ''
        return reviewer.get_full_name() or reviewer.username

    def get_is_overdue(self, obj: Approval) -> bool:
        if obj.status != Approval.STATUS_PENDING or not obj.timeout_at:
            return False
        from django.utils import timezone

        return obj.timeout_at < timezone.now()


class ApprovalDetailSerializer(ApprovalSerializer):
    logs = ApprovalLogSerializer(many=True, read_only=True)

    class Meta(ApprovalSerializer.Meta):
        fields = [*ApprovalSerializer.Meta.fields, 'logs']
