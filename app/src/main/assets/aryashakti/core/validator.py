from rest_framework import serializers

class GetCustomFormDetails(serializers.Serializer):
    form_id = serializers.IntegerField(required=True)
