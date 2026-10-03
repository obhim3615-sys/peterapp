from rest_framework import serializers

from . import models
from app_farm.utils.helper import remove_media

class SmsTemplateFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SmsTemplateField
        fields = ('name','type','field_possible_value','is_required','key')

class GetSmsTemplateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SmsTemplate
        fields = ('id','name','image','emoji','doms_id','description')

    def to_representation(self, instance):
        return remove_media(self,instance,GetSmsTemplateListSerializer,'image')
    
class GetSmsTemplateDetailSerializer(serializers.ModelSerializer):
    fields = serializers.SerializerMethodField('get_template_fields')

    def get_template_fields(self,obj):
        return SmsTemplateFieldSerializer(obj.template_fields.filter(status=True).all().order_by('order'),many=True).data
    
    class Meta:
        model = models.SmsTemplate
        fields = ('msg','template_id','fields','doms_id')


class CommunitiesShareSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return remove_media(self,instance,CommunitiesShareSerializer,'image')
    
    class Meta:
        model=models.CommunitiesShare
        fields="__all__"