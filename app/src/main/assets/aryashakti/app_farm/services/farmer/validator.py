from rest_framework import serializers
from app_farm.utils.constants import USER_DESIGNATIONS

class SmsFarmerListValidator(serializers.Serializer):
    org_id = serializers.IntegerField(required=True)
    stressed = serializers.ChoiceField(choices=[0, 1], required=False, allow_null=True, allow_blank=True)
    featured = serializers.ChoiceField(choices=[0, 1], required=False, allow_null=True, allow_blank=True)
    healthy = serializers.ChoiceField(choices=[0, 1], required=False, allow_null=True, allow_blank=True)
    sort_by = serializers.ChoiceField(choices=[0, 1, 2, 3], required=False, allow_null=True, allow_blank=True)

class GetRolesValidator(serializers.Serializer):
    secret_key = serializers.CharField(min_length=2, max_length=100, required=True)
    country_id = serializers.IntegerField(required=True)

class LatLongValidator(GetRolesValidator):
    lat = serializers.FloatField(required=True)
    long = serializers.FloatField(required=True)

class PincodeValidator(GetRolesValidator):
    pincode = serializers.IntegerField(required=True,min_value=100000,max_value=999999)

class UpdateFarmerValidator(serializers.Serializer):
    name = serializers.CharField(required=True)
    pincode = serializers.IntegerField(required=True,min_value=100000,max_value=999999)
    country = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    district = serializers.CharField(required=True)
    taluka = serializers.CharField(required=True)
    village = serializers.CharField(required=True)
    lat = serializers.FloatField(required=True)
    long = serializers.FloatField(required=True)
    designation = serializers.ChoiceField(choices=USER_DESIGNATIONS,required=True)

class CreateFarmerBySponsorValidator(serializers.Serializer):
    name = serializers.CharField(required=True)
    phone = serializers.IntegerField(required=True)
    country_id = serializers.IntegerField(required=True)

