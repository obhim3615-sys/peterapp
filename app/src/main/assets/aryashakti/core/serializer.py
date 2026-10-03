from rest_framework import serializers
from app_farm.utils.helper import remove_media
from .models import *

class GetCountriesSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return remove_media(self,instance,GetCountriesSerializer,'image')
    
    class Meta:
        model = Country
        fields = ('id','name','code','mobile_code','phone_len','image')

class CustomeFormFieldSerializer(serializers.ModelSerializer):
    """
    Serializer to get the Form Fields.
    """
    class Meta:
        model = CustomFormField
        fields = ('name','type','field_possible_value','is_required')

class CustomFormParentSerializer(serializers.ModelSerializer):
    fields = serializers.SerializerMethodField('get_custom_form_fields')
    def get_custom_form_fields(self,obj):
        return CustomeFormFieldSerializer(obj.custom_form_child.custom_form_fields.filter(status=True).all().order_by('order'),many=True).data
    
    class Meta:
        model = CustomFormParent
        fields = ['id','custom_form_child','fields']
        depth = 1

class GetCustomeFormSerializer(serializers.ModelSerializer):
    """
    Serializer to get the Forms with Fields.
    """
    fields = serializers.SerializerMethodField('get_custom_form_fields')
   
    def get_custom_form_fields(self,obj):
        return CustomeFormFieldSerializer(obj.custom_form_fields.filter(status=True).all().order_by('order'),many=True).data
    
    def to_representation(self, instance):
        return remove_media(self,instance,GetCustomeFormSerializer,'image_url')

    class Meta:
        model = CustomForm
        fields = ('id','name','fields','type','image_url')
        depth = 1
