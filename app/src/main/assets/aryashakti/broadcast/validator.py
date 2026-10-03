from rest_framework import serializers

from app_farm.utils.constants import MSG_TYPES

class SendGroupSmsValidator(serializers.Serializer):
    contacts = serializers.ListField(required=True, allow_empty=False)
    msg = serializers.CharField(min_length=2, max_length=500, required=True)
    template_id = serializers.CharField(min_length=2, max_length=50, required=True)
    msg_type = serializers.ChoiceField(required=True,choices=MSG_TYPES)
    send_notification = serializers.BooleanField(required=True)