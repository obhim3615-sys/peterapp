from rest_framework import serializers
from app_farm.utils.constants import SUBSCRIPTION_TYPES

class BaseCreateOrderValidator(serializers.Serializer):
    price = serializers.DecimalField(required=True,decimal_places=2,max_digits=10)
    total_discount = serializers.DecimalField(required=True,decimal_places=2,max_digits=10)
    taxes = serializers.DecimalField(required=True,decimal_places=2,max_digits=10)
    final_price = serializers.DecimalField(required=True,decimal_places=2,max_digits=10)
    description = serializers.CharField(required=True,max_length=500)
    package_id = serializers.IntegerField(required=True)
    package_validity = serializers.IntegerField(required=True)
    package_type = serializers.ChoiceField(required=True,choices=SUBSCRIPTION_TYPES)
    coupon_id = serializers.IntegerField(required=False, allow_null=True)
    coupon_value = serializers.DecimalField(required=False,decimal_places=2,max_digits=10,allow_null=True)
    coupon_discount = serializers.DecimalField(required=False,decimal_places=2,max_digits=10,allow_null=True)
    services = serializers.ListField(required=True,allow_empty=False)

class RandomFarmerCreateOrderValidator(BaseCreateOrderValidator):
    num_of_farmers = serializers.IntegerField(required=True)
    org_id = serializers.IntegerField(required=True)

class NoRandomFarmerCreateOrderValidator(BaseCreateOrderValidator):
    farmers = serializers.ListField(required=True,allow_empty=False)

class UserBankValidation(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=100, required=True)
    acc_num = serializers.CharField(max_length=40,required=True)
    ifsc = serializers.CharField(min_length=11, max_length=11, required=True)

class UserBankValidationByAdmin(UserBankValidation):
    user_id = serializers.IntegerField(required=True)



class UserBankValidationPams(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=100, required=True)
    acc_num = serializers.CharField(max_length=40,required=True)
    ifsc = serializers.CharField(min_length=11, max_length=11, required=True)
    bank_name = serializers.CharField(required=True)
    city_name = serializers.CharField( required=True)

class UserBankValidationByAdminPams(UserBankValidationPams):
    user_id = serializers.IntegerField(required=True)
    