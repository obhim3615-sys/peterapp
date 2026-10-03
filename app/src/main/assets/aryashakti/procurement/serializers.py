from rest_framework import serializers
from .models import *
from app_farm.utils.helper import remove_media

class ProcurementRegisterSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = ProcurementRegister
        fields="__all__"

class ProcurementImageSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return remove_media(self,instance,ProcurementImageSerializer,'image_url')
    
    class Meta:
        model = ProcurementImage
        fields="__all__"

class ProcurementSerializer(serializers.ModelSerializer):
    user_to_name= serializers.SerializerMethodField('get_user_to_name')
    address= serializers.SerializerMethodField('get_address')
    crop_name= serializers.SerializerMethodField('get_crop_name')
    payment_type= serializers.SerializerMethodField('get_payment_type')
    payment_status= serializers.SerializerMethodField('get_payment_status')
    payment_link_id= serializers.SerializerMethodField('get_payment_link_id')
    payout_status= serializers.SerializerMethodField('get_payout_status')
    procurement_img= serializers.SerializerMethodField('get_procurement_img')
    mobile_number= serializers.SerializerMethodField('get_mobile_number')
    payment_img=serializers.SerializerMethodField('get_payment_img')
    kyc_documents= serializers.SerializerMethodField('get_kyc_documents')
    user_image= serializers.SerializerMethodField('get_user_image')
    country_code= serializers.SerializerMethodField('get_country_code')

    def get_address(self,obj): 
        farm=obj.user_to  
        if farm:     
            return obj.user_to.address_taluka
        return None

    def get_user_to_name(self,obj):
        farm= obj.user_to
        if farm:
            return farm.full_name   
        return None
    
    def get_crop_name(self,obj):
        return obj.crop.crop_name
    
    def get_payment_type(self,obj):
        payment=None
        if obj.payment:
            payment=obj.payment.payment_type
        return payment
    

    def get_payment_link_id(self,obj):
        payment=None
        if obj.payment:
            payment=obj.payment.payment_link_id
        return payment
    
    def get_payment_status(self,obj):
        payment=None
        if obj.payment:
            payment=obj.payment.status
        return payment
    
    def get_payout_status(self,obj):
        payment=None
        if obj.payout:
            payment=obj.payout.status
        return payment
    
    def get_payment_img(self,obj):
        payment=None
        if obj.payment:
            payment=obj.payment.response
        return payment
    
    def get_procurement_img(self,obj):
        imgs= obj.procurement_img.all()
        if imgs:
            return ProcurementImageSerializer(imgs,many=True).data
        return None
    
    def get_user_image(self,obj):
        return obj.user_to.user_profile_img
    
    def get_country_code(self,obj):
        return obj.user_to.country.mobile_code
    
    def get_mobile_number(self,obj):
        farm= obj.user_to
        if farm:
            return farm.mobile_number
        return None
    
    def get_kyc_documents(self,obj):
        docs = list(obj.user_to.document_user.filter(status=1).values_list('type', flat=True))
        if obj.user_to.otp_verfied:
            docs.append('otp_verified')
        return docs
    
    class Meta:
        model = Procurement
        fields=['user_to_name','user_image','country_code','payment_link_id','kyc_documents','address','type','crop_name','mobile_number','payment_img','payment_type','payment_status','payout_status','description','procurement_img','id','crop','procure_register','user_from','user_to','variety','qty','rate','amount','payment','status','created_at','updated_at']