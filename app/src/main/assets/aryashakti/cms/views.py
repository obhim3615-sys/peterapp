from rest_framework.views import APIView
from rest_framework import status
import json

from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from . import validator,serializer
from app_farm.utils.response import req_response
from app_farm.utils.helper import constants,verify_secret_key
from . import models
from core.views import BaseViewWithoutAuthentication, BaseView
from app_farm.models import user,language_master
# Create your views here.
class GetPageDetails(BaseView):
    def get_page_details(self, request, err_code, req_data):
        page = models.Page.objects.filter(id=req_data['page_id']).order_by('order')
        data = serializer.GetPageDetailsSerializer(page, many=True, context={'country_id': req_data['country_id']})

        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data.data)

    def post(self, request):
        return self.common_function(request, 'CV-GPDPOS-', validator.GetPageDetails, self.get_page_details)
        
class GetConfig(BaseViewWithoutAuthentication):    
    def get_config(self, request, err_code, req_data):
        if not verify_secret_key(req_data['key']):
            return req_response(constants.INVALID_KEY, False, err_code+'3', status.HTTP_400_BAD_REQUEST)
        
        config = models.Setting.objects.filter(country=req_data['country_id'])
        data = serializer.GetConfigSerializer(config, many=True)

        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data.data)
        
    def get(self, request):
        return self.common_function(request, 'CV-GCGET-', validator.GetConfigValidator, self.get_config)
        
class GetLanguageContent(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self, request):
        try:
            key = request.GET.get("key")
            language = request.GET.get("language")
            if not key or not verify_secret_key(key):
                return req_response(constants.INVALID_KEY, False, 'CV-GLCGET-1', status.HTTP_400_BAD_REQUEST)
            if not language:
                return req_response(constants.INVALID_BODY, False, 'CV-GLCGET-2', status.HTTP_400_BAD_REQUEST)

            content = models.LanguageContent.objects.get(language=language)
            data = serializer.GetLanguageContentSerializer(content, many=False)

            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, {**data.data['content'],**data.data['crop_content']})
        except Exception as e:
            return req_response(constants.ERROR, False, 'CV-GLCGET-3', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)

    def post(self,request):
        try:
            data = request.data
            language_id= data.get('language_id')
            user_id= data.get('user_id')
            
            try:
                user_data= user.objects.filter(id=user_id).get()
            except user.DoesNotExist:
                return req_response("User not found", False, 'CV-GLCGET-3', status.HTTP_404_NOT_FOUND, None )
            try:
                language= language_master.objects.filter(id=language_id).get()
            except language_master.DoesNotExist:
                return req_response("Language not found", False, 'CV-GLCGET-3', status.HTTP_404_NOT_FOUND, None)

            user_data.language_selected=language
            user_data.save()

            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK,{"user_language":language_id})

        except Exception as e:
            return req_response(constants.ERROR, False, 'CV-GLCGET-3', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)