from rest_framework import serializers
from app_farm.models import organizations,OrgType,user,Tag,TagOrganization,agenda
from app_farm.serializers import orgSerializer
from app_farm.utils.helper import remove_media


class GetOrgListSerializer(serializers.ModelSerializer):
    class Meta:
        model = organizations
        fields = ('id','org_name','share_capital','paid_capital','state','district','is_verified','members')

class GetOrgDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = organizations
        fields = ('id','org_name','share_capital','paid_capital','state','district','village','taluka','country','is_verified')

class GetOrgTypesListSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return remove_media(self,instance,GetOrgTypesListSerializer,'image')
    
    class Meta:
        model = OrgType
        fields = ('id','name','image')

class SendNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = user
        fields = ('firebase_token','mobile_number')

class TagSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        return remove_media(self,instance,TagSerializer,'image')

    class Meta:
        model=Tag
        fields=["id","name","image","color"]


class TagOrganizationSerializer(serializers.ModelSerializer):
    organization=orgSerializer()
    class Meta:
        model=TagOrganization
        fields="__all__"
    

class AgendaSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return remove_media(self,instance,AgendaSerializer,'img_url')

    class Meta:
        model=agenda
        fields=['id','img_url','text','status']