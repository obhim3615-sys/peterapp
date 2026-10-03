from rest_framework import serializers
from .models import*
import json
from rest_framework.serializers import Serializer, FileField
from app_farm.utils.helper import remove_media
from app_farm.utils import helper
from django.urls import reverse
from app_farm.models import user as usermodel


class CertificationSerializer(serializers.ModelSerializer):
    certification_list= serializers.SerializerMethodField('get_certification_list')
    def to_representation(self, instance):
        return remove_media(self,instance,CertificationSerializer,'background')
    
    def get_certification_list(self,obj):
        farmerid=self.context['farmerid']
        return FarmerCertificationSerializerData(obj.certification_data.filter(farmer_id=farmerid),many=True,context=self.context).data
    
    class Meta:
        model= Certification
        fields=['id','name','color','background','certification_list']

class ScoreSerializer(serializers.ModelSerializer):
   

    class Meta:
        model= Score
        fields=['id','name','icon','information']
    
    def to_representation(self, instance):
        return remove_media(self,instance,ScoreSerializer,'icon')


class ScoreFarmerSerializer(serializers.ModelSerializer): 
    score_details=serializers.SerializerMethodField('get_score')
    def get_score(self,obj):
        score=ScoreSerializer(obj.score)
        if score:
            return score.data
        return {}
    class Meta:
        model= ScoreFarmer
        fields=['id','value','score_details']
    

class FarmerCertificationSerializerData(serializers.ModelSerializer):
    score_data=serializers.SerializerMethodField('get_score')
    # graph_url=serializers.SerializerMethodField('get_graph_url')
    def get_score(self,obj):
        score=ScoreFarmerSerializer(obj.certification_farmer_score.all(),many=True)
        if score:
            return score.data
        return []
    
    
    # def get_graph_url(self,obj):
    #     request=self.context['request']
    #     farmerid=self.context['farmerid']
    #     farm=usermodel.objects.filter(id=farmerid).get().created_by30.first()
    #     if farm:
    #         graph_url=helper.replaceHttp(request.build_absolute_uri(reverse('getgraph',args=(farm.id,obj.certification.id))))            
    #     else:
    #         graph_url=""
    #     return graph_url
    
    def to_representation(self, instance):
        return remove_media(self,instance,FarmerCertificationSerializerData,'file_url')
    
    class Meta:
        model= FarmerCertification
        fields=['id','farmer','certification','file_url','score_data','expiry_date','issued_date','is_approved']


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model= Badge
        fields="__all__"
    def to_representation(self, instance):
        return remove_media(self,instance,BadgeSerializer,'icon')

class FarmerBadgeSerializer(serializers.ModelSerializer):
    badge_details= serializers.SerializerMethodField('get_badge_details')
  
    def get_badge_details(self,obj):
        return BadgeSerializer(obj.badge).data
    
    
    class Meta:
        model= FarmerBadge
        fields=['id','farmer','badge_details']


class GraphHistorySerializer(serializers.ModelSerializer):
    certification_name= serializers.SerializerMethodField('get_certification_name')
    type_name= serializers.SerializerMethodField('get_type_name')

    def get_certification_name(self,obj):
        return obj.type.certificate.name
    
    def get_type_name(self,obj):
        return obj.type.name
    
    class Meta:
        model= GraphHistory
        fields=['id','value','date','type','farm','type_name','certification_name']

