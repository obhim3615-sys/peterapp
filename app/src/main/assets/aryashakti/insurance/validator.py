from rest_framework import serializers

from app_farm.utils.constants import RELATIONSHIPS,ASSIGNEE_RELATIONSHIPS
from payment.validator import UserBankValidation

class AddMemberValidator(serializers.Serializer):
    # front_aadhaar = serializers.ImageField(allow_empty_file=False)
    # back_aadhaar = serializers.ImageField(allow_empty_file=False)
    otp=serializers.CharField(required=True)
    request_id=serializers.CharField(required=True) 
    phone = serializers.IntegerField(required=True)
    email = serializers.EmailField(required=False,allow_null=True)
    fpo_name = serializers.CharField(required=True,max_length=20)
    fpo_state = serializers.CharField(required=True,max_length=30)
    kutumb_id = serializers.IntegerField(required=False,allow_null=True)
    org_id = serializers.IntegerField(required=True)
    aadhaar_num = serializers.CharField(required=True,max_length=12)

class MemberBankValidation(UserBankValidation):
    member_id = serializers.IntegerField(required=True)
    kutumb_id = serializers.IntegerField(required=True)


class InsuranceBankValidation(UserBankValidation):
    insurance_id = serializers.IntegerField(required=True)

class SameBankAccountValidation(serializers.Serializer):
    member_id = serializers.IntegerField(required=True)
    husband_id = serializers.IntegerField(required=True)

class MemberDetailsValidation(serializers.Serializer):
    member_id = serializers.IntegerField(required=True)

class KutumbsSummaryValidator(serializers.Serializer):
    org_id = serializers.IntegerField(required=True)

class AddNomineeValidator(serializers.Serializer):
    kutumb_id = serializers.IntegerField(required=True)
    name = serializers.CharField(required=True,max_length=50)
    phone = serializers.IntegerField(required=True)
    relationship = serializers.ChoiceField(required=True,choices=RELATIONSHIPS)
    assignee = serializers.CharField(required=False,max_length=50,allow_null=True,allow_blank=True)
    assignee_relationship = serializers.ChoiceField(required=False,choices=ASSIGNEE_RELATIONSHIPS,allow_null=True,allow_blank=True)

class UpdateMemberValidator(serializers.Serializer):
    pincode = serializers.IntegerField(required=False,min_value=100000,max_value=999999)
    address1 = serializers.CharField(required=False,max_length=200)
    address2 = serializers.CharField(required=False,max_length=200)
    state = serializers.CharField(required=False,max_length=50)
    member_id = serializers.IntegerField(required=False)

class VerifyConsentValidator(serializers.Serializer):
    phone = serializers.IntegerField(required=True)
    otp = serializers.IntegerField(required=True,min_value=100000,max_value=999999)
    kutumb_id = serializers.IntegerField(required=True)

class VerifyInsuranceConsentValidator(serializers.Serializer):
    phone = serializers.IntegerField(required=True)
    otp = serializers.IntegerField(required=True,min_value=100000,max_value=999999)
    insurance_id = serializers.IntegerField(required=True)

class CashPaymentValidator(serializers.Serializer):
    cash_receipt = serializers.FileField(allow_empty_file=False)
    kutumb_id = serializers.IntegerField(required=True)
    amount = serializers.DecimalField(required=True,decimal_places=2,max_digits=10)

class OnlinePaymentValidator(serializers.Serializer):
    kutumb_ids = serializers.ListField(required=True, allow_empty=False)
    amount = serializers.DecimalField(required=True,decimal_places=2,max_digits=10)
