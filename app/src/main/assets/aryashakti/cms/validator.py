from rest_framework import serializers

class GetPageDetails(serializers.Serializer):
    page_id = serializers.IntegerField(required=True)
    country_id = serializers.IntegerField(required=True)

class GetConfigValidator(serializers.Serializer):
    country_id = serializers.IntegerField(required=True)
    key = serializers.CharField(required=True)
