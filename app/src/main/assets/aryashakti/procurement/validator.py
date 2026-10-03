from rest_framework import serializers

class ProcurementValidator(serializers.Serializer):
    user_to_id= serializers.IntegerField(required=True)
    crop_id=serializers.IntegerField(required=True)
    variety=serializers.CharField(required=True)
    qty=serializers.IntegerField(required=True)
    rate=serializers.IntegerField(required=True)
    amount=serializers.IntegerField(required=True)
    # farm_id=serializers.IntegerField(required=True)

class CastlerSendPayment(serializers.Serializer):
    user_list = serializers.ListField(required=True,allow_empty=False)
