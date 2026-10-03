from django.shortcuts import render
from rest_framework.views import APIView
from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .models import *
from .serializers import *
from app_farm.utils import constants,response as res
from rest_framework.pagination import PageNumberPagination
from rest_framework import status
import json
from django.db.models import Sum
from app_farm.utils import helper
from django.db import connection,reset_queries

# Create your views here.


class GetUserSurveyData(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 

    def get(self,request):

        completed_survey= UserSurvey.objects.get_user_surveys(request.user.id).filter(status="accepted")
        total_earnings = completed_survey.aggregate(total_earnings=Sum('survey__price'))['total_earnings'] or 0
        total_completed=completed_survey.count()
        total_available= Survey.objects.get_available_survey(request.user.id,request.user.organization_id).count()
        
        return res.req_response("Result Found",True,"",status.HTTP_200_OK,{
            "total_earned":total_earnings,
            "total_completed":total_completed,
            "total_available":total_available
        })

class SurveySubmitView(APIView):
    #  authentication_classes = [CustomTokenAuthentication]
    #  permission_classes = [IsAuthenticated]
     def get(self,request,surveyid):       
             
          survey= Survey.objects.filter(id=surveyid).get()
          survey_fields=[]
          if survey:
              survey_fields=SurveyFields.objects.filter(survey=survey).all()
          return render(
            request,
            'survey_form.html',
            {
                'token':request.GET.get('token'),
                'latitude':request.GET.get('latitude'),
                'longitude':request.GET.get('longitude'),
                'survey':survey,
                'survey_fields':survey_fields,
            }
        )

class CreateSurveyWeb(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 

    def post(self,request):
        latitude=longitude=survey_id=None
        user = request.user  # Assuming you have a way to get the authenticated user
        
        # Create UserSurvey instance and store the response JSON
        survey_id = request.POST.get('survey_id')  # Get the survey ID from the form        
        latitude = request.POST.get('latitude')  # Get latitude from the form        
        longitude = request.POST.get('longitude')  # Get the longitude from the form        
        
        if not survey_id:
            return res.req_response("Survey id not found",False,"SV-CSPOST-01",status.HTTP_400_BAD_REQUEST)

        try:
            survey= Survey.objects.filter(id=survey_id).get()
        except Survey.DoesNotExist:
            return res.req_response("Survey not found",False,"SV-CSPOST-02",status.HTTP_400_BAD_REQUEST)
        response_data = {}
        file_keys=request.POST.getlist('keyfile[]')        
        for field_name, uploaded_files in request.FILES.lists():
            # Handle the uploaded files and get the image URLs
            image_urls = [helper.image_upload(file) for file in uploaded_files]
            response_data[file_keys.pop(0)] = image_urls

        # Process the form submission and extract keys and values
        keys = request.POST.getlist('keys[]')
        values = request.POST.getlist('values[]')
        
        # Create a dictionary to store the response JSON
        
        for key, value in zip(keys, values):
            response_data[key] = value
        if survey.is_multiple_allowed:
            user_survey = UserSurvey.objects.create(
                user=user,
                survey=survey,
                status="pending",
                response=response_data,
                latitude=latitude,
                longitude=longitude
            ) 
        else:
            user_survey = UserSurvey.objects.update_or_create(
                user=user,
                survey=survey,
                defaults={"status":"pending","response":response_data,"latitude":latitude,"longitude":longitude}
            )   
        
        return res.req_response("Survey added",True,"",status.HTTP_201_CREATED)

class CreateSurvey(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 

    def post(self,request):
        latitude=longitude=survey_id=None
        data=json.loads(request.body)
        
        if "survey_id" in data.keys():
            survey_id=data['survey_id']
        if "latitude" in data.keys():        
            latitude = data['latitude']  # Get latitude from the form    
        if "longitude" in data.keys():  
            longitude = data['longitude']  # Get the longitude from the form 
        
        if not survey_id:
            return res.req_response("Survey id not found",False,"SV-CSPOST-01",status.HTTP_400_BAD_REQUEST)

        try:
            survey= Survey.objects.filter(id=survey_id).get()
        except Survey.DoesNotExist:
            return res.req_response("Survey not found",False,"SV-CSPOST-02",status.HTTP_400_BAD_REQUEST)

        if survey.is_multiple_allowed:
            create= UserSurvey.objects.create(user=request.user,survey=survey,status="pending",latitude=latitude,longitude=longitude)
        else:
            create= UserSurvey.objects.update_or_create(user=request.user,survey=survey,defaults={"status":"pending","latitude":latitude,"longitude":longitude})

        return res.req_response("Survey added",True,"",status.HTTP_201_CREATED)
    
class GetSurvey(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 
    # number of items per page by default
    page_size = 50
    # max number of items per page
    max_page_size = 100
    model=Survey

    def get_queryset(self):
        organization= self.request.user.organization_id
        status=self.request.GET.get('status')
        
        queryset = Survey.objects
        if status and status=="available":
            queryset=queryset.get_available_survey(self.request.user.id,organization)
        elif status:            
            queryset=queryset.filter( organization_survey__id=organization,survey_user__status=status,survey_user__user_id=self.request.user.id)
        queryset = queryset.order_by('-id')
        return queryset
 
    def get(self,request):
        queryset = self.get_queryset()      
        page =  self.paginate_queryset(queryset,request)
        
        survey=None
        if page:          
            survey=SurveySerializer(page,many=True,context={'user_id':request.user.id}).data
            survey=self.get_paginated_response(survey).data
        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,survey)