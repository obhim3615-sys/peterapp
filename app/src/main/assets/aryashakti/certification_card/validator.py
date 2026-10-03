from rest_framework import serializers


class FarmerCertificationSerializer(serializers.Serializer):
    farmer_id=serializers.IntegerField(required=True)
    certification_id=serializers.IntegerField(required=True)
    expiry_date=serializers.DateField(required=True)
    issued_date=serializers.DateField(required=True)
    authority_name=serializers.CharField(required=True)
    authority_logo=serializers.CharField(required=True)

