from rest_framework import serializers
from app_farm.models import user,organizations,user_roles
from app_farm.serializers import UserRoleSerializer

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = organizations
        fields = ('id','org_name','logo','room_100ms','map_layer','latitude','longitude','zoom','carousel1','carousel2','carousel3','carousel4','members','acres','crops','stress','damaged','health','relationship_manager_name','relationship_manager_no')

class VerifyOtpSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer('organization')
    user_role = UserRoleSerializer('user_role')
    
    class Meta:
        model = user
        fields = ('id','full_name','full_name_telugu','user_profile_img','firebase_token','organization','admin','email','user_role','is_deleted')
        depth = 1

class CreateFarmerSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer('organization')
    user_role = UserRoleSerializer('user_role')
    
    class Meta:
        model = user
        fields = ('id','full_name','full_name_telugu','user_profile_img','firebase_token','organization','user_role','email','latitude','longitude','address_pincode','address_country','address_state','address_district','address_taluka','address_village')
        depth = 1

