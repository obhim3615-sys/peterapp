from rest_framework import serializers
from app_farm.models import farm,user_roles,SoilReport
from app_farm.utils.helper import remove_media

class SmsFarmerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = farm
        fields = ('id','user','name','farmer_contact')

class GetRolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = user_roles
        fields = "__all__"

    def to_representation(self, instance):
        return remove_media(self,instance, GetRolesSerializer,'image')

class GetSoilReportSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return remove_media(self,instance,GetSoilReportSerializer,'soil_report')
    
    class Meta:
        model = SoilReport
        fields = ('soil_report',)
