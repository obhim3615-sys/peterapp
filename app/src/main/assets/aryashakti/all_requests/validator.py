from rest_framework import serializers

class CreateFpoRequest(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)
    phone = serializers.IntegerField(required=True)

class CreateFarmerToFpoRequest(serializers.Serializer):
    org_id = serializers.IntegerField(required=True)

class RequestsListValidator(serializers.Serializer):
    org_id = serializers.IntegerField(required=True)
    status = serializers.IntegerField(required=True)

class RequestsUpdateValidator(serializers.Serializer):
    req_id = serializers.IntegerField(required=True)
    status = serializers.IntegerField(required=True)
