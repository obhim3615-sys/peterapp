from rest_framework import serializers
from app_farm.utils.constants import LAND_SIZE_UNIT,LAND_SIZE_UNIT_TELEGU

class GetOrgListValidator(serializers.Serializer):
    lat = serializers.FloatField(required=False,)
    long = serializers.FloatField(required=False,)
    search_by_name = serializers.CharField(max_length=200, required=True,allow_blank=True)
    secret_key = serializers.CharField(min_length=2, max_length=100, required=True)

class GetOrgDetailValidator(serializers.Serializer):
    org_id = serializers.IntegerField(required=True)

class GetOrgTypesValidator(serializers.Serializer):
    secret_key = serializers.CharField(min_length=2, max_length=100, required=True)

class OrgCreateValidator(serializers.Serializer):
    phone = serializers.IntegerField(required=True)
    secret_key = serializers.CharField(min_length=2, max_length=100, required=True)
    fcm_token = serializers.CharField(required=True)
    name = serializers.CharField(max_length=100, required=True)
    name_telugu = serializers.CharField(max_length=100, required=False, allow_null=True)
    land_size = serializers.CharField(max_length=100, required=True)
    land_size_unit = serializers.ChoiceField(choices=LAND_SIZE_UNIT, required=True)
    land_size_unit_telugu = serializers.ChoiceField(choices=LAND_SIZE_UNIT_TELEGU, required=False, allow_null=True, allow_blank=True)
    role = serializers.IntegerField(required=True)
    language_selected = serializers.IntegerField(required=True)
    pincode = serializers.IntegerField(required=True)
    country = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    district = serializers.CharField(required=True)
    taluka = serializers.CharField(required=True)
    village = serializers.CharField(required=True)
    crop_id = serializers.ListField(required=True, allow_empty=False)
    lat = serializers.FloatField(required=True)
    long = serializers.FloatField(required=True)
    org_name = serializers.CharField(max_length=100, required=True)
    members = serializers.IntegerField(required=True)
    org_type = serializers.IntegerField(required=True)
    country_id = serializers.IntegerField(required=True)

class UploadDocValidator(serializers.Serializer):
    org_id=serializers.IntegerField(required=True)
    user_id=serializers.IntegerField(required=True)
    secret_key = serializers.CharField(min_length=2, max_length=100, required=True)

class SendNotificationValidator(serializers.Serializer):
    org_id=serializers.IntegerField(required=True)
    msg = serializers.CharField(min_length=2, max_length=500, required=True)