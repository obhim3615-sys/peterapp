from rest_framework import serializers
from app_farm.utils.constants import LAND_SIZE_UNIT,LAND_SIZE_UNIT_TELEGU,GENDERS

class LevelZeroValidator(serializers.Serializer):
    phone = serializers.IntegerField(required=True)
    secret_key = serializers.CharField(min_length=2, max_length=100, required=True)

class LevelOneValidator(LevelZeroValidator):
    fcm_token = serializers.CharField(required=True)

class LevelTwoValidator(LevelOneValidator):
    name = serializers.CharField(max_length=100, required=True)
    name_telugu = serializers.CharField(max_length=100, required=False, allow_null=True)
    language_selected = serializers.IntegerField(required=True)
    pincode = serializers.IntegerField(required=True)
    country = serializers.CharField(required=True)
    state = serializers.CharField(required=True)
    district = serializers.CharField(required=True)
    taluka = serializers.CharField(required=True)
    village = serializers.CharField(required=True)
    country_id = serializers.IntegerField(required=True)

class LevelThreeValidator(LevelTwoValidator):
    land_size = serializers.CharField(max_length=100, required=True)
    land_size_unit = serializers.ChoiceField(choices=LAND_SIZE_UNIT, required=True)
    land_size_unit_telugu = serializers.ChoiceField(choices=LAND_SIZE_UNIT_TELEGU, required=False, allow_null=True, allow_blank=True)

class LevelFourValidator(LevelTwoValidator):
    role = serializers.IntegerField(required=True)
    lat = serializers.FloatField(required=False, allow_null=True)
    long = serializers.FloatField(required=False, allow_null=True)

class VerifyOtpValidator(LevelOneValidator):
    otp = serializers.IntegerField(required=True)
    country_code = serializers.CharField(max_length=5, required=True)

class VerifyOtpByAdminValidator(serializers.Serializer):
    name = serializers.CharField(max_length=100, required=True)
    phone = serializers.IntegerField(required=True)
    otp = serializers.IntegerField(required=True)

class SendOtpValidator(LevelZeroValidator):
    country_code = serializers.CharField(max_length=5, required=True)
    unique_id = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)

class SignupValidator(LevelThreeValidator):
    org_id = serializers.IntegerField(required=True)
    user_profile_img = serializers.CharField(required=True)

class CreateFarmerValidator(LevelThreeValidator, LevelFourValidator):
    no_of_plots = serializers.IntegerField(required=True)
    crop_id = serializers.ListField(required=True, allow_empty=False)
    gender = serializers.ChoiceField(choices=GENDERS, required=True)

class CreateSponsorValidator(LevelFourValidator):
    org_name = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)

class CreateBdValidator(LevelOneValidator):
    name = serializers.CharField(max_length=100, required=True)
    language_selected = serializers.IntegerField(required=True)
    role = serializers.IntegerField(required=True)
    org_id = serializers.IntegerField(required=True)
    country_id = serializers.IntegerField(required=True)
    lat = serializers.FloatField(required=True)
    long = serializers.FloatField(required=True)
