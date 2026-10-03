from rest_framework import serializers
from . import models
import json
from rest_framework.serializers import Serializer, FileField
from .models import *


class UserSurveySerializer(serializers.ModelSerializer):
    class Meta:
        fields="__all__"
        model= UserSurvey




class SurveySerializer(serializers.ModelSerializer):
    type_name=serializers.SerializerMethodField('get_type_name')
    user_survey=serializers.SerializerMethodField('get_user_survey')
    total_completed=serializers.SerializerMethodField('get_total_completed')
    def get_type_name(self,obj):
        if obj.type:
            return obj.type.name
        else:
            return None        
    
    def get_user_survey(self,obj):
        try:
            return UserSurveySerializer(obj.survey_user.filter(user=self.context['user_id']).last()).data
        except:
            return None
    
    def get_total_completed(self,obj):
        return obj.survey_user.filter(status="accepted").count()

    class Meta:
        model=Survey
        fields=['id','color','link_form','created_by','price','started_at','valid_till','total_allowed','total_completed','description','is_multiple_allowed','status','type_name','user_survey','video_link']

