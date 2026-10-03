from rest_framework import serializers
from .models import *
from payment.serializer import BankAccountSerializer

class KutumbsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Kutumb
        fields = ('id','status','payment')

class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ('id','first_name','last_name','phone')

class NomineeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Nominee
        fields = ('id','name','phone','relationship')

class MemberDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ('id','first_name','last_name','phone','dob','gender','district','city','pincode','state','address1','address2',)

class MemberDetailsWithBankDetailsSerializer(serializers.ModelSerializer):
    bank_acc = serializers.SerializerMethodField('get_bank_acc_details')

    def get_bank_acc_details(self,obj):
        return BankAccountSerializer(obj.bank_acc,many=False).data
    class Meta:
        model = Member
        fields = ('id','first_name','last_name','phone','dob','gender','pincode','state','address1','address2','bank_acc')

class KutumbDetailsSerializer(serializers.ModelSerializer):
    husband = serializers.SerializerMethodField('get_husband_details')
    wife = serializers.SerializerMethodField('get_wife_details')

    def get_husband_details(self,obj):
        return MemberSerializer(obj.husband,many=False).data
    
    def get_wife_details(self,obj):
        return MemberSerializer(obj.wife,many=False).data
    
    class Meta:
        model = Kutumb
        fields = ('id','status','payment','husband','wife')

class ClaimableKutumbDetailsSerializer(serializers.ModelSerializer):
    husband = serializers.SerializerMethodField('get_husband_details')
    wife = serializers.SerializerMethodField('get_wife_details')

    def get_husband_details(self,obj):
        return MemberDetailsSerializer(obj.husband,many=False).data
    
    def get_wife_details(self,obj):
        return MemberSerializer(obj.wife,many=False).data
    
    class Meta:
        model = Kutumb
        fields = ('id','kutumb_id','valid_until','husband','wife')




class InsuranceEnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = InsuranceEnrollment
        fields = '__all__'