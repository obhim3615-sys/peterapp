from rest_framework import serializers
from app_farm.models import user,organizations
from .models import Requests
from app_farm.serializers import CropsListSerializer

class UserSerializer(serializers.ModelSerializer):
    # arr = serializers.ListField(child=serializers.CharField())
    crop_list= serializers.SerializerMethodField('get_crops')

    def get_crops(self,obj):
        return CropsListSerializer(obj.crops_interest,many=True).data

    class Meta:
        model = user
        fields = ('id','full_name','mobile_number','land_size','land_size_unit','address_pincode','address_country','address_state','address_district','address_taluka','address_village','user_profile_img','crop_list')

class RequestsListSerializer(serializers.ModelSerializer):
    user = UserSerializer('user')
    
    class Meta:
        model = user
        fields = ('id','user')
        depth = 1
