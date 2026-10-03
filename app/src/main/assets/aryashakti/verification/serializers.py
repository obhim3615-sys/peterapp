from rest_framework import serializers
from . import models
import json
from rest_framework.serializers import Serializer, FileField



class Documenterializer(serializers.ModelSerializer):
    is_verified = serializers.SerializerMethodField('get_is_verified')

    def get_is_verified(self,obj):
        return obj.is_verified

    class Meta:
        model = models.Document
        fields = ('id','name','status','is_verified','is_required')
        depth=1


class UnsecureLoanStepSerializer(serializers.ModelSerializer):
    is_completed = serializers.SerializerMethodField('get_is_completed')
    def get_is_completed(self,obj):
        return obj.is_completed
    class Meta:
        model = models.UnsecureLoanStep
        fields = ('id','name','status','is_completed','is_required','link_url','is_iframe')


class OrganizationConsolidationDirectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.OrganizationConsolidationDirector
        fields="__all__"

class PanSerializer(serializers.ModelSerializer):
    directors_data= serializers.SerializerMethodField('get_directors')

    def get_directors(self,obj):
        return OrganizationConsolidationDirectorSerializer(obj.directors.all(),many=True).data
   
    class Meta:
        model = models.PanVerifcation
        fields=['id','pan_number','address','state','pincode','leadId','email','pan_dob','pan_name','father_name','response_details','user','directors_data']

    


class AdharSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = models.AdharVerifcation
        fields="__all__"

class GSTSerializer(serializers.ModelSerializer):
  
    class Meta:
        model = models.GSTData
        fields="__all__"



class TemplateDataSerializer(serializers.ModelSerializer):
    template_upload= serializers.SerializerMethodField('get_template_upload')

    def get_template_upload(self,obj):
        org= self.context['org']
        try:
            template= obj.template_organization.filter(organization_id=org).get()
        except Exception as e:
            template=None
        if template:
            return True
        
        return False

    class Meta:
        model = models.TemplateData
        fields=['id','template_name','type','body','template_upload']


class OrganizationKeyDataSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = models.OrganizationKeyValues
        fields="__all__"


