from rest_framework import serializers
from . import models
import json
from rest_framework.serializers import Serializer, FileField
from .models import *
from django.db.models import F
from decimal import Decimal, InvalidOperation




class ServiceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model=Service
        fields="__all__"


class UserServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model=UserService
        fields="__all__"

class ServiceDetailedSerializer(serializers.ModelSerializer):
    validity= serializers.SerializerMethodField('get_validity')
    remaining= serializers.SerializerMethodField('get_remaining')
    service_user_type= serializers.SerializerMethodField('get_service_user_type')
    sponsored_by_full_name= serializers.SerializerMethodField('get_sponsored_by_full_name')
    sponsored_by_id=serializers.SerializerMethodField('get_sponsored_by_id')
    def get_validity(self,obj):
        return obj.validity
    
    def get_sponsored_by_full_name(self,obj):
        if obj:
            return obj.sponsored_by_full_name
        
        return None
    
    def get_sponsored_by_id(self,obj):
        if obj:
            return obj.sponsored_by_id
        return None
    
    def get_remaining(self,obj):
        if obj:
            return obj.remaining
        return None
    
    
    def get_service_user_type(self,obj):
        if obj:
            return obj.service_user_type
        return None

    class Meta:
        model=Service
        fields=['id','name','slug','type','unit','status','sponsored_by_id','sponsored_by_full_name','type','price','validity','remaining','service_user_type']

        #'sponsored_by_full_name','get_sponsored_by_id',
class SubscriptionSerializer(serializers.ModelSerializer):
    subscription_service = serializers.SerializerMethodField()


    def get_subscription_service(self, obj):
        if obj and obj.subscription_service:
            return obj.subscription_service.filter(service__status=True).annotate(
                s_id=F('service__id'),
                service_name=F('service__name'),
                service_slug=F('service__slug'),
                service_type=F('service__type'),
                service_price=F('service__price'),
                unit=F('service__unit'),
                # Add more fields as needed
            ).values('s_id','service_name', 'service_slug', 'service_price','service_type', 'validity','unit')
        return None

    class Meta:
        model=Subscription
        fields=['id','name','status','color','slug','price','validity','type','subscription_service','package_type']



class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model=Coupon
        fields="__all__"