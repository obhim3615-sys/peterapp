from rest_framework import serializers
from .models import *
from app_farm.utils.helper import remove_media

class SubSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSection
        fields = ('name','image_url','image_text','url','is_iframe')

    def to_representation(self, instance):
        return remove_media(self,instance,SubSectionSerializer,'image_url')


class SectionSerializer(serializers.ModelSerializer):
    sub_sections= serializers.SerializerMethodField('get_sub_sections')

    def get_sub_sections(self,obj):
        return SubSectionSerializer(obj.sub_sections.filter(countries=self.context['country_id']).order_by('order'),many=True).data
    
    class Meta:
        model = Section
        fields = ('name','type','sub_sections')


class GetPageDetailsSerializer(serializers.ModelSerializer):
    sections= serializers.SerializerMethodField('get_sections')

    def get_sections(self,obj):
        return SectionSerializer(
            obj.sections.filter(countries=self.context['country_id']).order_by('order'),
            many=True,
            context={'country_id': self.context['country_id']}
        ).data
   
    class Meta:
        model = Page
        fields = ('id','name','sections')

class GetConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setting
        fields = ('key','value','type')

class GetLanguageContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LanguageContent
        fields = ('content','crop_content',)
