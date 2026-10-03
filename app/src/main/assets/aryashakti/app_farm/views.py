from rest_framework import generics
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from . import models
from django.db.models import Sum,Prefetch,Subquery,Q
from decimal import Decimal
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from . import serializers, validators
from rest_framework.validators import ValidationError
from datetime import timedelta
from rest_framework import status
from django.shortcuts import get_object_or_404
from urllib.parse import unquote
import json
import re
import urllib.request
import ast
import ssl
from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.core.files.storage import default_storage
import basehash
#from Crypto.Cipher import AES
import base64
import hashlib
from decimal import Decimal
import datetime
from itertools import chain
import os
#from azure.storage.blob import BlobServiceClient, BlobClient,ContainerClient
from rest_framework.viewsets import ViewSet
import requests
import json
import re
from django.utils import timezone
from app_farm.utils import constants,response as res
import random
import math
from dateutil import parser
# Helper functions
from .utils import constants,helper
from django.contrib.gis.geos import Point
from app_farm.utils.queries_lib import getDistanceValidation
from django.db.models import Avg,Count
from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from app_farm.utils.mixin.subscription import SubscriptionRequiredMixin
from libraries.push_notification import FirebaseHelper
from itertools import islice
from libraries.video_ms import VideoMS
from rest_framework.pagination import PageNumberPagination

from libraries.noms import NoMS 

hash_fn = basehash.base36()

class Addcomment_reporting(generics.CreateAPIView):
    serializer_class = serializers.comment_reportingSerializer
    queryset = models.comment_reporting.objects.all()

class Addcommunity_post_reporting(generics.CreateAPIView):
    serializer_class = serializers.community_post_reportingSerializer
    queryset = models.community_post_reporting.objects.all()

class Adduser_reporting(generics.CreateAPIView):
    serializer_class = serializers.adduser_reportingSerializer
    queryset = models.user_reporting.objects.all()

class AddInquiry(generics.CreateAPIView):
    serializer_class = serializers.aryadhan_inquirySerializer
    queryset = models.aryadhan_inquiry.objects.all()

class AddOfferInquiry(generics.CreateAPIView):
    serializer_class = serializers.offer_inquirySerializer
    queryset = models.offer_inquiry.objects.all()

class SignUp(generics.CreateAPIView):
    serializer_class = serializers.signuperializer
    queryset = models.user.objects.all()

class AddAgent(generics.CreateAPIView):
    serializer_class = serializers.addagentSerializer
    queryset = models.agents.objects.all()

class AddSocialPost(generics.CreateAPIView):
    serializer_class = serializers.addsocialSerializer
    queryset = models.social_post.objects.all()


class GetSocialPostTagList(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=models.SocialPostTag   

    def get_queryset(self):
        queryset= models.SocialPostTag.objects.filter(status=True).all()  

        return queryset
        

    def get(self,request):
        queryset = self.get_queryset()      
        page =  self.paginate_queryset(queryset,request)

        social_post_tag=None
        if page:          
            social_post_tag=serializers.SocialPostTagSerializer(page,many=True).data
            social_post_tag=self.get_paginated_response(social_post_tag).data
        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,social_post_tag)
    
class AddFarm(generics.CreateAPIView):
    serializer_class = serializers.farmaddSerializer
    


class AddMachine(generics.CreateAPIView):
    serializer_class = serializers.machineSerializer
    
class AddSellCrop(generics.CreateAPIView):
    serializer_class = serializers.sellcropaddSerializer
    
class AddDeliveryAddress(generics.CreateAPIView):
    serializer_class = serializers.adddeliveryaddress
    
class AddOrder(generics.CreateAPIView):
    # def form_valid(self, form):
    #     form.instance.user = self.request.user
    #     return super(TodoView, self).form_valid(form)
    # noti=models.notification(user_id=7, title= 'Your Order Have been Placed', desc= "Your Amount is")
    # noti.save()
    serializer_class = serializers.addorderlistSerializer
   
class AddNotification(generics.CreateAPIView):
    serializer_class=serializers.addnotificationSerializer
    
class AddOrderDetails(generics.CreateAPIView):
    serializer_class = serializers.addorderdetailsSerializer
    
class Addcompliance(generics.CreateAPIView):

    serializer_class = serializers.complianceSerializer    
    
    def perform_create(self, serializer):
        # Create
        instance = serializer.save()
        
        if instance.document_name == "aadhaarProofDocument":
            helper.addVerification(instance.user_id,settings.SIGNZY_ADHAR_DOC_ID,instance.id,"verification_adharuser_request")            
        elif instance.document_name == "bankStatement":
            helper.addVerification(instance.user_id,settings.ONEMONEY_DOCUMENT_ID,instance.id,"verification_adharuser_request")
        elif instance.document_name == 'businessPAN':
            helper.addVerification(instance.user_id,settings.SIGNZY_PAN_DOC_ID,instance.id,"verification_adharuser_request")
        elif instance.document_name == 'gstProof':
            helper.addVerification(instance.user_id,settings.SIGNZY_GST_DOC_ID,instance.id,"verification_adharuser_request")

        helper.updateDocumentStep(instance.user_id)

    

'''
class AddMachine(generics.CreateAPIView):
    serializer_class=serializers.machineSerializer
    queryset=models.machine_master.objects.all()
'''

class AddImplement(generics.CreateAPIView):
    serializer_class=serializers.implementSerializer
   
class AddChemical(generics.CreateAPIView):
    serializer_class=serializers.chemicalSerializer
    
class AddSeed(generics.CreateAPIView):
    serializer_class=serializers.seedSerializer
    
class AddLiveFeed(generics.CreateAPIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 
    serializer_class = serializers.addlivefeedSerializer
    
    def filter_letters(self,input_string):
        # Use a regular expression to filter only letters
        letters_only = re.sub(r'[^a-zA-Z]', '', input_string)
        return letters_only

    def perform_create(self, serializer):
        user = self.request.user  
        org=self.request.user.organization
        organization = org.id
        
        if not org.room_100ms:
            video= VideoMS()
            data=video.create_room(self.filter_letters(org.org_name),"")
            # print(data)
            if 'id' not in data.keys():
                raise ValueError("Room could not be created")
            code_video=video.createCode(data['id'])
            if 'data' not in code_video.keys():
                raise ValueError("Url could not be created")
            host=code_video['data'][1]['code']
            guest=code_video['data'][0]['code']
            models.organizations.objects.filter(id=organization).update(room_100ms=data['id'],room_hostcode=host,room_guestcode=guest)
        # Check if a live_feed already exists for the organization
        existing_live_feed = models.live_feed.objects.filter(org_id=organization).first()

        if existing_live_feed:
             # Modify the validated data to update the 'status' field
            serializer.validated_data['status'] = 'Active'
            # Update the existing live_feed object            
            serializer.update(existing_live_feed, serializer.validated_data)    
            serializer.save()       
            
        else:
            # Create a new live_feed object
            serializer.save()   
        
        

        tokens = models.user.objects.filter(organization=user.organization_id,firebase_token__isnull=False).distinct().values_list('firebase_token', flat=True)
        firebasehelper=FirebaseHelper(True)
        # Convert the queryset to a list
        tokens_list = list(tokens)
        # Define the batch size
        batch_size = 500
        # Split the list of tokens into batches
        token_batches = [tokens_list[i:i + batch_size] for i in range(0, len(tokens_list), batch_size)]

        for batch in token_batches:
            # Send notifications for each batch of tokens
            firebasehelper.send_push_notification(
                list(batch),
                self.request.user.organization.org_name + " admin is Live",
                "Click here to Join",
                "ggnotisound.mp3",
                {"url": serializer.data["url"]}
            )

        firebasehelper.send_push_notification(list(tokens),self.request.user.organization.org_name+" admin is Live","Click here to Join","ggnotisound.mp3",{"url":serializer.data["url"]})
        # Return the response
        return Response(serializer.data)
        


class AddInputCatalogue(generics.CreateAPIView):
    serializer_class = serializers.addinputcatalogueSerializer
   
class AddFarmerRequest(generics.CreateAPIView):
    serializer_class = serializers.addfarmer_requestSerializer
   
from farm_category.models import WarehousePincodeLocation
from django.db.models import F, FloatField
from django.db.models.functions import ACos, Cos, Sin, Radians

def find_pincode_by_latlong(lat, lon):
    lat = float(lat)
    lon = float(lon)

    return (
        WarehousePincodeLocation.objects
        .exclude(latitude__isnull=True)
        .exclude(longitude__isnull=True)
        .annotate(
            distance=(
                ACos(
                    Cos(Radians(lat)) *
                    Cos(Radians(F("latitude"))) *
                    Cos(Radians(F("longitude")) - Radians(lon)) +
                    Sin(Radians(lat)) *
                    Sin(Radians(F("latitude")))
                ,
                output_field=FloatField()
                ) * 6371.0
            )
        )
        .order_by("distance")
        .first()
    )
class add_farmer(APIView):
    """
    Function to create a new farmer and it's farm.
    """
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_extra_actions(cls):
        return []
    def post(self, request):
        from survey.models import Survey
        try:
            if request.data.get('data') == None:
                response = {'status_code': status.HTTP_400_BAD_REQUEST, 'status': False, 'message': constants.EMPTY_REQ_BODY }
                return Response(response, status=response['status_code'])

            body_data = request.data['data']
            
            if type(body_data) == str:
                body_data = json.loads(body_data)
            validation = validators.AddFarmDataValidator(data=body_data)

            if validation.is_valid():
                survey = None
                if body_data.get('survey_id'):
                    try:
                        survey = Survey.objects.get(id=body_data['survey_id'])
                    except ObjectDoesNotExist:
                        response = {'status_code': status.HTTP_400_BAD_REQUEST, 'status': False, 'message': constants.SURVEY_NOT_FOUND }
                        return Response(response, status=response['status_code'])
                
                if body_data['country_id'] != settings.IDS_COUNTRY_INDIA:   # Condition to get hardcode address for kenya like countries.
                    address_data = helper.kenya_address
                else:
                    lat = body_data.get('lat')
                    long = body_data.get('long')
                    nearest = find_pincode_by_latlong(lat, long)
                    if not nearest:
                        response = {'status_code': status.HTTP_400_BAD_REQUEST, 'status': False, 'message': 'Pincode location not found' }
                        return Response(response, status=response['status_code'])
                    # print("nearest")
                    # address_data=helper.get_address_from_pincode(nearest.pin_code)
                    address_data={"country":"India",
                                  "district":nearest.district,
                                  "state":nearest.state,
                                  "pincode":nearest.pin_code,
                                  "village": nearest.office_name.strip() if nearest.office_name else None}
                    
                
                try:
                    # I have done this way, because in future there will be functionality of adding farm to the existing user.
                    user = models.user.objects.only("id", "mobile_number", "organization").get(mobile_number= body_data['mobile_number'])
                    # print("existing user data")
                    if user.organization != request.user.organization:
                        response= {'status_code': status.HTTP_400_BAD_REQUEST, 'status': False, 'message': "User with mobile number already exist in other organization with name: "+user.organization.org_name }
                        return Response(response, status=response['status_code'])
                    if survey:
                        # Code for adding farm from survey.
                        with transaction.atomic():
                            user_survey = add_user_survey(request.user, survey)
                            response = add_farm(request.user, user, user_survey, body_data, address_data, request.data.get('image'))
                    else:
                        response = add_farm(request.user, user, None, body_data, address_data, request.data.get('image'),True)
                    return Response(response, status=response['status_code'])
                except ObjectDoesNotExist:
                    # Fetch the address details.
                    # print("user doesn't exist")
                    
                    # Create the user.
                    with transaction.atomic():
                        user = models.user.objects.create(
                            language_selected = request.user.language_selected,
                            mobile_number = body_data['mobile_number'],
                            organization = request.user.organization,
                            otp_verfied = False,
                            full_name = body_data['name'],
                            # full_name_telugu = helper.translate_text('en', 'hi', body_data['name']),
                            land_size = body_data.get('land_size'),
                            land_size_unit = body_data.get('land_size_unit'),
                            # land_size_unit_telugu = utils.area_unit_dict[body_data['land_size_unit']],
                            address_pincode = address_data.get('pincode'),
                            address_country = address_data.get('country'),
                            address_state = address_data.get('state'),
                            address_district = address_data.get('district'),
                            address_taluka = address_data.get('taluka'),
                            address_village = address_data.get('village'),
                            added_by = request.user,
                            country_id = body_data['country_id']
                        )
                        # print("user created")

                        user.crops_interest.add(body_data['crop_id'])

                        # Code for adding farm from survey.
                        user_survey = None
                        if survey:
                            user_survey = add_user_survey(request.user, survey)

                        response = add_farm(request.user, user, user_survey, body_data, address_data, request.data.get('image'))
                        return Response(response, status=response['status_code'])
            else:
                response = {'status_code': status.HTTP_400_BAD_REQUEST, 'status': False, 'message': constants.INVALID_BODY, 'data': validation.errors }
                return Response(response, status=response['status_code'])
        except Exception as e:
            print("Error is-01:: ",str(e))
            response = {'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR, 'status': False, 'message': constants.FARM_CREATION_ERR }
            return Response(response, status=response['status_code'])

def add_farm(added_by, user, user_survey, body_data, address_data, image, without_transaction=False):
    """
    Function to add farm for the farmer/user.
    """
    print("adding farm now")
 
    lat = body_data.get('lat')
    long = body_data.get('long')

    if (lat and long and not getDistanceValidation(lat,long)):

        if not without_transaction:
            transaction.set_rollback(True)

        return {'status_code': status.HTTP_400_BAD_REQUEST, 'status': False, 'message': constants.LOCATION_ALREADY_EXIST }
    if lat and long:
        timestamp_lat_long=timezone.now()
    else:
        timestamp_lat_long=None

    point_value = Point(float(long) if long else None, float(lat) if lat else None, srid=4326)

    crop_id = models.crop_master.objects.get(id=body_data['crop_id'])


    image_url = None


    exists = models.farm.objects.filter(
        farmer_contact=body_data['mobile_number']
    ).exclude(org_id=user.organization).exists()

    if exists:
        return {'status_code': status.HTTP_400_BAD_REQUEST, 'status': False, 'message': "Farm with mobile number already exist in other organization" }


    if  image :
        # print("adding image")
        image_url = helper.image_upload(image)

    variety_id=body_data.get('variety_id')
    if body_data.get('variety_name') and not variety_id:
        variety_name=body_data.get('variety_name')
        crop_variety=models.crop_variety_master.objects.create(crop_id=crop_id,crop_variety=variety_name)
        variety_id= crop_variety.id


    farm_data = models.farm.objects.create(
        user = user,
        added_by = added_by,
        name = body_data['name'],
        # name_telugu = helper.translate_text('en', 'hi', body_data['name']),
        stage = 'Vegetative',
        stage_telugu = 'वनस्पतिक',
        total_area = body_data.get('land_size'),
        area_unit = body_data.get('land_size_unit'),
        sowing_date = body_data.get('sowing_date'),
        # area_unit_telugu = utils.area_unit_dict[body_data['land_size_unit']],
        crop_id = crop_id,
        crop_variety_id_id=variety_id,   #body_data.get('variety_id'),
        org_id = user.organization,
        khasra_no = body_data.get('khasra_no'),
        latitude = lat,
        longitude = long,
        is_location = True if body_data.get('lat') and body_data.get('long') else False,
        farm_country = address_data['country'] if address_data.get('country') else 'India',
        farm_state = address_data.get('state'),
        # farm_state_hindi = helper.translate_text('en', 'hi', address_data['state']),
        farm_district = address_data.get('district'),
        # farm_district_hindi = helper.translate_text('en', 'hi', address_data['district']),
        farm_taluka = address_data.get('taluka'),
        # farm_taluka_hindi = helper.translate_text('en', 'hi', address_data['taluka']),
        farm_village = address_data.get('village'),
        # farm_village_hindi = helper.translate_text('en', 'hi', address_data['village']),
        farm_img = image_url,
        farmer_contact = body_data['mobile_number'],
        geometry=point_value,
        user_survey = user_survey,
        timestamp_lat_long = timestamp_lat_long,
    )

    if body_data.get('otherCrop'):
        crop_list=body_data.get('otherCrop')
        for i in crop_list:
            models.farmCropMaster.objects.create(
                crop_id=i,
                farm=farm_data

            )
    return { 'status_code': status.HTTP_201_CREATED, 'status': True, 'message': constants.FARM_CREATION_SUCCESS, 'data': {
        'name': user.full_name,
        'id': user.id,
        'phone': user.mobile_number,
        'country_code': user.country.mobile_code,
        'img': user.user_profile_img,
        'farm_id':farm_data.id
    }}

def add_user_survey(user, survey):
    """
    Function to add User Survey.
    """
    from survey.models import UserSurvey
    try:
        user_survey = UserSurvey.objects.create(
            user = user,
            survey = survey,
        )
        return user_survey
    except ObjectDoesNotExist:
        return None

class notification_view(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
                #group_id = request.GET.get("group_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                # print(datetime.datetime.now()-timedelta(days=30))

                qs = models.notification.objects.filter(user_id= user_id ).distinct()
                s1 = serializers.notificationSerializer(qs, many=True)
                # print(s1.data)
                qs1 = models.notification.objects.filter(group= 0 ).distinct()
                s2 = serializers.notificationSerializer(qs, many=True)
                # print(s2.data)
                serializer = serializers.notificationSerializer((qs|qs1).distinct(), many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class mobile_view(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :

                qs = models.user.objects.filter(id= user_id ).distinct()
                s1 = serializers.mobserializer(qs, many=True)

                if len(s1.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':s1.data }
                if len(s1.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':s1.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class order_view(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.order.objects.filter(user_id=user_id).distinct()
                serializer = serializers.orderSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])
        


class myplot_view(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.farm.objects.filter(user_id=user_id).distinct()
                serializer = serializers.myplotSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class farm_list_featured(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        org_id  = request.GET.get("org_id")
        key = request.GET.get("secret-key")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            qs = models.farm.objects.filter(org_id=org_id,featured=True).distinct()
            serializer = serializers.farmlistSerializer(qs, many=True)
            if len(serializer.data) != 0  :
                response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
            if len(serializer.data) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
            return Response(response, status=response['status'])

        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
            return Response(response, status=response['status'])

        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])

class farm_list_admin(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        org_id  = request.GET.get("org_id")
        key = request.GET.get("secret-key")
        stressed = request.GET.get("stressed")
        healthy = request.GET.get("healthy")
        state1 = request.GET.get("state")
        district1 = request.GET.get("district")
        taluka1 = request.GET.get("taluka")
        village1 = request.GET.get("village")
        crop_id1 = request.GET.get("crop-id")
        sort_by = request.GET.get("sort_by") #0 for name ascending , 1 for name descending , 2 for acre descending , 3  for acre ascending , 4 for
        search_by_name = request.GET.get("search-by-name")
        added_by = request.GET.get("added_by")

        search_by_user_name= request.GET.get("search_by_user_name")

        filter_kwargs = {'org_id': org_id}
        if search_by_name is not None:
            filter_kwargs['name__istartswith'] = search_by_name
        if search_by_user_name is not None:
            filter_kwargs['user__full_name__istartswith'] = search_by_user_name
        if stressed is not None:
            if stressed == '1':
                filter_kwargs['stressed'] = True
            elif stressed == '0':
                filter_kwargs['stressed'] = False
        if healthy is not None:
            if healthy == '1':
                filter_kwargs['healthy'] = True
            elif healthy == '0':
                filter_kwargs['healthy'] = False
        if state1 is not None:
            filter_kwargs['farm_state'] = state1
        if district1 is not None:
            filter_kwargs['farm_district'] = district1
        if taluka1 is not None:
            filter_kwargs['farm_taluka'] = taluka1
        if village1 is not None:
            filter_kwargs['farm_village'] = village1
        if crop_id1 is not None:
            c1 = crop_id1.split(";")
            filter_kwargs['crop_id__in'] = [i for i in c1 if i]
        if added_by:
            filter_kwargs['user__added_by_id'] = added_by

        ordering = ['featured']
        if sort_by is not None:
            if sort_by == '0':
                ordering.append('name')
            if sort_by == '1':
                ordering.append('-name')
            if sort_by == '2':
                ordering.append('total_area')
            if sort_by == '3':
                ordering.append('-total_area')

        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            qs = models.farm.objects.filter(**filter_kwargs).order_by(*ordering)
                #qs = models.farm.objects.filter(org_id=org_id).distinct()
            serializer = serializers.farmlistSerializer(qs, many=True)
            if len(serializer.data) != 0  :
                response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
            if len(serializer.data) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content' }
            return Response(response, status=response['status'])

        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
            return Response(response, status=response['status'])

        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])

class farm_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            stressed = request.GET.get("stressed")
            healthy = request.GET.get("healthy")
            state1 = request.GET.get("state")
            district1 = request.GET.get("district")
            taluka1 = request.GET.get("taluka")
            village1 = request.GET.get("village")
            crop_id1 = request.GET.get("crop-id")
            sort_by = request.GET.get("sort_by") #0 for name ascending , 1 for name descending , 2 for acre descending , 3  for acre ascending , 4 for
            search_by_name = request.GET.get("search-by-name")
            search_by_user_name = request.GET.get("search_by_user_name")

            filter_kwargs = {'user_id': user_id}
            if search_by_user_name is not None:
                filter_kwargs['user__full_name__istartswith'] = search_by_user_name
            if search_by_name is not None:
                filter_kwargs['name__istartswith'] = search_by_name
            if stressed is not None:
                if stressed == '1':
                    filter_kwargs['stressed'] = True
                elif stressed == '0':
                    filter_kwargs['stressed'] = False
            if healthy is not None:
                if healthy == '1':
                    filter_kwargs['healthy'] = True
                elif healthy == '0':
                    filter_kwargs['healthy'] = False
            if state1 is not None:
                filter_kwargs['farm_state'] = state1
            if district1 is not None:
                filter_kwargs['farm_district'] = district1
            if taluka1 is not None:
                filter_kwargs['farm_taluka'] = taluka1
            if village1 is not None:
                filter_kwargs['farm_village'] = village1
            if crop_id1 is not None:
                c1 = crop_id1.split(";")
                filter_kwargs['crop_id__in'] = [i for i in c1 if i]

            ordering = ['featured']
            if sort_by is not None:
                if sort_by == '0':
                    ordering.append('name')
                if sort_by == '1':
                    ordering.append('-name')
                if sort_by == '2':
                    ordering.append('total_area')
                if sort_by == '3':
                    ordering.append('-total_area')


            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.farm.objects.filter(**filter_kwargs).order_by(*ordering).distinct()[start:end]
                #qs = models.farm.objects.filter(user_id=user_id).distinct()
                serializer = serializers.farmlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :

                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])


class sellcrop_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.sell_crop.objects.filter(user_id=user_id).distinct()
                serializer = serializers.sell_croplistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class sellcrop_admin_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            org_id  = request.GET.get("org_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.sell_crop.objects.filter(org_id=org_id).distinct()
                serializer = serializers.sell_croplistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])



class get_machine_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
        #user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.machine_master.objects.all().distinct()
                serializer = serializers.machineSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class get_implement_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        #user_id  = request.GET.get("user_id")
        key = request.GET.get("secret-key")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)

        if len(serializer1.data) != 0 :
            qs = models.implement_master.objects.all().distinct()
            serializer = serializers.implementSerializer(qs, many=True)
            if len(serializer.data) != 0  :
                response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
            if len(serializer.data) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
            return Response(response, status=response['status'])

        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
            return Response(response, status=response['status'])

        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])


class crop_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.crop_master.objects.all().distinct()
                serializer = serializers.croplistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class crop_list_org(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            org_id  = request.GET.get("org_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.organizations.objects.all().distinct()
                serializer = serializers.croplistorgSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])


class offers_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            org_id  = request.GET.get("org-id")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.offers.objects.filter(status='Active',org_id=org_id).distinct()
                serializer = serializers.offerlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class offer_details(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            offer_id  = request.GET.get("offer_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.offers.objects.filter(id=offer_id).distinct()
                serializer = serializers.offerdetailsSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class training_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            org_id  = request.GET.get("org-id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.training.objects.filter(status='Active',org_id=org_id).distinct()
                serializer = serializers.traininglistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class training_details(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            training_id  = request.GET.get("training_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.training.objects.filter(id=training_id).distinct()
                serializer = serializers.trainingdetailsSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class variety_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            crop_id  = request.GET.get("crop_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.crop_variety_master.objects.filter(crop_id=crop_id).distinct()
                serializer = serializers.varietylistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class existing_user(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            mobile_number = request.GET.get("mobile_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.user.objects.filter(mobile_number=mobile_number).distinct()
                serializer = serializers.existinguserSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'existing','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_200_OK,'message':'new user','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])



class ImageUpload(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def post(self, request):
        try:
            image = request.data.get("image")
            if not image:
                return Response(
                    {"error": "Image field is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            is_private = request.data["is_private"]
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                if is_private and is_private==True:
                    image_url=helper.private_image_upload(image,"documents/other/")
                else:
                    image_url=helper.image_upload(image)
                response = {'status': status.HTTP_200_OK, 'message': 'success', 'image_url': image_url}
                return Response(response, status=response['status'])
            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message': 'error' }
            return Response(response, status=response['status'])
        
class UploadViewSet(APIView):
    serializer_class = serializers.UploadSerializer

    def list(self, request):
        return Response("GET API")

    def post(self, request):
        response = "This api is deprecated"
        return Response(response)

class product_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            category  = request.GET.get("category")
            sub_category = request.GET.get("sub_category")
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10
                    end = start+10
                    #brand_id = request.GET.get("brand_id")
                    #crop_id = request.GET.get("crop_id")
                    \
                qs = models.product_master.objects.filter(status='Active',category_a=category,sub_category=sub_category).distinct()[start:end]
                tot = models.product_master.objects.filter(status='Active',category_a=category,sub_category=sub_category).distinct().count()
                # print(tot)
                serializer = serializers.productlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data ,'tot':tot}

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message': 'error' }

            return Response(response, status=response['status'])



class popular_product_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:

        #brand_id = request.GET.get("brand_id")
        #crop_id = request.GET.get("crop_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.product_master.objects.filter(popular=True).distinct()
                serializer = serializers.productlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message': 'error' }

            return Response(response, status=response['status'])

class product_details(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            product_id  = request.GET.get("product_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.product_variants.objects.filter(product_id=product_id).distinct()
                serializer = serializers.productdetailsSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message': 'error' }

            return Response(response, status=response['status'])

class product_variant_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.product_variants.objects.all().distinct()
                serializer = serializers.productvariantlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message': 'error' }

            return Response(response, status=response['status'])

class address_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:

            user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.delivery_address.objects.filter(user_id=user_id).distinct()
                serializer = serializers.deliveryaddresslist(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message': 'error' }

            return Response(response, status=response['status'])

class delete_address(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            address_id = request.GET.get("address_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.delivery_address.objects.filter(id=address_id).delete()
                if qs[0] != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success' }
                else :
                    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid ID'}

                return Response(response, status=response['status'])
            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Invalid Secret Key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request '}
            return Response(response, status=response['status'])

class news_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        #user_id  = request.GET.get("user_id")
        key = request.GET.get("secret-key")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        last_updated_time = request.GET.get("last_updated_time")
        last_updated_time = int(last_updated_time) if last_updated_time is not  None else 0
        org_id = request.GET.get("org-id")
        try:
            if len(serializer1.data) != 0 :
                qs = models.news.objects.filter(status='Active',org_id=org_id).order_by('-timestamp').distinct()[:20]
                serializer = serializers.newslistSerializer(qs, many=True)
            
                if last_updated_time is not None and last_updated_time !=0:
                    result = list()
                    fms = ['%Y-%m-%dT%H:%M:%S.%fZ','%Y-%m-%dT%H:%M:%SZ' ]
                    for news in serializer.data:
                        for fm in fms:
                            try:
                                dt = datetime.datetime.strptime(news["timestamp"], fm)
                            except ValueError:
                                pass
                            if dt is None :
                                raise Exception("Invalid date format specified:" )
                            
                    #dt = datetime.datetime.strptime(news["timestamp"], '%Y-%m-%dT%H:%M:%SZ')
                        ts = int((dt - datetime.datetime(1970,1,1)).total_seconds() * 1000)
                    
                        if ts > last_updated_time:
                            result.append(news)
                    response = {'status': status.HTTP_200_OK,'message':'successfully','data': result}
                else:
                    response = {'status': status.HTTP_200_OK,'message':'successfully','data':serializer.data }

            # if len(serializer.data) != 0  :
            #     response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

            # if len(serializer.data) == 0  :
            #     response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Invalid Secret Key'}
                return Response(response, status=response['status'])

        except Exception as e:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Error occurred: %s' %e.message}
            return Response(response, status=response['status'])

class news_details(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            news_id  = request.GET.get("news_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.news.objects.filter(id=news_id).distinct()
                serializer = serializers.newsdetailsSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Invalid Secret Key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request '}
            return Response(response, status=response['status'])

class tracking_view(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            order_id  = request.GET.get("order_id")
            key = request.GET.get("secret-key")

            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.tracking.objects.filter(order_id=order_id).distinct()
                serializer = serializers.trackingSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Invalid Secret Key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request '}
            return Response(response, status=response['status'])

class order_details(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            order_id  = request.GET.get("order_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.order_details.objects.filter(order_id=order_id).distinct()
                serializer = serializers.orderDetailsSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Invalid Secret Key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])

class carousel_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            key = request.GET.get("secret-key")
            user_id = request.GET.get("user-id")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.carousel.objects.filter(user=user_id).distinct().order_by('index')
                serializer = serializers.carousellistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                        #if len(serializer.data) == 0  :
                            #response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                    return Response(response, status=response['status'])
                else:
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content' }

                        #if len(serializer.data) == 0  :
                            #response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                    return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])

class carousel_list_admin(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            key = request.GET.get("secret-key")
            user_id = request.GET.get("org-id")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.organizations.objects.filter(id=user_id).distinct()
                serializer = serializers.carousellistAdminSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                        #if len(serializer.data) == 0  :
                            #response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                    return Response(response, status=response['status'])
                else:
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content' }

                        #if len(serializer.data) == 0  :
                            #response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                    return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])

class hashtag_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
        #user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.hashtag_master.objects.all().distinct()
                serializer = serializers.hastaglistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])

class social_list(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            org_id = request.GET.get("org_id")
            
            if request.user.user_role.role_name != constants.SLUGS['USER_ROLES']['SPONSOR'] and not org_id:
                return res.req_response(constants.INVALID_BODY, False, 'AFV-SLGET-1', status.HTTP_400_BAD_REQUEST)
            
            # Get the blocked users
            blocked_users = list(models.user_reporting.objects.filter(blocked_by_user=request.user.id,block=True).distinct().values_list('id', flat=True))
            
            if request.user.user_role.role_name == constants.SLUGS['USER_ROLES']['SPONSOR']:
                # Get the users sponsored by this sponsor
                sponsored_users = list(models.user.objects.filter(user_subscription__sponsored_by_id=request.user.id).distinct().values_list('id', flat=True))
                qs = models.social_post.objects.filter(approved=True,user_id__in=sponsored_users,status='Active').exclude(user_id__in=blocked_users).distinct().order_by('-timestamp')
            else:
                qs = models.social_post.objects.filter(approved=True,org_id=org_id,status='Active').exclude(user_id__in=blocked_users).distinct().order_by('-timestamp')

            serializer = serializers.sociallistSerializer(qs, many=True)
            if len(serializer.data) == 0:
                return res.req_response(constants.NO_CONTENT, True, '', status.HTTP_204_NO_CONTENT, serializer.data)
            return res.req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, serializer.data)
        except Exception as e:
            return res.req_response(constants.ERROR, False, 'AFV-SLGET-2', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)



class SellRecordsAPI(APIView, PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    page_size = 25
    max_page_size = 100

    def get_queryset(self, request):
        """
        Define the queryset for the SellRecords model.
        """
        return models.SellRecords.objects.filter(user_added=request.user).order_by('-date_time')

    def get(self, request):
        """
        Handle GET requests with pagination.
        """
        try:
            queryset = self.get_queryset(request)
            page = self.paginate_queryset(queryset, request, view=self)
            if page is not None:
                serializer = serializers.SellRecordsSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = serializers.SellRecordsSerializer(queryset, many=True)
            return res.req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, serializer.data)

        except Exception as e:
            return res.req_response(constants.ERROR, False, 'AFV-SRGET-2', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)

    def post(self, request):
        """
        Handle POST requests for creating a new SellRecord.
        """
        try:
            data=request.data
            data['user_added']=request.user.id
            serializer = serializers.SellRecordsSerializer(data=data)
            if serializer.is_valid():
                serializer.save(user_added=request.user)
                return res.req_response("Record created", True, '', status.HTTP_201_CREATED, serializer.data)
            
            return res.req_response(constants.ERROR, False, 'AFV-SLPOST-2', status.HTTP_400_BAD_REQUEST, None, serializer.errors)

        except Exception as e:
            return res.req_response(constants.ERROR, False, 'AFV-SRPOST-1', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)
            

class social_list_paginated(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=models.social_post

    def get_queryset(self,request,org_id,blocked_users,tag):
        if request.user.user_role.role_name == constants.SLUGS['USER_ROLES']['SPONSOR']:
            # Get the users sponsored by this sponsor
            sponsored_users = list(models.user.objects.filter(user_subscription__sponsored_by_id=request.user.id).distinct().values_list('id', flat=True))
            qs = models.social_post.objects.filter(approved=True,user_id__in=sponsored_users,status='Active').exclude(user_id__in=blocked_users).distinct().order_by('-timestamp')
        else:
            qs = models.social_post.objects.filter(approved=True,org_id=org_id,status='Active').exclude(user_id__in=blocked_users).distinct().order_by('-timestamp')
        
        if tag:
            qs=qs.filter(tag=tag)

        return qs

    def get(self,request):
        try:
            org_id= request.user.organization_id
            tag= request.GET.get("tag")
            
            if request.user.user_role.role_name != constants.SLUGS['USER_ROLES']['SPONSOR'] and not org_id:
                return res.req_response(constants.INVALID_BODY, False, 'AFV-SLGET-1', status.HTTP_400_BAD_REQUEST)
            
            # Get the blocked users
            blocked_users = list(models.user_reporting.objects.filter(blocked_by_user=request.user.id,block=True).distinct().values_list('id', flat=True))
            
            qs= self.get_queryset(request,org_id,blocked_users,tag)
            page =  self.paginate_queryset(qs,request)

            serializer=None
            if page:          
                serializer=serializers.sociallistSerializer(page,many=True).data
                serializer=self.get_paginated_response(serializer).data

            return res.req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, serializer)
        except Exception as e:
            return res.req_response(constants.ERROR, False, 'AFV-SLGET-2', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)

class user_block_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        #user_id  = request.GET.get("user_id")
        key = request.GET.get("secret-key")
        user_id = request.GET.get("user_id")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)


        if len(serializer1.data) != 0 :
            qs = models.user_reporting.objects.filter(blocked_by_user=user_id,block=True).distinct()
            serializer = serializers.userblocklistSerializer(qs, many=True)
            if len(serializer.data) != 0  :
                response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

            if len(serializer.data) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
            return Response(response, status=response['status'])

        else:
            response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}

class social_list_by_user(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        #user_id  = request.GET.get("user_id")
        key = request.GET.get("secret-key")
        user_id = request.GET.get("user-id")
        
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)

        if len(serializer1.data) != 0 :
            qs = models.social_post.objects.filter(approved=True,user_id=user_id,status='Active').distinct().order_by('-timestamp')
            serializer = serializers.sociallistSerializer(qs, many=True)
            if len(serializer.data) != 0  :
                response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

            if len(serializer.data) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
            return Response(response, status=response['status'])

        else:
            response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}
        #except:
            #response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            #return Response(response, status=response['status'])

class social_list_user_paginated(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=models.social_post

    def get_queryset(self,request,user_id,tag):
        if request.user.user_role.role_name == constants.SLUGS['USER_ROLES']['SPONSOR']:
            # Get the users sponsored by this sponsor
            qs = models.social_post.objects.filter(approved=True,user_id=user_id,status='Active').distinct().order_by('-timestamp')
        else:
            qs = models.social_post.objects.filter(approved=True,user_id=user_id,status='Active').distinct().order_by('-timestamp')
        if tag:
            qs=qs.filter(tag=tag)

        return qs

    def get(self,request):
        try:
            org_id= request.user.organization_id
            user_id = request.GET.get("user-id")
            tag = request.GET.get("tag")
          
            qs= self.get_queryset(request,user_id,tag)
            
            serializer = serializers.sociallistSerializer(qs, many=True)
            if len(serializer.data) == 0:
                return res.req_response(constants.NO_CONTENT, True, '', status.HTTP_204_NO_CONTENT, serializer.data)
            page =  self.paginate_queryset(qs,request)

            serializer=None
            if page:          
                serializer=serializers.sociallistSerializer(page,many=True).data
                serializer=self.get_paginated_response(serializer)

            return res.req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, serializer.data)
        except Exception as e:
            return res.req_response(constants.ERROR, False, 'AFV-SLGET-2', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)

class agents_summary(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs2 = models.tb_application_access.objects.filter(key=key)
            serializer2 = serializers.key_serializer(qs2, many=True)

            if len(serializer2.data) != 0 :
                qs1 = models.agents.objects.filter(user_id=user_id,approved=True)
                serializer1 = serializers.agentSerializer(qs1, many=True)

                if len(serializer1.data) != 0 :
                    #qs = models.user.objects.filter(id=user_id).distinct()
                    #pincode = models.user.objects.filter(id=user_id).values('address_pincode')
                    pincode = models.user.objects.values_list('address_pincode',flat=True).get(id=user_id)

                    # print("pincode is:",pincode)
                    q2 = models.user.objects.filter(address_pincode=pincode).distinct()
                    farmers_num = models.user.objects.filter(address_pincode=pincode).distinct().count()
                    total_downloads = models.user.objects.filter(address_pincode=pincode).distinct().count()
                    order_list =  models.order.objects.filter(user_id__in=Subquery(q2.values('id')))
                    prod_list = models.order_details.objects.filter(order_id__in=Subquery(order_list.values('id'))).all()
                    #serializer2 = serializers.userpincodeSerializer(qs2, many=True)
                    #user_list = list(q2)
                    #print(user_list)

                    #user_list = qs2.values_list('id', flat=True)
                    #print("user_list is:",qs2.values_list('id', flat=True))

                    #orders_delivered = models.order.objects.filter(user_id=user_list,status='Delivered').count()
                    orders_delivered = models.order.objects.filter(user_id__in=Subquery(q2.values('id')),status='Delivered').count()
                    sales_amount = 0.001
                    money_earned = 0.001
                    orders_current = models.order.objects.filter(user_id__in=Subquery(q2.values('id'))).count() - models.order.objects.filter(user_id__in=Subquery(q2.values('id')),status='Delivered').count()
                    sales_amount = models.order.objects.filter(user_id__in=Subquery(q2.values('id'))).aggregate(Sum('total_amount')).get('total_amount__sum',0.0)
                    #order_details = models.order_details.objects.filter(user_id=user_id,approved=True)
                    agent_amount = models.product_master.objects.filter(id__in=Subquery(prod_list.values('product_id'))).aggregate(Sum('agent_price')).get('agent_price__sum',0.0)
                    #money_earned = sales_amount[0] * 0.1
                    #print(type(float(sales_amount)))
                    if sales_amount is None :
                        sales_amount = 0.001

                    else:
                        money_earned = round(float(sales_amount) - float(agent_amount))
                    #    sales_amount =0
                    #else :
                    #    sales_amount =0
                    #orders_current= models.order.objects.filter(user_id=user_list,status__in=('Placed','In Transit')).count()

                    #if len(serializer.data) != 0  :

                    #if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_200_OK,'message':'agent', 'orders_delivered':orders_delivered, 'sales_amount':sales_amount , 'money_earned':money_earned ,'order_current':orders_current, 'farmers_num':farmers_num,'total_downloads':total_downloads }
                    return Response(response, status=response['status'])
                else :

                    response = {'status': status.HTTP_400_BAD_REQUEST, 'message':'not an agent' }

                #if len(serializer.data) == 0  :
                #    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])

class order_view_agent(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.agents.objects.filter(user_id=user_id)
            serializer1 = serializers.agentSerializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.user.objects.filter(id=user_id).distinct()
                pincode = models.user.objects.filter(id=user_id).values('address_pincode')
                pincode = models.user.objects.values_list('address_pincode',flat=True).get(id=user_id)
                print("pincode is:",pincode)
                q2 = models.user.objects.filter(address_pincode=pincode).distinct()
                    #user_list = models.user.objects.values_list('id',flat=True).get(address_pincode=pincode)
                    #print(user_list)
                    #key = request.GET.get("secret-key")
                    #qs1 = models.tb_application_access.objects.filter(key=key)
                    #serializer1 = serializers.key_serializer(qs1, many=True)

                    #if len(serializer1.data) != 0 :
                #qs = models.order.objects.filter(user_id__in=Subquery(q2.values('id'),status='Delivered')).distinct()
                qs = models.order.objects.filter(user_id__in=Subquery(q2.values('id'))).distinct()
                serializer = serializers.orderSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])

def send_mail(send_to, subject, text, files=None):
    '''files is the list of file_paths to be attached'''
    send_from = 'jaya.kumari@arya.ag.com'
    #assert isinstance(send_to, list)

    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=os.path.basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f)
        msg.attach(part)

    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(send_from, "pra123**")
    text = msg.as_string()
    server.sendmail(send_from, send_to, text)
    server.quit()

class Agent_reg_email(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []

    def get(self,request):
        #try:
        user_id  = request.GET.get("user_id")
        send_to = 'jaya.kumari@arya.ag'
        subject = 'Agent Registration Form Filled by ' + user_id
        text = 'user id :' + user_id
        send_mail(send_to,subject,text)
        response = {'status': status.HTTP_204_NO_CONTENT,'message':'Success' }
        return Response(response)



hash_fn = basehash.base36()


#class SessionAddView(generics.CreateAPIView):
#    serializer_class = serializers.session_serializer
#    queryset = models.session.objects.all()

def validNumber(phone_nuber):
    pattern = re.compile("^[+]{1}[\dA-Z]{12}$", re.IGNORECASE)
    return pattern.match(phone_nuber) is not None

class verifyOTPView(APIView):
    def post(self, request, *args, **kwargs):
        otp = self.kwargs.get('otp')
        phone = self.kwargs.get('phone')
        key = self.kwargs.get('secret-key')
        # qs1 = models.tb_application_access.objects.filter(key=key)
        # serializer1 = serializers.login_serializer(qs1, many=True)
            #print("serializer 1 :",serializer1)
        #if len(serializer1.data) != 0 :
            #try:
                #user = OTPValidation.objects.get(phone_number=phone)

                #identitySerializer = employee_profile_list_serializer(data=user.__dict__)
            #employee_profile_list_serializer.is_valid(raise_exception=False)
        if (phone == '+919191919191') or (phone =='+919999999999'):
            if otp == '123456':
                return JsonResponse(
                        {'status': 'Success', 'message': "Phone number verified"}, status=200)
        else :
            sessionData = models.OTPValidation.objects.get(phone_number=phone)
            verify_otp = settings.OTP_VERIFY_URL+settings.OTP_VERIFY_TOKEN+"/SMS/VERIFY/"+sessionData.session_id+"/"+otp
            # print(verify_otp)
            req = urllib.request.Request(verify_otp)

            context = ssl.SSLContext()

            with urllib.request.urlopen(req, context=context) as response:
                html = response.read()
                Details = ast.literal_eval(html.decode('utf-8')).get("Details")
                status = ast.literal_eval(html.decode('utf-8')).get("Status")
                if status == "Success" and Details == "OTP Matched":

                    #if user is not None:
                            #login(request, user)
                            #payload = payload_handler(user)
                            #token = encode_handler(payload)
                            #sessionData.delete()
                        return JsonResponse(
                                {'status': 'Success', 'message': "Phone number verified"}, status=200)
                #except:
                #   return JsonResponse(
                #      {'status': 'Error', 'message': "Invalid otp or phone number"}, status=400)


@api_view([ 'POST'])
def OTPLogin(request, phone):
    if validNumber(phone):

        uniqueid=request.GET.get('uniqueid')
        if (phone == '+919191919191') or (phone =='+919999999999'):
            return JsonResponse({'status': 'success', 'message': "OTP has been sent successfully to your phone number"}, status=200)
        
        #try:
        #user = employee_profile.objects.get(phone_number=phone)
        # qs1 = models.tb_user_auth.objects.filter(key=secret-key)
        # serializer1 = serializers.login_serializer(qs1, many=True)
            #print("serializer 1 :",serializer1)
        # if len(serializer1.data) != 0 :
        url = "https://alerts.cbis.in/SMSApi/send"
        digits = [i for i in range(0, 10)]

        ## initializing a string
        otp = ""

        for i in range(6):
            index = math.floor(random.random() * 10)
            otp += str(digits[index])

        msg= "<#> Please use OTP "+otp+" to login to your Aryashakti account and get advisory and help from your FPO and our satellite based farm analysis. "+uniqueid
                        
        payload={'userid': 'aryacma',
        'password': 'fqGnYXMS',
        'msg': msg,
        'type': 'text',
        'senderid': 'aryaMK',
        'test': 'true',
        'duplicatecheck': 'true',
        'format': 'json',
        'mobile': phone,
        'sendMethod': 'quick',
        'msgType': "text",
        'dltTemplateId': "1707167948516066799"}
        
        headers = {
        'apikey': 'sdfds',
        'Cookie': 'SERVERID=webC1'
        }

        files=[

        ]
        
        response2 = requests.request("POST", url, headers=headers, data=payload, files=files)
        # print(response2)
        if response2:
            models.OTPValidation.objects.create(phone_number=phone,otp_value=otp)
            return JsonResponse(
                        {'status': 'success', 'message': "OTP has been sent successfully to your phone number"}, status=200)
        else:
            return JsonResponse(
                    {'status': 'false', 'message': "Error in sending the OTP"}, status=500)

           
class agent_summary_filter(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            start= request.GET.get("start")
            end= request.GET.get("end")
            key=request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.user.objects.filter(timestamp__gte=start,timestamp__lte=end)
                serializer = serializers.agent_summary_filter(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                        response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])


class order_details_by_id(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            order_id  = request.GET.get("order_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.order_details.objects.filter(order_id=order_id).distinct()
                serializer = serializers.orderDetailsSerializerbyId(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])


class brand_filter_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            category  = request.GET.get("category")
            sub_category = request.GET.get("sub_category")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :

                qs =models.product_master.objects.filter(category_a=category,sub_category=sub_category).values_list('brand_id',flat=True).distinct()
                qs1=models.brand_master.objects.filter(id__in=list(qs))
                serializer = serializers.brandlistSerializer(qs1, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])


class brand_filter(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            brand_id  = request.GET.get("brand_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.brand_master.objects.filter(id=brand_id).distinct()
                serializer = serializers.brandlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])



class product_list_by_brandID(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            category  = request.GET.get("category")
            sub_category = request.GET.get("sub_category")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                brand_id=list(request.GET.get("brand_id").split(','))
                print(brand_id)
                if '0' in brand_id:


                    qs = models.product_master.objects.filter(status='Active',category_a=category,sub_category=sub_category).distinct()

                        #tot = models.product_master.objects.filter(status='Active',category_a=category,sub_category=sub_category).distinct().count()
                        #print(tot)
                    serializer = serializers.productlistSerializer(qs, many=True)
                    if len(serializer.data) != 0  :
                        response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                    if len(serializer.data) == 0  :
                        response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                    return Response(response, status=response['status'])
                else:
                    brand_id.pop()
                    qs = models.product_master.objects.filter(category_a=category,sub_category=sub_category,brand_id__in=brand_id).distinct()

                    serializer = serializers.productlistSerializer(qs, many=True)
                    if len(serializer.data) != 0  :
                        response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                    if len(serializer.data) == 0  :
                        response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                    return Response(response, status=response['status'])

            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])

#############edited##########

from math import radians, cos, sin, asin, sqrt

class Nearbypartner(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def calculate(self,lat1, lat2, lon1, lon2):
        lon1 = radians(lon1)
        lon2 = radians(lon2)
        lat1 = radians(lat1)
        lat2 = radians(lat2)
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))
        r = 6371
        return(c * r)

    def get(self,request):
        try:
            latitude  = request.GET.get("latitude")
            longitude = request.GET.get("longitude")
            distance = int(request.GET.get("max_dist"))
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :

                l=[i.id for i in models.partner_list.objects.all() if distance>=self.calculate(i.latitude,float(latitude),i.longitude,float(longitude))  ]
                qs=models.partner_list.objects.filter(id__in=l)

                serializer = serializers.partnerlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])


class Deleteaddress(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            address_id= request.GET.get("address_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs=models.delivery_address.objects.filter(id=address_id).delete()
                response = {'status': status.HTTP_200_OK,'message':'success'}
                return Response(response, status=response['status'])

            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])

class Modifyaddress(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            address_id= request.GET.get("address_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs=models.delivery_address.objects.get(pk=address_id)
                serializer = serializers.ModifyaddressSerializer(qs,data=request.data,partial=True)
                if serializer.is_valid():
                    serializer.save()
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                else  :
                    response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])

from farm_category.views import getOrganizationFarms
from django.db.models import Q,F
class Socialprofile(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id= request.GET.get("user_id")
            key = request.GET.get("secret-key")
            #email = request.GET.get("email")
            
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                try:
                    qs=models.user.objects.filter(id=user_id).select_related('organization','user_role').get()
                    filtered_categories=getOrganizationFarms(qs.organization)

                   
                    # Extract unique crop names
                    filtered_categories.filter(id__gt=0,farm__crop_id__id__isnull=False).annotate(
                        crop_id=F('farm__crop_id__id'),
                        crop_name=F('farm__crop_id__crop_name'),
                        unselected_icon_url=F('farm__crop_id__crop_unselected_icon_url'),
                        selected_icon_url=F('farm__crop_id__crop_selected_icon_url'),
                    )

                    # Count distinct crop entries
                    count = filtered_categories.values('farm__crop_id').distinct().count()

                    #print(count)
                    models.organizations.objects.filter(id=qs.organization.id).update(crops=count)
                    qs=models.user.objects.filter(id=user_id).select_related('organization','user_role').get()
                    
                except models.user.DoesNotExist:
                    qs=None
                if qs:
                    serializer = serializers.SocialprofileSerializer(qs,many=False)
                    profile_data = [serializer.data]
                    response = {'status': status.HTTP_200_OK,'message':'success','data':profile_data }
                else  :
                    response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
                return Response(response, status=response['status'])

            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}
                return Response(response, status=response['status'])

        except Exception as e:
            print(e)
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])

class EditSocialprofile(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id= request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs=models.user.objects.get(pk=user_id)
                serializer = serializers.EditSocialprofileSerializer(qs,data=request.data,partial=True)
                if serializer.is_valid():
                    serializer.save()
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                else  :
                    response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
                return Response(response, status=response['status'])

            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])


class OrganizationTagDetails(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []

    def get(self, request):
        try:
            org_id = request.GET.get('org_id')
            project = request.GET.get('project')
            cadre = request.GET.get('cadre')
            state = request.GET.get('state')
            key = request.GET.get('secret-key')

            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) == 0:
                response = {'status': status.HTTP_400_BAD_REQUEST, 'message': 'Invalid Secret Key'}
                return Response(response, status=response['status'])

            organizations_qs = models.organizations.objects.all()

            if org_id:
                organizations_qs = organizations_qs.filter(id=org_id)

            if project:
                organizations_qs = organizations_qs.filter(
                    tag_organization__tag__type__category__iexact='PROJECT',
                    tag_organization__tag__name__iexact=project,
                )

            if cadre:
                organizations_qs = organizations_qs.filter(
                    tag_organization__tag__type__category__iexact='CADRE',
                    tag_organization__tag__name__iexact=cadre,
                )

            if state:
                organizations_qs = organizations_qs.filter(
                    tag_organization__tag__type__category__iexact='STATE',
                    tag_organization__tag__name__iexact=state,
                )

            organizations_qs = organizations_qs.distinct().order_by('org_name')

            if not organizations_qs.exists():
                response = {'status': status.HTTP_204_NO_CONTENT, 'message': 'No content', 'data': []}
                return Response(response, status=response['status'])

            serializer = serializers.OrganizationWithTagsSerializer(organizations_qs, many=True)
            response = {
                'status': status.HTTP_200_OK,
                'message': 'success',
                'data': serializer.data,
            }
            return Response(response, status=response['status'])

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            response = {'status': status.HTTP_400_BAD_REQUEST, 'message': f'Bad Request: {str(e)}'}
            return Response(response, status=response['status'])

class Delivered_order(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id=request.GET.get('user_id')
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                q=models.order.objects.filter(user_id=user_id).values_list('id')
                # print(q)
                qs = models.tracking.objects.filter(delivered=True,order_id__in=q).distinct().values_list('order_id')
                qs1=models.order.objects.filter(id__in=qs)
                serializer = serializers.orderSerializer(qs1,many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])



class Delivered_order_for_agents(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.agents.objects.filter(user_id=user_id)
            serializer1 = serializers.agentSerializer(qs1, many=True)

            if len(serializer1.data) != 0 :
            #qs = models.user.objects.filter(id=user_id).distinct()
            #pincode = models.user.objects.filter(id=user_id).values('address_pincode')
                pincode = models.user.objects.values_list('address_pincode',flat=True).get(id=user_id)
                # print("pincode is:",pincode)
                q2 = models.user.objects.filter(address_pincode=pincode).distinct()
                    #user_list = models.user.objects.values_list('id',flat=True).get(address_pincode=pincode)
                    #print(user_list)
                    #key = request.GET.get("secret-key")
                    #qs1 = models.tb_application_access.objects.filter(key=key)
                    #serializer1 = serializers.key_serializer(qs1, many=True)

                    #if len(serializer1.data) != 0 :
                #qs = models.order.objects.filter(user_id__in=Subquery(q2.values('id'),status='Delivered')).distinct()
                qs = models.order.objects.filter(user_id__in=Subquery(q2.values('id')),status  = 'Delivered').distinct()
                serializer = serializers.orderSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])


class product_list_by_secondfilter(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            category  = request.GET.get("category")
            sub_category = request.GET.get("sub_category")
            brand_id=list(request.GET.get("brand_id").split(','))
            filter2=request.GET.get('filter2')
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                # print(brand_id)
                if '0' in brand_id:

                    #
                    #
                    #

                    #
                    qs = models.product_master.objects.filter(status='Active',category_a=category,sub_category=sub_category).distinct()

                        #tot = models.product_master.objects.filter(status='Active',category_a=category,sub_category=sub_category).distinct().count()
                        #print(tot)
                    serializer = serializers.productsecondfilter(qs, many=True)
                    if len(serializer.data) != 0  :
                        response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                    if len(serializer.data) == 0  :
                        response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                    return Response(response, status=response['status'])

                elif filter2=='0':
                    brand_id.pop()
                    qs = models.product_master.objects.filter(category_a=category,sub_category=sub_category,brand_id__in=brand_id).distinct()

                    serializer = serializers.productsecondfilter(qs, many=True)
                    if len(serializer.data) != 0  :
                        response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                    if len(serializer.data) == 0  :
                        response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                    return Response(response, status=response['status'])



                elif filter2.isnumeric() :
                    brand_id.pop()
                    qs = models.product_master.objects.filter(category_a=category,sub_category=sub_category,brand_id__in=brand_id,hp__icontains=filter2).distinct()
                    serializer = serializers.productfiltermachine(qs, many=True)
                    if len(serializer.data) != 0  :
                        response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                    if len(serializer.data) == 0  :
                        response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                    return Response(response, status=response['status'])

                else:
                    brand_id.pop()
                    qs = models.product_master.objects.filter(category_a=category,sub_category=sub_category,brand_id__in=brand_id,crop__icontains=filter2).distinct()
                    serializer = serializers.productfiltercrop(qs, many=True)
                    if len(serializer.data) != 0  :
                        response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                    if len(serializer.data) == 0  :
                        response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                    return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])



from firebase_admin import credentials
from firebase_admin import firestore
import firebase_admin


class social_list_with_like(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
        # post_id = request.GET.get("post_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :

                db=firestore.client()
                doc_ref=db.collection('posts')
                l=[doc.to_dict() for doc in doc_ref.stream()]
                doc_ref=db.collection('comments')
                comments=[doc.to_dict() for doc in doc_ref.stream()]

                qs = models.social_post.objects.all().distinct().order_by('-timestamp')
                serializer = serializers.sociallistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data,'like':l,'commments':comments}

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])


class Crop_list_filter(APIView):
    def get(self,request):
        try:
            category=request.GET.get('category')
            sub_category=request.GET.get('sub_category')
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                if sub_category=='0' or sub_category==None :
                    if category in ['Chemical','Seed','Nutrition']:
                        qs = models.product_master.objects.filter(category_a=category).values_list('crop').distinct()
                        l=[]
                        for i in qs:
                            if i[0]!=None:
                                l+=i[0].split(',')
                        serializer=serializers.Crop_list_filterSerializer(qs,many=True)
                        if len(serializer.data)!=0:
                            response = {'status': status.HTTP_200_OK,'message':'success','data':set(l) }
                        else  :
                            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
                        return Response(response, status=response['status'])
                    else:
                        qs=models.product_master.objects.filter(category_a=category).values_list('hp').distinct()
                        l=[]
                        for i in qs:
                            if i[0]!=None:
                                l.append(Decimal(i[0]))
                        serializer=serializers.Hp_list_filterSerializer(qs,many=True)
                        if len(serializer.data)!=0:
                            response = {'status': status.HTTP_200_OK,'message':'success','data':set(l) }
                        else  :
                            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
                        return Response(response, status=response['status'])
                else:
                    if category in ['Chemical','Seed','Nutrition'] and sub_category not in ["Tracktor","Sprayer","Electronics"]:
                        qs = models.product_master.objects.filter(category_a=category,sub_category=sub_category).values_list('crop').distinct()
                        # print(qs)
                        l=[]
                        for i in qs:
                            if i[0]!=None:
                                l+=i[0].split(',')
                        serializer=serializers.Crop_list_filterSerializer(qs,many=True)
                        if len(serializer.data)!=0:
                            response = {'status': status.HTTP_200_OK,'message':'success','data':set(l) }
                        else  :
                            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
                        return Response(response, status=response['status'])
                    else:
                        qs=models.product_master.objects.filter(category_a=category,sub_category=sub_category).values_list('hp').distinct()
                        # print(qs)
                        l=[]
                        for i in qs:
                            if i[0]!=None:
                                l.append(Decimal(i[0]))
                        serializer=serializers.Hp_list_filterSerializer(qs,many=True)
                        if len(serializer.data)!=0:
                            response = {'status': status.HTTP_200_OK,'message':'success','data':set(l) }
                        else  :
                            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
                        return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])



class Product_list_with_varient(APIView):
    def get(self,request):
        try:
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.product_master.objects.all()
                serializer = serializers.Productlist_with_variantlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret Key'}

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])


class Valid_Coupon(APIView):
    def get(self,request):
        try:

            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                date=datetime.datetime.now()
                qs = models.coupon_details.objects.filter(valid_to__gte=date)
                serializer=serializers.Valid_Coupon_Serializer(qs,many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class Coupon_Details(APIView):
    def get(self,request):
        try:
            coupon_code=request.GET.get("coupon_code")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.coupon_details.objects.filter(coupon_code=coupon_code)
                serializer=serializers.Coupon_Details_Serializer(qs,many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])



#pagination api's
class pagination_farm_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id1  = request.GET.get("user_id")
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            stressed = request.GET.get("stressed")
            healthy = request.GET.get("healthy")
            state1 = request.GET.get("state")
            district1 = request.GET.get("district")
            taluka1 = request.GET.get("taluka")
            village1 = request.GET.get("village")
            crop_id1 = request.GET.get("crop-id")
            sort_by = request.GET.get("sort_by") #0 for name ascending , 1 for name descending , 2 for acre descending , 3  for acre ascending , 4 for
            search_by_name = request.GET.get("search-by-name")
            search_by_user_name = request.GET.get("search_by_user_name")
            added_by = request.GET.get("added_by")

            filter_kwargs = {'user_id': user_id1}
            if search_by_user_name is not None:
                filter_kwargs['user__full_name__istartswith'] = search_by_user_name
            if search_by_name is not None:
                filter_kwargs['name__istartswith'] = search_by_name
            if stressed is not None:
                if stressed == '1':
                    filter_kwargs['stressed'] = True
                elif stressed == '0':
                    filter_kwargs['stressed'] = False
            if healthy is not None:
                if healthy == '1':
                    filter_kwargs['healthy'] = True
                elif healthy == '0':
                    filter_kwargs['healthy'] = False
            if state1 is not None:
                filter_kwargs['farm_state'] = state1
            if district1 is not None:
                filter_kwargs['farm_district'] = district1
            if taluka1 is not None:
                filter_kwargs['farm_taluka'] = taluka1
            if village1 is not None:
                filter_kwargs['farm_village'] = village1
            if added_by is not None:
                filter_kwargs['user__added_by_id'] = added_by
            if crop_id1 is not None:
                c1 = crop_id1.split(";")
                filter_kwargs['crop_id__in'] = [i for i in c1 if i]

            ordering = ['featured']
            if sort_by is not None:
                if sort_by == '0':
                    ordering.append('name')
                if sort_by == '1':
                    ordering.append('-name')
                if sort_by == '2':
                    ordering.append('total_area')
                if sort_by == '3':
                    ordering.append('-total_area')
            if stressed is not None:
                if stressed == '1':
                    ordering.append('-biotic_stress')
                elif stressed == '0':
                    ordering.append('biotic_stress')


            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10


                qs = models.farm.objects.filter(**filter_kwargs).order_by(*ordering).distinct()[start:end]
                tot = models.farm.objects.filter(**filter_kwargs).order_by(*ordering).distinct().count()
                serializer = serializers.farmlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'length':len(serializer1.data),'message':'success','data':serializer.data,'total_pages':tot}
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data}
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
                return Response(response, status=response['status'])
        except Exception as e :
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request '+str(e)}
            return Response(response, status=response['status'])

class pagination_farm_list_admin(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            org_id  = request.GET.get("org_id")
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            stressed = request.GET.get("stressed")
            healthy = request.GET.get("healthy")
            state1 = request.GET.get("state")
            district1 = request.GET.get("district")
            taluka1 = request.GET.get("taluka")
            village1 = request.GET.get("village")
            crop_id1 = request.GET.get("crop-id")
            sort_by = request.GET.get("sort_by") #0 for name ascending , 1 for name descending , 2 for acre descending , 3  for acre ascending , 4 for
            search_by_name = request.GET.get("search-by-name")
            search_by_user_name = request.GET.get("search_by_user_name")
            featured = request.GET.get("featured")
            stress_type = request.GET.get("stress_type")
            added_by = request.GET.get("added_by")

            q_filters = Q()
            filter_kwargs = {'org_id': org_id}

            if search_by_name is not None:
                q_filters &= (Q(name__istartswith=search_by_name) | Q(farmer_contact__icontains=search_by_name) | Q(user__mobile_number__icontains=search_by_name))

            if search_by_user_name is not None:
                q_filters &= (Q(user__full_name__istartswith=search_by_user_name) | Q(farmer_contact__icontains=search_by_user_name) | Q(user__mobile_number__icontains=search_by_user_name))

            if stressed is not None:
                if stressed == '1':
                    filter_kwargs['stressed'] = True
                elif stressed == '0':
                    filter_kwargs['stressed'] = False
            if featured is not None:
                if featured == '1':
                    filter_kwargs['featured'] = True
                elif featured == '0':
                    filter_kwargs['featured'] = False
            if healthy is not None:
                if healthy == '1':
                    filter_kwargs['healthy'] = True
                elif healthy == '0':
                    filter_kwargs['healthy'] = False
            if state1 is not None:
                filter_kwargs['farm_state'] = state1
            if district1 is not None:
                filter_kwargs['farm_district'] = district1
            if taluka1 is not None:
                filter_kwargs['farm_taluka'] = taluka1
            if village1 is not None:
                filter_kwargs['farm_village'] = village1
            if added_by is not None:
                filter_kwargs['user__added_by_id'] = added_by
            if crop_id1 is not None:
                c1 = crop_id1.split(";")
                filter_kwargs['crop_id__in'] = [i for i in c1 if i]
            if stress_type:
                if stress_type == "biotic":
                    filter_kwargs['biotic_stress__gt'] = constants.STRESS_THRESHOLD
                elif stress_type == "abiotic":
                    filter_kwargs['abiotic_stress__gt'] = constants.STRESS_THRESHOLD
                elif stress_type == "nutrient":
                    filter_kwargs['nutrient_stress__gt'] = constants.STRESS_THRESHOLD

            ordering = ['featured']
            if sort_by is not None:
                if sort_by == '0':
                    ordering.append('name')
                if sort_by == '1':
                    ordering.append('-name')
                if sort_by == '2':
                    ordering.append('total_area')
                if sort_by == '3':
                    ordering.append('-total_area')
            if stressed is not None:
                if stressed == '1':
                    ordering.append('-biotic_stress')
                elif stressed == '0':
                    ordering.append('biotic_stress')


            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10


                qs = models.farm.objects.filter(q_filters, **filter_kwargs).order_by(*ordering).distinct()[start:end]
                tot = models.farm.objects.filter(q_filters, **filter_kwargs).order_by(*ordering).distinct().count()
                serializer = serializers.farmlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','length':len(serializer.data),'data':serializer.data,'total_pages':tot}
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_200_OK,'message':'No content','data':serializer.data}
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
                return Response(response, status=response['status'])
        except Exception as e:
           print(e)
           response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request 1'}
           return Response(response, status=response['status'])


class pagination_activity_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10


                qs = models.activity.objects.filter(user_id=user_id).distinct()[start:end]
                tot=models.activity.objects.filter(user_id=user_id).distinct().count()
                serializer = serializers.activitylistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data,'total_pages':tot}

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data}
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])


class pagination_activity_master_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10

                qs = models.activity_master.objects.filter(user_id=user_id).distinct()[start:end]
                tot=  models.activity_master.objects.filter(user_id=user_id).distinct().count()
                serializer = serializers.activity_masterlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data ,'total_pages':tot}
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class pagination_sellcrop_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10

                qs = models.sell_crop.objects.filter(user_id=user_id).distinct()[start:end]
                tot=models.sell_crop.objects.filter(user_id=user_id).distinct().count()
                serializer = serializers.sell_croplistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data,'total_pages':tot }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class pagination_crop_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10
                #
                #
                #

                #
                qs = models.crop_master.objects.all().distinct()[start:end]
                tot= models.crop_master.objects.all().distinct().count()
                serializer = serializers.croplistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data,'total_pages':tot }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class pagination_offers_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10

                qs = models.offers.objects.filter(status='Active').distinct()[start:end]
                tot=models.offers.objects.filter(status='Active').distinct().count()
                serializer = serializers.offerlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data,'total_pages':tot }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class pagination_training_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            page_number = request.GET.get("page_number")
            page_number1 = int(page_number)
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10

                qs = models.training.objects.filter(status='Active').distinct()[start:end]
                tot = models.training.objects.filter(status='Active').distinct().count()
                serializer = serializers.traininglistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data ,'total_pages':tot }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class pagination_variety_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            crop_id  = request.GET.get("crop_id")
            page_number=request.GET.get("page_number")
            key = request.GET.get("secret-key")
            # qs1 = models.tb_application_access.objects.filter(key=key)
            # serializer1 = serializers.key_serializer(qs1, many=True)
            # if len(serializer1.data) != 0 :
            page_number1 = int(page_number)
            if (page_number1 == 1) :
                start = 0
                end = 10
            else :
                start = page_number1*10-10
                end = start+10

            # key = request.GET.get("secret-key")
            # qs1 = models.tb_application_access.objects.filter(key=key,id=12)
            # serializer1 = serializers.key_serializer(qs1, many=True)

            # if len(serializer1.data) != 0 :
            qs = models.crop_variety_master.objects
            
            if crop_id:
                try:
                    crop_data=models.crop_master.objects.filter(id=crop_id).get()
                except models.crop_master.DoesNotExist:
                    response={'status':status.HTTP_404_NOT_FOUND,'message':'Crop not found'}
                    return Response(response, status=response['status'])
                qs= qs.filter(crop_id=crop_data)
                qs=qs.distinct()[start:end]
                tot = models.crop_variety_master.objects.filter(crop_id=crop_id).distinct().count()
                serializer = serializers.varietylistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data ,'total_pages':tot}
                
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class pagination_product_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            category  = request.GET.get("category")
            sub_category = request.GET.get("sub_category")
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10

                qs = models.product_master.objects.filter(status='Active',category_a=category,sub_category=sub_category).distinct()[start:end]
                tot = models.product_master.objects.filter(status='Active',category_a=category,sub_category=sub_category).distinct().count()
                        
                serializer = serializers.productlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data,'total_pages':tot }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])


class pagination_popular_product_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10

                qs = models.product_master.objects.filter(popular=True).distinct()[start:end]
                tot=models.product_master.objects.filter(popular=True).distinct().count()
                serializer = serializers.productlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data,'total_pages':tot }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])

class pagination_product_variant_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10

                # key = request.GET.get("secret-key")
                # qs1 = models.tb_application_access.objects.filter(key=key,id=18)
                # serializer1 = serializers.key_serializer(qs1, many=True)
                # if len(serializer1.data) != 0 :
                qs = models.product_variants.objects.all().distinct()[start:end]
                tot=models.product_variants.objects.all().distinct().count()
                serializer = serializers.productvariantlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data,'total_pages':tot }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])


class pagination_address_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:

            user_id  = request.GET.get("user_id")
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10


                qs = models.delivery_address.objects.filter(user_id=user_id).distinct()[start:end]
                tot=models.delivery_address.objects.filter(user_id=user_id).distinct().count()
                serializer = serializers.deliveryaddresslist(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data ,'total_pages':tot}

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data}
                return Response(response, status=response['status'])

            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])

class pagination_news_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10

                qs = models.news.objects.filter(status='Active').distinct()[start:end]
                tot=models.news.objects.filter(status='Active').distinct().count()
                serializer = serializers.newslistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data ,'total_pages':tot}

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data}
                return Response(response, status=response['status'])

            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])


class pagination_carousel_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10

                qs = models.carousel.objects.all().distinct().order_by('index')[start:end]
                tot=models.carousel.objects.all().distinct().order_by('index').count()
                serializer = serializers.carousellistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data ,'total_pages':tot}

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data}
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])

class pagination_hashtag_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end=start+10
                #user_id  = request.GET.get("user_id")
                 #
                    #
                    #

                    #
                qs = models.hashtag_master.objects.all().distinct()[start:end]
                tot=models.hashtag_master.objects.all().distinct().count()
                serializer = serializers.hastaglistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data ,'total_pages':tot}

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else :
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])


class pagination_social_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10
                #user_id  = request.GET.get("user_id")
                    #
                    #
                    #

                    #
                #db=firestore.client()
                #doc_ref=db.collection('posts')
                n_likes = {'likes':1}    #[doc.to_dict() for doc in doc_ref.stream()]
                #doc_ref=db.collection('comments')
                n_comments ={'comments':1} #[doc.to_dict() for  doc in doc_ref.stream()]
                qs = models.social_post.objects.filter(approved=True).distinct().order_by('-timestamp')[start:end]
                tot=models.social_post.objects.filter(approved=True).distinct().count()
                serializer = serializers.sociallistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data ,'total_pages':tot}

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else :
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])


class pagination_social_list_with_like(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
        # post_id = request.GET.get("post_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                page_number = request.GET.get("page_number")
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10
                db=firestore.client()
                doc_ref=db.collection('posts')
                l=[doc.to_dict() for doc in doc_ref.stream()]
                doc_ref=db.collection('comments')
                comments=[doc.to_dict() for doc in doc_ref.stream()]

                qs = models.social_post.objects.all().distinct().order_by('-timestamp')[start:end]
                tot=models.social_post.objects.filter().distinct().count()
                serializer = serializers.sociallistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data,'total_pages':tot,'like':l,'commments':comments}

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else :
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])



class pagination_brand_filter_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            category  = request.GET.get("category")
            sub_category = request.GET.get("sub_category")
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10

                qs =models.product_master.objects.filter(category_a=category,sub_category=sub_category).values_list('brand_id',flat=True).distinct()
                qs1=models.brand_master.objects.filter(id__in=list(qs))[start:end]
                tot=models.brand_master.objects.filter(id__in=list(qs)).distinct().count()
                serializer = serializers.brandlistSerializer(qs1, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data ,'total_pages':tot}

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else :
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])

class AddActivityMaster(generics.CreateAPIView):
    serializer_class = serializers.activity_masteraddSerializer
    queryset = models.activity_master.objects.all()

class AddActivity(generics.CreateAPIView):
    serializer_class = serializers.activityaddSerializer
    queryset = models.activity.objects.all()

class activity_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                if user_id is None:

                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content'}
                    return Response(response, status=response['status'])
                else:

                    qs = models.activity.objects.filter(user_id=user_id).distinct()
                    serializer = serializers.activitylistSerializer(qs, many=True)
                    if len(serializer.data) != 0  :
                        response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                    if len(serializer.data) == 0  :
                        response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                    return Response(response, status=response['status'])
            else :
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class activity_admin_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        org_id  = request.GET.get("org_id")
        key = request.GET.get("secret-key")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            if org_id is None:

                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content'}
                return Response(response, status=response['status'])
            else:

                qs = models.activity.objects.filter(org_id=org_id).distinct()
                serializer = serializers.activitylistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
        else :
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
            return Response(response, status=response['status'])
        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])


class activity_master_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            plot_id  = request.GET.get("plot_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.activity_master.objects.filter(plot_id=plot_id).distinct()
                serializer = serializers.activity_masterlistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])
            else :
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class update_activity(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:

            now = timezone.now()
            activity_id  = request.GET.get("activity_id")
            total_hours = request.GET.get("total_hours")
            total_area = request.GET.get("total_area")
            trajectory = request.GET.get("trajectory")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.activity.objects.filter(id=activity_id).update(total_hours=total_hours,total_area=total_area,end_timestamp=now,trajectory=trajectory)
                #response = {'status': status.HTTP_200_OK,'message':'success' }

                qs1 = models.activity.objects.filter(prakshep_id=plot_id).distinct()
                serializer = serializers.activityaddSerializer(qs1, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK }

                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT}
                return Response(response, status=response['status'])
            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class update_livefeed(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:

        now = timezone.now()
        feed_id  = request.GET.get("feed-id")
        key = request.GET.get("secret-key")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            qs = models.live_feed.objects.filter(id=feed_id).update(status='Inactive')
                #response = {'status': status.HTTP_200_OK,'message':'success' }


            response = {'status': status.HTTP_200_OK }
            return Response(response, status=response['status'])
        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
            return Response(response, status=response['status'])
        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])

class update_farm(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:

            now = timezone.now()
            feed_id  = request.GET.get("farm-id")
            key = request.GET.get("secret-key")
            lat = request.GET.get("lat")
            lon = request.GET.get("lon")
            state = request.GET.get("state")
            district = request.GET.get("district")
            taluka = request.GET.get("taluka")
            village = request.GET.get("village")
            farm_img = request.GET.get("farm-img")
            

            if (not getDistanceValidation(lat,lon,feed_id)):
                response= {'status_code': status.HTTP_400_BAD_REQUEST, 'status': False, 'message': constants.LOCATION_ALREADY_EXIST }
                return Response(response, status=response['status_code'])
            point_value = Point(float(lon),float(lat))
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.farm.objects.filter(id=feed_id).update(
                    is_location=True,
                    latitude=lat,
                    longitude=lon,
                    farm_img=farm_img,
                    farm_state=state,
                    farm_district=district,
                    farm_taluka=taluka,
                    farm_village=village, 
                    updated_on_timestamp=datetime.datetime.now(),
                    geometry=point_value,
                    is_manual_updated=False,
                    timestamp_lat_long=timezone.now()
                   
                )
                    #response = {'status': status.HTTP_200_OK,'message':'success' }


                response = {'status': status.HTTP_200_OK }
                return Response(response, status=response['status'])
            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
                return Response(response, status=response['status'])
        except:
           response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
           return Response(response, status=response['status'])

class live_feed(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:

            now = timezone.now()
            org_id  = request.GET.get("org-id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 or True :
                qs = models.live_feed.objects.filter(org_id=org_id,status='Active',url__isnull=False).last()
                #response = {'status': status.HTTP_200_OK,'message':'success' }
                serializer = serializers.livefeedSerializer(qs, many=False)
                finaldata=[]
                if serializer:
                    finaldata=[serializer.data]
                    if not finaldata[0]['org_id']:
                        finaldata=[]

                response = {'status': status.HTTP_200_OK,'message':'success','data':finaldata}
                return Response(response, status=response['status'])
            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])


def has_admin_org_edit_access(user_obj):
    return bool(
        user_obj
        and getattr(user_obj, 'admin', False)
        and getattr(user_obj, 'can_edit_org_details', False)
    )


class AdminManagedUserList(APIView, PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    @classmethod
    def get_extra_actions(cls):
        return []

    def get_queryset(self, request):
        queryset = models.user.objects.select_related('organization', 'user_role').all().order_by('-id')

        organization_id = request.GET.get('organization_id')
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)

        user_type = (request.GET.get('type') or 'all').strip().lower()
        if user_type in ('farmer', 'farmers'):
            queryset = queryset.filter(
                Q(user_role__role_name__iexact='Farmer') |
                Q(user_role__role_name__icontains='farmer')
            )
        elif user_type in ('admin', 'admins'):
            queryset = queryset.filter(
                Q(user_role__role_name__iexact='Admin') |
                Q(user_role__role_name__icontains='admin')
            )
        elif user_type in ('can_edit_org', 'can_edit_org_details', 'editable_org', 'org_editor'):
            queryset = queryset.filter(can_edit_org_details=True)

        search = (request.GET.get('search') or '').strip()
        if search:
            search_filters = (
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(organization__org_name__icontains=search) |
                Q(user_role__role_name__icontains=search)
            )
            if search.isdigit():
                search_filters = search_filters | Q(mobile_number=int(search))
            queryset = queryset.filter(search_filters)

        return queryset

    def get(self, request):
        if not has_admin_org_edit_access(request.user):
            return res.req_response(
                "Not authorized",
                False,
                "PERMISSION_DENIED",
                status.HTTP_403_FORBIDDEN,
            )

        queryset = self.get_queryset(request)
        page = self.paginate_queryset(queryset, request)

        if page is not None:
            data = serializers.AdminManagedUserListSerializer(page, many=True).data
            data = self.get_paginated_response(data).data
        else:
            data = serializers.AdminManagedUserListSerializer(queryset, many=True).data

        return res.req_response("Data found", True, "", status.HTTP_200_OK, data)


class AdminUserActiveStatusUpdate(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []

    def patch(self, request, user_id):
        if not has_admin_org_edit_access(request.user):
            return res.req_response(
                "Not authorized",
                False,
                "PERMISSION_DENIED",
                status.HTTP_403_FORBIDDEN,
            )

        target_user = get_object_or_404(models.user, id=user_id)
        serializer = serializers.UserActiveStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_user.is_active = serializer.validated_data['is_active']
        target_user.save(update_fields=['is_active'])

        response_data = {
            "id": target_user.id,
            "is_active": target_user.is_active,
        }
        return res.req_response("User status updated", True, "", status.HTTP_200_OK, response_data)


class AdminUserCVRPStatusUpdate(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []

    def patch(self, request, user_id):
        if not has_admin_org_edit_access(request.user):
            return res.req_response(
                "Not authorized",
                False,
                "PERMISSION_DENIED",
                status.HTTP_403_FORBIDDEN,
            )

        target_user = get_object_or_404(models.user, id=user_id)
        serializer = serializers.UserCVRPStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_user.is_cvrp = serializer.validated_data['is_cvrp']
        target_user.save(update_fields=['is_cvrp'])

        response_data = {
            "id": target_user.id,
            "is_cvrp": target_user.is_cvrp,
        }
        return res.req_response("User CVRP status updated", True, "", status.HTTP_200_OK, response_data)


class TagOptionsView(APIView):
    """Returns available tag options grouped by category (PROJECT, CADRE, STATE)."""
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []

    def _is_serialized_list_name(self, value):
        raw = str(value).strip() if value is not None else ""
        if not (raw.startswith('[') and raw.endswith(']')):
            return False

        try:
            parsed = json.loads(raw)
            return isinstance(parsed, list)
        except Exception:
            try:
                parsed = ast.literal_eval(raw)
                return isinstance(parsed, (list, tuple, set))
            except Exception:
                return False

    def get(self, request):
        categories = ['PROJECT', 'CADRE', 'STATE']
        result = {}
        for category in categories:
            tags = (
                models.Tag.objects
                .filter(type__category__iexact=category, type__is_active=True)
                .select_related('type')
                .values('id', 'name')
                .order_by('name')
            )
            tag_list = [tag for tag in list(tags) if not self._is_serialized_list_name(tag.get('name'))]
            result[category.lower()] = tag_list
        return res.req_response("Tag options", True, "", status.HTTP_200_OK, result)


class AdminOrganizationUpdate(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []

    def patch(self, request, org_id):
        if not has_admin_org_edit_access(request.user):
            return res.req_response(
                "Not authorized",
                False,
                "PERMISSION_DENIED",
                status.HTTP_403_FORBIDDEN,
            )

        organization = get_object_or_404(models.organizations, id=org_id)
        state_value = request.data.get('state')
        cadre_value = request.data.get('cadre')
        project_value = request.data.get('project')
        serializer = serializers.OrganizationManagementUpdateSerializer(
            organization,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        if state_value is not None:
            self._set_single_category_tag(organization, state_value, 'STATE')
        if cadre_value is not None:
            self._set_single_category_tag(organization, cadre_value, 'CADRE')
        if project_value is not None:
            try:
                self._set_multi_category_tags(organization, project_value, 'PROJECT')
            except Exception as e:
                return res.req_response(
                    "Invalid project tag payload",
                    False,
                    "ORG_PROJECT_TAG_UPDATE_FAILED",
                    status.HTTP_400_BAD_REQUEST,
                    None,
                    str(e),
                )

        return res.req_response("Organization updated", True, "", status.HTTP_200_OK, serializer.data)
    
    def _set_single_category_tag(self, organization, tag_name, category):
        """Ensure organization has only one tag for a given category."""
        if isinstance(tag_name, (list, tuple, set)):
            tag_name = next((str(item).strip() for item in tag_name if str(item).strip()), "")

        normalized_value = str(tag_name).strip() if tag_name is not None else ""

        # If empty value is passed, clear existing mapping for this category
        if normalized_value == "":
            models.TagOrganization.objects.filter(
                organization=organization,
                tag__type__category__iexact=category,
            ).delete()
            return

        tag_type = models.TagType.objects.filter(category__iexact=category).first()
        if not tag_type:
            tag_type = models.TagType.objects.create(name=category.title(), category=category)

        tag = models.Tag.objects.filter(type=tag_type, name__iexact=normalized_value).first()
        if not tag:
            tag = models.Tag.objects.create(name=normalized_value, type=tag_type)

        # Keep only one tag per category per organization
        models.TagOrganization.objects.filter(
            organization=organization,
            tag__type__category__iexact=category,
        ).exclude(tag=tag).delete()

        models.TagOrganization.objects.get_or_create(
            organization=organization,
            tag=tag,
            defaults={
                'tag_assigned_date': timezone.now(),
            },
        )

    def _normalize_tag_values(self, tag_values):
        """Normalize tag values from list/json/comma-separated string into unique names."""
        if tag_values is None:
            return []

        values = []
        if isinstance(tag_values, (list, tuple, set)):
            values = list(tag_values)
        elif isinstance(tag_values, str):
            raw_value = tag_values.strip()
            if not raw_value:
                return []

            if raw_value.startswith('[') and raw_value.endswith(']'):
                try:
                    parsed = json.loads(raw_value)
                    if isinstance(parsed, list):
                        values = parsed
                    else:
                        values = [parsed]
                except Exception:
                    try:
                        parsed = ast.literal_eval(raw_value)
                        if isinstance(parsed, (list, tuple, set)):
                            values = list(parsed)
                        else:
                            values = [parsed]
                    except Exception:
                        values = [raw_value]
            elif ',' in raw_value:
                values = [item.strip() for item in raw_value.split(',')]
            else:
                values = [raw_value]
        else:
            values = [tag_values]

        normalized = []
        seen = set()
        for value in values:
            clean_value = str(value).strip()
            if not clean_value:
                continue
            dedupe_key = clean_value.lower()
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            normalized.append(clean_value)
        return normalized

    def _set_multi_category_tags(self, organization, tag_values, category):
        """Assign multiple tags for a category while preserving one mapping per tag."""
        normalized_values = self._normalize_tag_values(tag_values)

        if not normalized_values:
            models.TagOrganization.objects.filter(
                organization=organization,
                tag__type__category__iexact=category,
            ).delete()
            return

        tag_type = models.TagType.objects.filter(category__iexact=category).first()
        if not tag_type:
            tag_type = models.TagType.objects.create(name=category.title(), category=category)

        selected_tag_ids = []
        for value in normalized_values:
            tag = models.Tag.objects.filter(type=tag_type, name__iexact=value).first()
            if not tag:
                tag = models.Tag.objects.create(name=value, type=tag_type)
            selected_tag_ids.append(tag.id)

            models.TagOrganization.objects.get_or_create(
                organization=organization,
                tag=tag,
                defaults={
                    'tag_assigned_date': timezone.now(),
                },
            )

        models.TagOrganization.objects.filter(
            organization=organization,
            tag__type__category__iexact=category,
        ).exclude(tag_id__in=selected_tag_ids).delete()

class org_member_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            org_id  = request.GET.get("org_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.user.objects.filter(organization=org_id).distinct()
                serializer = serializers.org_member_listSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class org_member_download_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            org_id  = request.GET.get("org_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.user.objects.filter(organization=org_id,installed_app=False).distinct()
                serializer = serializers.org_member_listSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class org_member_first_time_user_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            org_id  = request.GET.get("org_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.user.objects.filter(organization=org_id,installed_app=True).distinct()
                serializer = serializers.org_member_listSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])


class update_profilepicture(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:

        now = timezone.now()
        user_id  = request.GET.get("user-id")
        url = request.GET.get("profile-url")
        key = request.GET.get("secret-key")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            qs = models.user.objects.filter(id=user_id).update(user_profile_img=url)
                #response = {'status': status.HTTP_200_OK,'message':'success' }
            response = {'status': status.HTTP_200_OK }
            return Response(response, status=response['status'])
        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
            return Response(response, status=response['status'])
        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])

from broadcast.views import send_notification
class send_push_notification(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:

        now = timezone.now()
        user_id  = request.GET.get("user-id")
        key = request.GET.get("secret-key")
        title = request.GET.get("title")
        body = request.GET.get("body")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            user_obj = models.user.objects.filter(id=user_id).first()
            if not user_obj:
                return Response({'status': status.HTTP_404_NOT_FOUND, 'message': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            deviceToken = user_obj.firebase_token
            mobile_number = user_obj.mobile_number

            # ── FCM tracking: dry-run validate BEFORE sending ─────────
            fcm_tracking = {}
            if deviceToken:
                try:
                    from libraries.push_notification import FirebaseHelper
                    firebase_helper = FirebaseHelper(use_adc=True)
                    validation = firebase_helper.validate_fcm_token(deviceToken)
                    token_valid = validation.get('valid', False)

                    if token_valid:
                        fcm_tracking['token_status'] = 'VALID'
                        fcm_tracking['what_this_means'] = 'App is installed on device. Token is registered with FCM.'
                    else:
                        fcm_error = validation.get('error', 'Unknown')
                        if 'Unregistered' in fcm_error:
                            fcm_tracking['token_status'] = 'UNREGISTERED'
                            fcm_tracking['what_this_means'] = 'App was UNINSTALLED or user cleared app data. Cannot receive notifications.'
                        elif 'Mismatch' in fcm_error:
                            fcm_tracking['token_status'] = 'WRONG_PROJECT'
                            fcm_tracking['what_this_means'] = 'Token belongs to a different Firebase project.'
                        elif 'Invalid' in fcm_error:
                            fcm_tracking['token_status'] = 'MALFORMED_TOKEN'
                            fcm_tracking['what_this_means'] = 'Token string is corrupted or not a real FCM token.'
                        else:
                            fcm_tracking['token_status'] = 'FCM_ERROR'
                            fcm_tracking['what_this_means'] = f'FCM rejected token: {fcm_error}'
                        fcm_tracking['fcm_error'] = fcm_error
                except Exception as e:
                    fcm_tracking['token_status'] = 'CHECK_FAILED'
                    fcm_tracking['what_this_means'] = f'Could not validate token: {str(e)}'
            else:
                fcm_tracking['token_status'] = 'NO_TOKEN'
                fcm_tracking['what_this_means'] = 'No firebase token stored. User never installed app or denied notification permission.'

            # ── Original sending logic (UNCHANGED) ────────────────────
            send_notification([str(mobile_number)], body)

            # ── Original response + FCM tracking added on top ─────────
            response = {
                'status': status.HTTP_200_OK,
                'message': 'message sent',
                'fcm_tracking': fcm_tracking,
            }
            return Response(response, status=response['status'])
        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
            return Response(response, status=response['status'])
        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])


class HookLiveFeed(APIView):

    def convertTime(self,date):
        datetime_object = parser.parse(date) 
        return datetime_object
    

    def deductMin(self,minute,user):

        helper.deductValidityNumber(user,'video-call',minute)


    def differenceStartEndTime(self,start_time,end_time):
        # Calculate the difference
        time_difference = end_time - start_time

        # Extract total minutes
        minutes_difference = time_difference.total_seconds() / 60

        return minutes_difference


    def post(self,request):
        data=request.data
        if(data['type']=="peer.join.success"):
            self.updateLivefeedUser(data)
        elif(data['type']=="peer.leave.success"):
            self.updatePeerLeave(data)
        elif(data['type']=="session.open.success"):
            self.sessionStarted(data)
        elif(data['type']=="session.close.success"):
            self.sessionClosed(data)
        return res.req_response("Data found",True,"",status.HTTP_200_OK,[])

    #peer.join.success
    def updateLivefeedUser(self,data):    
        # print(data)    
        org=models.organizations.objects.filter(room_100ms=data['data']['room_id']).first()
        if org: 
            live_feed=models.live_feed.objects.filter(org_id=org).first()
            user=None
            try:
                user=models.user.objects.filter(id=data['data']['user_id']).first()
            except models.user.DoesNotExist:
                user=None
            if live_feed and user:
                models.LivefeedUser.objects.update_or_create(user=user,live_feed=live_feed,defaults={"status":1,"data":data})

    #peer.join.leave
    def updatePeerLeave(self,data):        
        org=models.organizations.objects.filter(room_100ms=data['data']['room_id']).first()
        # print(org)
        if org: 
            try:
                live_feed=models.live_feed.objects.filter(org_id=org).first()
            except models.live_feed.DoesNotExist:
                live_feed=None
            try:
                user=models.user.objects.filter(id=data['data']['user_id']).first()
            except models.user.DoesNotExist:
                user=None
            if live_feed and user:
                models.LivefeedUser.objects.update_or_create(user=user,live_feed=live_feed,defaults={"status":0})
            if live_feed:
                still_active=models.LivefeedUser.objects.filter(live_feed=live_feed,status=1).count()
                
                if still_active>=0:
                    live_feed.end_timestamp=datetime.datetime.now(datetime.timezone.utc)
                    live_feed.save()
                    admin=models.user.objects.filter(organization=org,user_role__role_name="Admin").first()
                    started_time=live_feed.start_timestamp         
                    ended_time=live_feed.end_timestamp   
                    difference_min=self.differenceStartEndTime(started_time,ended_time)
                    if difference_min>0:                      
                        self.deductMin(difference_min,admin)

                    

    #session.open.success
    def sessionStarted(self,data):
        org=models.organizations.objects.filter(room_100ms=data['data']['room_id']).first()
        
        if org: 
            try:
                live_feed=models.live_feed.objects.filter(org_id=org).first()
            except models.live_feed.DoesNotExist:
                user=None
            if live_feed :
                live_feed.start_timestamp=self.convertTime(data['data']['session_started_at'])
                live_feed.save()
    
    #session.close.success
    def sessionClosed(self,data):
        org=models.organizations.objects.filter(room_100ms=data['data']['room_id']).first()
       
        if org: 
            live_feed=models.live_feed.objects.filter(org_id=org).first()
            user=models.user.objects.filter(organization=org,user_role__role_name="Admin").first()
            
            if live_feed and user : 
                
                started_time=self.convertTime(data['data']['session_started_at'])          
                ended_time=self.convertTime(data['data']['session_stopped_at'])  
                difference_min=self.differenceStartEndTime(started_time,ended_time)  
                live_feed.end_timestamp=ended_time
                live_feed.save()
                self.deductMin(difference_min,user)
                

class update_fcmtoken(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:

            now = timezone.now()
            user_id  = request.GET.get("user-id")
            fcm_token = request.GET.get("fcm-token")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.user.objects.filter(id=user_id).update(firebase_token=fcm_token)
                    #response = {'status': status.HTTP_200_OK,'message':'success' }
                response = {'status': status.HTTP_200_OK }
                return Response(response, status=response['status'])
            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class update_installedapp(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:

            now = timezone.now()
            user_id  = request.GET.get("user-id")

            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                qs = models.user.objects.filter(id=user_id).update(installed_app=True)
                    #response = {'status': status.HTTP_200_OK,'message':'success' }
                response = {'status': status.HTTP_200_OK }
                return Response(response, status=response['status'])
            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class update_status_community(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:

        now = timezone.now()
        post_id  = request.GET.get("post-id")
        status1 = request.GET.get("status")
        key = request.GET.get("secret-key")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            qs = models.social_post.objects.filter(id=post_id).update(status=status1)
                #response = {'status': status.HTTP_200_OK,'message':'success' }
            response = {'status': status.HTTP_200_OK }
            return Response(response, status=response['status'])
        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
            return Response(response, status=response['status'])
        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])

import threading
from concurrent.futures import ThreadPoolExecutor
import time

from broadcast.models import SmsTemplate, NotificationLog

sms_executor = ThreadPoolExecutor(max_workers=10)      # SMS thread pool
firebase_executor = ThreadPoolExecutor(max_workers=10) # Firebase thread pool


##########################################################################
# 1) SMS THREAD FUNCTION  (unchanged, but clean)
##########################################################################
def send_sms_threaded(phone, params, doms_id, language, sender, receiver, sms_template, delay_between=5):

    def job():
        try:
            noms = NoMS()
            status = noms.send_smsv2(
                0,
                'TRANSACTIONAL',
                'User',
                {
                    "parameterMap": params,
                    "domsTemplateId": doms_id,
                    "sendTo": phone,
                    "sendFrom": "aryaMK"
                },
                language
            )

            log = NotificationLog.objects.create(
                sender=sender,
                receiver=receiver,
                sms_template=sms_template,
                org_name=receiver.organization if receiver else None,
                receiver_phone=phone,
                status="pending"
            )

            if status["success"]:
                log.status = "success"
            else:
                log.status = "failed"

            log.response = status
            log.save()

        except Exception as e:
            print("Error sending SMS:", e)

    # Submit to pool
    sms_executor.submit(job)

    # Add delay BETWEEN SMS from API side
    if delay_between > 0:
        time.sleep(delay_between)



##########################################################################
# 2) FIREBASE THREAD-POOL IMPLEMENTATION
##########################################################################
from libraries.firebase_helper import get_firebase_helper

def send_firebase_threaded(device_tokens, title, message, data={}):
    """
    Entire Firebase send runs on ThreadPool (no direct threading.Thread)
    """

    def job():
        try:
            firebase_helper = get_firebase_helper()

            # NOTE: We remove internal infinite loop — firebase_helper handles batch tokens
            firebase_helper.send_push_notification(
                token_data=device_tokens,
                title=title,
                message=message,
                delay_between=5  # delay is handled outside if needed
            )
        except Exception as e:
            print("Firebase push error:", str(e))

    # Submit to firebase thread pool
    firebase_executor.submit(job)


from celery import group
from libraries.celery_task import send_sms_task, process_device_management_action

##########################################################################
# 3) GROUP SMS API VIEW
##########################################################################
class group_sms(APIView, SubscriptionRequiredMixin):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []
    
    def _get_phone_numbers_from_org(self, org_id):
        org_users = models.user.objects.filter(organization_id=org_id).values_list('mobile_number', flat=True)
        return [str(phone) for phone in org_users if phone and str(phone).isdigit() and len(str(phone)) == 10]
    
    def _normalize_contact_list(self, contact):
        if isinstance(contact, str):
            return [p.strip() for p in contact.split(";")]
        return contact if isinstance(contact, list) else []
    
    def _validate_template(self, language, doms_id):
        language_data = models.language_master.objects.filter(google_translate_code=language).first()
        if not language_data:
            return None, res.req_response("Language not found", False, "AF-VGSPOST-09", status.HTTP_404_NOT_FOUND)
        
        sms_template = SmsTemplate.objects.filter(doms_id=doms_id, language=language_data).first()
        if not sms_template:
            return None, res.req_response("Template not found", False, "AF-VGSPOST-08", status.HTTP_404_NOT_FOUND)
        
        return sms_template, None
    
    def _get_phone_from_item(self, item):
        if isinstance(item, str) and item.isdigit() and len(item) == 10:
            return item
        
        try:
            user = models.user.objects.filter(id=item).first()
            if user and user.mobile_number:
                phone_str = str(user.mobile_number)
                if phone_str.isdigit() and len(phone_str) == 10:
                    return phone_str
        except Exception:
            pass
        return None
    
    def _process_unselected_ids(self, unselected_ids):
        unselected_phones = set()
        for item in unselected_ids:
            phone = self._get_phone_from_item(item)
            if phone:
                unselected_phones.add(phone)
        return unselected_phones

    def post(self, request):
        msg = request.data.get("msg")
        contact = request.data.get("contact", [])
        doms_id = request.data.get("doms_id")
        payload = request.data.get("payload", {})
        language = request.data.get("language")
        select_all = request.data.get("select_all", False)
        org_id = request.data.get("org_id")
        unselected_ids = request.data.get("unselected_ids", [])

        if select_all:
            if not org_id:
                return res.req_response("org_id is required when select_all is true", False, "AF-VGSPOST-10", status.HTTP_400_BAD_REQUEST)
            phones = self._get_phone_numbers_from_org(org_id)
            if unselected_ids:
                unselected_phones = self._process_unselected_ids(unselected_ids)
                phones = [p for p in phones if p not in unselected_phones]
        else:
            phones = self._normalize_contact_list(contact)
            phones = [p for p in phones if p.isdigit() and len(p) == 10]

        if not phones:
            return res.req_response("No valid contacts", False, "AF-VGSPOST-01", status.HTTP_400_BAD_REQUEST)

        sms_template, error_response = self._validate_template(language, doms_id)
        if error_response:
            return error_response

        users = models.user.objects.filter(mobile_number__in=phones)
        user_map = {str(u.mobile_number): u for u in users}
        device_tokens = [u.firebase_token for u in users if u.firebase_token]

        jobs = [
            send_sms_task.s(
                phone,
                payload,
                doms_id,
                language,
                request.user.id,
                user_map.get(str(phone)).id if user_map.get(str(phone)) else None,
                sms_template.id
            )
            for phone in phones
        ]
        group(jobs).apply_async()

        if device_tokens:
            send_firebase_threaded(device_tokens, "Message from Admin", msg)

        helper.deductValidityNumber(request.user, 'sms', len(phones))

        return Response({"status": True, "sent": len(phones)}, status=status.HTTP_200_OK)


    

class location_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id1  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            state1 = request.GET.get("state")
            district1 = request.GET.get("district")
            taluka1 = request.GET.get("taluka")
            village1 = request.GET.get("village")

            filter_kwargs = {'user_id': user_id1}
            if state1 is not None:
                filter_kwargs['farm_state'] = state1
            if district1 is not None:
                filter_kwargs['farm_district'] = district1
            if taluka1 is not None:
                filter_kwargs['farm_taluka'] = taluka1
            if village1 is not None:
                filter_kwargs['farm_village'] = village1

            loc_ordering = ['featured', 'farm_state', 'farm_district', 'farm_taluka', 'farm_village']

            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                page_number1 = int(page_number)
                if (page_number1 == 1) :
                    start = 0
                    end = 10
                else :
                    start = page_number1*10-10
                    end = start+10


                qs = models.farm.objects.filter(**filter_kwargs).order_by(*loc_ordering).distinct()
                tot = models.farm.objects.filter(**filter_kwargs).order_by(*loc_ordering).distinct().count()
                serializer = serializers.loclistSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    tot=(tot//11)+1
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data,'total_pages':tot}
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data}
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
                return Response(response, status=response['status'])
        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class location_list_state(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        user_id1  = request.GET.get("user_id")
        key = request.GET.get("secret-key")
        lang = request.GET.get("language") #0 for hindi 1 for english
            #state1 = request.GET.get("state")
            #district1 = request.GET.get("district")
            #taluka1 = request.GET.get("taluka")
            #village1 = request.GET.get("village")

        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :

            qs = models.farm.objects.filter(user_id=user_id1).order_by('farm_state').values_list('farm_state', 'farm_state_hindi').distinct()
            s1 = list(qs)
            primary_index = 1 if lang == '0' else 0
            rm_list = []
            for c1, i in enumerate(s1):
                if i[primary_index] is None or i[primary_index] == '':
                    rm_list.append(c1)

            for z in sorted(rm_list, reverse=True):
                if len(s1)>z:
                    s1.pop(z)
                #serializer = serializers.loclistSerializerstate(qs, many=True)

            if len(s1) != 0  :
                    #tot=(tot//11)+1
                response = {'status': status.HTTP_200_OK,'message':'success','data':s1}
                return Response(response, status=response['status'])
            if len(s1) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content'}
                return Response(response, status=response['status'])
            else:
                response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
                return Response(response, status=response['status'])

class location_list_district(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        user_id1  = request.GET.get("user_id")
        key = request.GET.get("secret-key")
        state1 = request.GET.get("state")
        lang = request.GET.get("language") #0 for hindi 1 for english

        filter_kwargs = {'user_id': user_id1}
        if state1 is not None:
            if lang == '0':
                filter_kwargs['farm_state_hindi'] = state1
            else:
                filter_kwargs['farm_state'] = state1

        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :

            qs = models.farm.objects.filter(**filter_kwargs).values_list('farm_district', 'farm_district_hindi').distinct()

            s1 = list(qs)
            primary_index = 1 if lang == '0' else 0
            rm_list = []
            for c1, i in enumerate(s1):
                if i[primary_index] is None or i[primary_index] == '':
                    rm_list.append(c1)

            for z in sorted(rm_list, reverse=True):
                if len(s1)>z:
                    s1.pop(z)

            if len(s1) != 0  :
                #tot=(tot//11)+1
                response = {'status': status.HTTP_200_OK,'message':'success','data':s1}
                return Response(response, status=response['status'])
            if len(s1) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content'}
                return Response(response, status=response['status'])
        else:
            response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
            return Response(response, status=response['status'])
        #except:
            #response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            #return Response(response, status=response['status'])

class location_list_taluka(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        user_id1  = request.GET.get("user_id")
        key = request.GET.get("secret-key")
        state1 = request.GET.get("state")
        district1 = request.GET.get("district")
        lang = request.GET.get("language") #0 for hindi 1 for english

        filter_kwargs = {'user_id': user_id1}
        if state1 is not None:
            if lang == '0':
                filter_kwargs['farm_state_hindi'] = state1
            else:
                filter_kwargs['farm_state'] = state1
        if district1 is not None:
            if lang == '0':
                filter_kwargs['farm_district_hindi'] = district1
            else:
                filter_kwargs['farm_district'] = district1

        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            qs = models.farm.objects.filter(**filter_kwargs).values_list('farm_taluka', 'farm_taluka_hindi').distinct()
            s1 = list(qs)
            primary_index = 1 if lang == '0' else 0
            rm_list = []
            for c1, i in enumerate(s1):
                if i[primary_index] is None or i[primary_index] == '':
                    rm_list.append(c1)

            for z in sorted(rm_list, reverse=True):
                if len(s1)>z:
                    s1.pop(z)

            if len(s1) != 0  :
                #tot=(tot//11)+1
                response = {'status': status.HTTP_200_OK,'message':'success','data':s1}
                return Response(response, status=response['status'])
            if len(s1) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content'}
                return Response(response, status=response['status'])
        else:
            response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
            return Response(response, status=response['status'])
        #except:
            #response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            #return Response(response, status=response['status'])

class location_list_village(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        user_id1  = request.GET.get("user_id")
        key = request.GET.get("secret-key")
        state1 = request.GET.get("state")
        district1 = request.GET.get("district")
        taluka1 = request.GET.get("taluka")
        lang = request.GET.get("language") #0 for hindi 1 for english

        filter_kwargs = {'user_id': user_id1}
        if state1 is not None:
            if lang == '0':
                filter_kwargs['farm_state_hindi'] = state1
            else:
                filter_kwargs['farm_state'] = state1
        if district1 is not None:
            if lang == '0':
                filter_kwargs['farm_district_hindi'] = district1
            else:
                filter_kwargs['farm_district'] = district1
        if taluka1 is not None:
            if lang == '0':
                filter_kwargs['farm_taluka_hindi'] = taluka1
            else:
                filter_kwargs['farm_taluka'] = taluka1

        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :

            qs = models.farm.objects.filter(**filter_kwargs).values_list('farm_village', 'farm_village_hindi').distinct()
            s1 = list(qs)
            primary_index = 1 if lang == '0' else 0
            rm_list = []
            for c1, i in enumerate(s1):
                if i[primary_index] is None or i[primary_index] == '':
                    rm_list.append(c1)

            for z in sorted(rm_list, reverse=True):
                if len(s1)>z:
                    s1.pop(z)

            serializer = serializers.loclistSerializervillage(qs, many=True)
            if len(s1) != 0  :
                #s1 = removeduplicate(serializer.data)
            #s2=
            #if len(s1) != 0  :
                #tot=(tot//11)+1
                response = {'status': status.HTTP_200_OK,'message':'success','data':s1}
                return Response(response, status=response['status'])
            if len(s1) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content'}
                return Response(response, status=response['status'])
        else:
            response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
            return Response(response, status=response['status'])

def removeduplicate(it):
    seen = set()
    for x in it:
        if x not in seen:
            yield x
            seen.add(x)

class location_list_admin(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        org_id1  = request.GET.get("org_id")
        key = request.GET.get("secret-key")
        state1 = request.GET.get("state")
        district1 = request.GET.get("district")
        taluka1 = request.GET.get("taluka")
        village1 = request.GET.get("village")

        filter_kwargs = {'org_id': org_id1}

        if state1 is not None:
            filter_kwargs['farm_state'] = state1
        if district1 is not None:
            filter_kwargs['farm_district'] = district1
        if taluka1 is not None:
            filter_kwargs['farm_taluka'] = taluka1
        if village1 is not None:
            filter_kwargs['farm_village'] = village1


        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :


            qs = models.farm.objects.filter(**filter_kwargs).values_list('farm_state', 'farm_district', 'farm_taluka', 'farm_village').distinct()
            #tot=eval(y)
            #serializer = serializers.loclistSerializer(qs, many=True)

            s1 = removeduplicate(qs)
            #s2=
            if len(qs) != 0  :
                #tot=(tot//11)+1
                response = {'status': status.HTTP_200_OK,'message':'success','data':s1}
                return Response(response, status=response['status'])
            if len(serializer.data) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data}
                return Response(response, status=response['status'])
        else:
            response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
            return Response(response, status=response['status'])
        #except:
            #response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            #return Response(response, status=response['status'])

class location_list_admin_state(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        org_id1  = request.GET.get("org_id")
        key = request.GET.get("secret-key")
        lang = request.GET.get("language") #0 for hindi 1 for english

        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)

        if len(serializer1.data) != 0 :

            qs = models.farm.objects.filter(org_id=org_id1).values_list('farm_state', 'farm_state_hindi').distinct()
            s1 = list(qs)
            c1 = 0
            rm_list = []

            #removing none values
            for i in s1:
                count = 0
                for j in i:
                    if j is None :
                        count+=1
                if count > 0:
                    rm_list.append(c1)
                c1 +=1
            if len(rm_list)!=0:
                a=0
                for z in rm_list:
                        #print(z)
                    s1.pop(z-a)
                    a+=1
            #serializer = serializers.loclistSerializerstate(qs, many=True)

            if len(s1) != 0  :
                #tot=(tot//11)+1
                response = {'status': status.HTTP_200_OK,'message':'success','data':s1}
                return Response(response, status=response['status'])
            if len(s1) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content'}
                return Response(response, status=response['status'])
        else:
            response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
            return Response(response, status=response['status'])
        #except:
            #response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            #return Response(response, status=response['status'])

class location_list_admin_district(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        org_id1  = request.GET.get("org_id")
        key = request.GET.get("secret-key")
        state1 = request.GET.get("state")
        lang = request.GET.get("language") #0 for hindi 1 for english

        filter_kwargs = {'org_id': org_id1}
        if state1 is not None:
            if lang == 0:
                filter_kwargs['farm_state_hindi'] = state1
            else:
                filter_kwargs['farm_state'] = state1

        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :

            qs = models.farm.objects.filter(**filter_kwargs).values_list('farm_district', 'farm_district_hindi').distinct()

            s1 = list(qs)
            c1 = 0
            rm_list = []
            for i in s1:
                count = 0
                for j in i:
                    if j is None :
                        count+=1
                if count > 0:
                    rm_list.append(c1)
                c1 +=1
            a=0
            for z in rm_list:

                s1.pop(z-a)
                a+=1
            if len(qs) != 0  :
                #tot=(tot//11)+1
                response = {'status': status.HTTP_200_OK,'message':'success','data':s1}
                return Response(response, status=response['status'])
            if len(qs) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content'}
                return Response(response, status=response['status'])
        else:
            response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
            return Response(response, status=response['status'])
        #except:
            #response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            #return Response(response, status=response['status'])

class location_list_admin_taluka(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        org_id1  = request.GET.get("org_id")
        key = request.GET.get("secret-key")
        state1 = request.GET.get("state")
        district1 = request.GET.get("district")
        lang = request.GET.get("language") #0 for hindi 1 for english

        filter_kwargs = {'org_id': org_id1}
        if state1 is not None:
            if lang == 0:
                filter_kwargs['farm_state_hindi'] = state1
            else:
                filter_kwargs['farm_state'] = state1
        if district1 is not None:
            if lang == 0:
                filter_kwargs['farm_district_hindi'] = district1
            else:
                filter_kwargs['farm_district'] = district1

        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            qs = models.farm.objects.filter(**filter_kwargs).values_list('farm_taluka', 'farm_taluka_hindi').distinct()
            s1 = list(qs)
            c1 = 0
            rm_list = []
            for i in s1:
                count = 0
                for j in i:
                    if j is None :
                        count+=1
                if count > 0:
                    rm_list.append(c1)
                c1 +=1
            a=0
            for z in rm_list:
                s1.pop(z-a)
                a+=1

            if len(qs) != 0  :
                #tot=(tot//11)+1
                response = {'status': status.HTTP_200_OK,'message':'success','data':s1}
                return Response(response, status=response['status'])
            if len(qs) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content'}
                return Response(response, status=response['status'])
        else:
            response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
            return Response(response, status=response['status'])
        #except:
            #response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            #return Response(response, status=response['status'])

class location_list_admin_village(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        org_id1  = request.GET.get("org_id")
        key = request.GET.get("secret-key")
        state1 = request.GET.get("state")
        district1 = request.GET.get("district")
        taluka1 = request.GET.get("taluka")
        lang = request.GET.get("language") #0 for hindi 1 for english

        filter_kwargs = {'org_id': org_id1}
        if state1 is not None:
            if lang == 0:
                filter_kwargs['farm_state_hindi'] = state1
            else:
                filter_kwargs['farm_state'] = state1
        if district1 is not None:
            if lang == 0:
                filter_kwargs['farm_district_hindi'] = district1
            else:
                filter_kwargs['farm_district'] = district1
        if taluka1 is not None:
            if lang == 0:
                filter_kwargs['farm_taluka_hindi'] = taluka1
            else:
                filter_kwargs['farm_taluka'] = taluka1

        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :

            qs = models.farm.objects.filter(**filter_kwargs).values_list('farm_village', 'farm_village_hindi').distinct()
            s1 = list(qs)
            c1 = 0
            rm_list = []
            for i in s1:
                count = 0
                for j in i:
                    if j is None :
                        count+=1
                if count > 0:
                    rm_list.append(c1)
                c1 +=1
            a=0
            for z in rm_list:
                s1.pop(z-a)
                a+=1

            serializer = serializers.loclistSerializervillage(qs, many=True)
            if len(qs) != 0  :
                #s1 = removeduplicate(serializer.data)
            #s2=
            #if len(qs) != 0  :
                #tot=(tot//11)+1
                response = {'status': status.HTTP_200_OK,'message':'success','data':s1}
                return Response(response, status=response['status'])
            if len(qs) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content'}
                return Response(response, status=response['status'])
        else:
            response={'status':status.HTTP_400_BAD_REQUEST,'message':'Invalid Secret key'}
            return Response(response, status=response['status'])
        #except:
            #response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            #return Response(response, status=response['status'])
import sys, os
from decimal import Decimal
class org_details(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            org_id  = request.GET.get("org_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.organizations.objects.filter(id=org_id).annotate(stress_data=Avg('organization_farm__biotic_stress'),                                    
                                    damaged_data=Avg('organization_farm__damaged'),
                                    acre_data=Sum('organization_farm__total_area',filter=Q(organization_farm__area_unit="Acre")),
                                    hect_data=Sum('organization_farm__total_area',filter=Q(organization_farm__area_unit="Hectare")),
                                    healthy_farms=Count('organization_farm__category_farm__biotic_category',filter=Q(organization_farm__category_farm__biotic_category__trigger='Healthy')),
                                    healthy_farms_acres=Sum('organization_farm__total_area',filter=Q(organization_farm__area_unit="Acre",organization_farm__category_farm__biotic_category__trigger='Healthy')),
                                    healthy_farms_hect=Sum('organization_farm__total_area',filter=Q(organization_farm__area_unit="Hectare",organization_farm__category_farm__biotic_category__trigger='Healthy')),
                                    stressed_farms=Count('organization_farm__category_farm__biotic_category',filter=Q(organization_farm__category_farm__biotic_category__trigger__in=['Early Onset of Stress','Severe / Prolonged Stress','Stress'])),
                                    stressed_farms_acres=Sum('organization_farm__total_area',filter=Q(organization_farm__area_unit="Acre",organization_farm__category_farm__biotic_category__trigger__in=['Early Onset of Stress','Severe / Prolonged Stress','Stress'])),
                                    stressed_farms_hect=Sum('organization_farm__total_area',filter=Q(organization_farm__area_unit="Hectare",organization_farm__category_farm__biotic_category__trigger__in=['Early Onset of Stress','Severe / Prolonged Stress','Stress'])),
                                    damaged_farms=Count('organization_farm__category_farm__biotic_category',filter=Q(organization_farm__category_farm__biotic_category__trigger='Damaged')),
                                    damaged_farms_acres=Sum('organization_farm__total_area',filter=Q(organization_farm__area_unit="Acre",organization_farm__category_farm__biotic_category__trigger='Damaged')),
                                    damaged_farms_hect=Sum('organization_farm__total_area',filter=Q(organization_farm__area_unit="Hectare",organization_farm__category_farm__biotic_category__trigger='Damaged'))
                                      ).first()
                
                if qs.stress_data is not None:
                    qs.stress=round(qs.stress_data,2)
                if qs:
                    # Count unique users who have at least one farm in this organization
                    members_data = models.farm.objects.filter(
                        org_id=qs.id,
                        farmer_contact__isnull=False
                    ).exclude(
                        farmer_contact__exact=''
                    ).values(
                        'farmer_contact'
                    ).distinct().count()
                    qs.members = members_data
                
               
                if qs.damaged_data is not None:
                    qs.damaged=round(qs.damaged_data,2)
                
                if qs.acre_data is not None:
                    
                    if qs.hect_data is None:
                        qs.hect_data=0
                    qs.acres=Decimal(qs.acre_data) + ((Decimal(qs.hect_data) * Decimal('2.47105')))
                    
                qs.save()
                qs.refresh_from_db() 
                if qs.healthy_farms_acres and qs.healthy_farms_hect:
                    qs.healthy_farms_acres=qs.healthy_farms_acres+(Decimal(qs.healthy_farms_hect) * Decimal(2.47))

                if qs.stressed_farms_acres and qs.stressed_farms_hect:
                    qs.stressed_farms_acres=qs.stressed_farms_acres+(Decimal(qs.stressed_farms_hect) * Decimal(2.47))

                if qs.damaged_farms_acres and qs.damaged_farms_hect:
                    qs.damaged_farms_acres=qs.damaged_farms_acres+(Decimal(qs.damaged_farms_hect) * Decimal(2.47))




                serializer = serializers.OrgDetailSerializer(qs)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':[serializer.data]}
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content' }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request '+str(e)}
            return Response(response, status=response['status'])

class farm_stress(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        org_id  = request.GET.get("org_id")
        key = request.GET.get("secret-key")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)

        if len(serializer1.data) != 0 :
            qs = models.farm.objects.filter(org_id=org_id,stressed=True).distinct().order_by('stress')
            serializer = serializers.farmlistSerializer(qs, many=True)
            if len(serializer.data) != 0  :
                response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
            if len(serializer.data) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content' }
            return Response(response, status=response['status'])

        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
            return Response(response, status=response['status'])

        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])

class doc_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.compliance.objects.filter(user_id=user_id,status='Active').distinct()
                serializer = serializers.complianceSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class doc_view(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            doc_id  = request.GET.get("doc_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.compliance.objects.filter(id=doc_id).distinct()
                serializer = serializers.complianceSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class update_doc(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:

        now = timezone.now()
        doc_id  = request.GET.get("doc_id")
        url = request.GET.get("url")
        key = request.GET.get("secret-key")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            qs = models.live_feed.objects.filter(id=doc_id).update(file_url1=url)
                #response = {'status': status.HTTP_200_OK,'message':'success' }


            response = {'status': status.HTTP_200_OK }
            return Response(response, status=response['status'])
        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
            return Response(response, status=response['status'])

class delete_doc(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:

        now = timezone.now()
        doc_id  = request.GET.get("doc_id")

        key = request.GET.get("secret-key")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            qs = models.compliance.objects.filter(id=doc_id).update(status='Deleted')
                #response = {'status': status.HTTP_200_OK,'message':'success' }


            response = {'status': status.HTTP_200_OK }
            return Response(response, status=response['status'])
        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
            return Response(response, status=response['status'])

class product_category_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            #user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.product_category.objects.all().distinct()
                serializer = serializers.product_categorySerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class product_list_input(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            org_id  = request.GET.get("org_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.input_catalogue.objects.filter(org_id=org_id,status='Active').distinct()
                serializer = serializers.inputcatalogueSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class delete_product_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:

        now = timezone.now()
        product_id  = request.GET.get("product_id")
        key = request.GET.get("secret-key")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            qs = models.input_catalogue.objects.filter(id=product_id).update(status='Deleted')
                #response = {'status': status.HTTP_200_OK,'message':'success' }


            response = {'status': status.HTTP_200_OK }
            return Response(response, status=response['status'])
        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
            return Response(response, status=response['status'])
        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])

class edit_product_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:

        now = timezone.now()
        product_id  = request.GET.get("product_id")
        key = request.GET.get("secret-key")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            qs = models.input_catalogue.objects.filter(id=product_id).update(status='Deleted')
                #response = {'status': status.HTTP_200_OK,'message':'success' }


            response = {'status': status.HTTP_200_OK }
            return Response(response, status=response['status'])
        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
            return Response(response, status=response['status'])
        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])


class product_details(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            prod_id  = request.GET.get("prod_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.input_catalogue.objects.filter(id=prod_id).distinct()
                serializer = serializers.addinputcatalogueSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class farmer_request_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            user_id  = request.GET.get("user_id")
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)

            if len(serializer1.data) != 0 :
                qs = models.farmer_request.objects.filter(user_id=user_id).distinct()
                serializer = serializers.farmer_requestSerializer(qs, many=True)
                if len(serializer.data) != 0  :
                    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
                if len(serializer.data) == 0  :
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response, status=response['status'])

            else:
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
                return Response(response, status=response['status'])

        except:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
            return Response(response, status=response['status'])

class admin_request_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        org_id  = request.GET.get("org_id")
        key = request.GET.get("secret-key")
        status1 = request.GET.get("status")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)

        if len(serializer1.data) != 0 :
            if status is not None:
                qs = models.farmer_request.objects.filter(org_id=org_id,status=status1).distinct()
            else:
                qs = models.farmer_request.objects.filter(org_id=org_id).distinct()
            serializer = serializers.farmer_requestSerializer(qs, many=True)
            if len(serializer.data) != 0  :
                response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
            #else:
            #    response = {'status': status.HTTP_200_OK,'message':'success','data':serializer.data }
            if len(serializer.data) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content' }
            return Response(response, status=response['status'])

        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
            return Response(response, status=response['status'])

        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])

class update_request_status(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:

        now = timezone.now()
        request_id  = request.GET.get("request_id")
        status1= request.GET.get("status")
        key = request.GET.get("secret-key")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            qs = models.farmer_request.objects.filter(id=request_id).update(status=status1)
                #response = {'status': status.HTTP_200_OK,'message':'success' }


            response = {'status': status.HTTP_200_OK }
            return Response(response, status=response['status'])
        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
            return Response(response, status=response['status'])
        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])

class app_configuration(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:

        key = request.GET.get("secret-key")

        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)

        if len(serializer1.data) != 0 :

            qs = models.app_configuration.objects.filter(status=True).order_by('-minimum_compatible_version')[0]
            serializer = serializers.app_configurationSerializer(qs, many=True)
            if len(serializer.data) != 0  :
                # print(serializer)
                response = {'status': status.HTTP_200_OK,'message':'success' }
            if len(serializer.data) == 0  :
                response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content' }
            return Response(response,status=response['status'])

        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
            return Response(response, status=response['status'])

class update_firsttimelogin(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:

        now = timezone.now()
        user_id  = request.GET.get("user_id")
        key = request.GET.get("secret-key")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)
        if len(serializer1.data) != 0 :
            qs = models.user.objects.filter(id=user_id).update(installed_app=True,timestamp_login=timezone.now())
                #response = {'status': status.HTTP_200_OK,'message':'success' }
            response = {'status': status.HTTP_200_OK }
            return Response(response, status=response['status'])
        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
            return Response(response, status=response['status'])
        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])

# class Update_UserProfileEdit(APIView):
#     @classmethod
#     def get_extra_actions(cls):
#         return []
#     def get(self,request):

#         try:
#             user_id  = request.GET.get("user_id")
#             key = request.GET.get("secret-key")
#             qs1 = models.tb_application_access.objects.filter(key=key)
#             serializer1 = serializers.key_serializer(qs1, many=True)

#             if len(serializer1.data) != 0:

#                 qs = models.user.objects.filter(id= user_id ).distinct()
#                 s1 = serializers.update_user_profile(qs, many=True)

#                 if len(s1.data) != 0:
#                     response = {'status': status.HTTP_200_OK,'message':'success','data':s1.data }
#                     if len(s1.data) == 0  :
#                         response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':s1.data }
#                     return Response(response, status=response['status'])

#                 else:
#                     response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'invalid key'}
#                     return Response(response, status=response['status'])

#         except:
#             response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
#             return Response(response, status=response['status'])
class update_profile(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:

        now = timezone.now()
        user_id1 = request.GET.get("user-id")
        key = request.GET.get("secret-key")
        full_name = request.GET.get("full_name")
        full_name_telugu =request.GET.get("full_name_telugu")
        description =request.GET.get("description")
        #mobile_number = request.GET.get("mobile_number")
        email = request.GET.get("email")
        org_id = request.GET.get("org_id")
        role_id = request.GET.get("role_id")
        qs1 = models.tb_application_access.objects.filter(key=key)
        serializer1 = serializers.key_serializer(qs1, many=True)

        if len(serializer1.data) != 0 :

            update_kwargs = {}
            if full_name is not None:
                update_kwargs['full_name'] = full_name
            if full_name_telugu is not None:
                update_kwargs['full_name_telugu'] = full_name_telugu
            if description:
                update_kwargs['description'] = description
            if org_id is not None:
                update_kwargs['organization_id'] = org_id
            if role_id is not None:
                update_kwargs['user_role_id'] = role_id
            if email is not None:
                update_kwargs['email'] = email

            qs = models.user.objects.filter(id=user_id1).update(**update_kwargs)
            #update_params = {}
            #if full_name:
            #    update_params["full_name"] =  full_name
            #if email :
              #  update_params["email"] = email
            #if mobile_number:
                 #update_params["mobile_number"] = mobile_number
            #models.user.objects.filter(id = user_id).update(**update_params)



                #response = {'status': status.HTTP_200_OK,'message':'success' }
            response = {'status': status.HTTP_200_OK }
            return Response(response, status=response['status'])
        else:
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
            return Response(response, status=response['status'])

class update_profileimg(APIView):
    @classmethod
    #it is a method that depend on that run on the class itself,rather than on an instance of the class
    def get_extra_actions(cls):
        return []
    def get(self,request):
        #try:
        # this will return current date and time in the timezone for example settings by UTC
        now = timezone.now()
        #used to retrive the value of user-id if the parameter is not present in the request none will be returned
        user_id  = request.GET.get("user-id")
        #used to retrive the value of a specific query string parameter it will return the value of the secret-key
        key = request.GET.get("secret-key")
        #used to retrive the user_profile_img
        user_profile_img = request.GET.get("user_profile_img")
        #query that retrive all objects of the tb_application_access the filter method is used to retrive objects that match the given criteria key attribute is equal to key variable
        qs1 = models.tb_application_access.objects.filter(key=key)
        #key_serializer is a class that defines the object in the queryset should be serializer many=True argument indicates that queryset contains multiple objects this method call would return Json-formatted string
        serializer1 = serializers.key_serializer(qs1, many=True)
        # statement checks the length of the serializedata not equal to zero then it goes to if condition part
        if len(serializer1.data) != 0 :
            # this method call query that update the user_profile_img attribute of all objects of a given model that have id is equal to user_id
            qs = models.user.objects.filter(id=user_id).update(user_profile_img=user_profile_img)
                #response = {'status': status.HTTP_200_OK,'message':'success' }
            #the http_200_ok method likely return a numeric HTTP status code which is used to indicate the request was successfull
            # the status of object contains a number of different http status code
            response = {'status': status.HTTP_200_OK }
            return Response(response, status=response['status'])
        else:
            #http_400_bad request indicates that the server cannot or will not process the request
            response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
            return Response(response, status=response['status'])
        #except:
        #    response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Bad Request'}
        #    return Response(response, status=response['status'])


class check_phone_no_status(APIView):
    @classmethod
    
    def get(self,request):
        #try:
        result = False
        phone_no= request.GET.get("phone_no")
        if phone_no is not None:
            if len(phone_no) != 10 or not phone_no.isnumeric():
                result = "Invalid phone number." 
                response = {'status': status.HTTP_400_BAD_REQUEST }
                return Response(result, status=response['status'])
            else:
                # qs = models.user_phonenumber_map.objects.all().distinct()
                # serializer = serializers.phonenumber_exist(qs, many=True)
                qs2 = models.user_phonenumber_map.objects.filter(phone_no=phone_no)
                qs2 = models.user_phonenumber_map.objects.filter(phone_no__contains={"phone_no":f"{phone_no}"})
                serializer2 = serializers.phonenumber_exist(qs2, many=True)
                result = True if len(serializer2.data)==1 else False
 
        response = {'status': status.HTTP_200_OK }
        return Response(result, status=response['status'])


class application_access_list(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            # Get all application access records
            qs = models.tb_application_access.objects.all()
            serializer = serializers.key_serializer(qs, many=True)
            
            if len(serializer.data) > 0:
                response = {'status': status.HTTP_200_OK, 'message': 'success', 'data': serializer.data}
            else:
                response = {'status': status.HTTP_204_NO_CONTENT, 'message': 'No content', 'data': serializer.data}
            
            return Response(response, status=response['status'])
        
        except Exception as e:
            response = {'status': status.HTTP_400_BAD_REQUEST, 'message': 'error', 'error': str(e)}
            return Response(response, status=response['status'])
        
class AnalyticsView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    ISO_TIMEZONE_SUFFIX = '+00:00'
    DEVICE_TYPES = ['mobile', 'tablet', 'other']
    OS_TYPES = ['android', 'ios', 'other']
    DEFAULT_THRESHOLD_MINUTES = 30

    def get(self, request):
        try:
            query_type = request.query_params.get('type', 'active-users')
            
            if query_type == 'user-devices':
                return self._get_user_devices(request)
            else:
                return self._get_active_users(request)
                
        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'message': 'Error retrieving analytics',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _parse_iso_datetime(self, date_str, fallback=None):
        """Parse ISO datetime string with timezone handling."""
        if not date_str:
            return fallback
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str.replace('Z', self.ISO_TIMEZONE_SUFFIX))
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return fallback

    def _apply_org_filter(self, queryset, org_id):
        """Apply organization filter if org_id is provided."""
        if org_id:
            queryset = queryset.filter(user__organization_id=org_id)
        return queryset

    def _calculate_breakdown(self, queryset, categories, field):
        """Calculate breakdown counts for categories."""
        return {cat: queryset.filter(**{field: cat}).count() for cat in categories}

    def _get_user_devices(self, request):
        """Handle user-devices query type."""
        user_id = request.query_params.get('user_id')
        
        if not user_id:
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                'message': 'user_id is required for user-devices query'
            }, status=status.HTTP_400_BAD_REQUEST)

        devices_qs = models.UserDeviceManagement.objects.filter(
            user_id=user_id
        ).order_by('-last_used')

        date_from = request.query_params.get('date_from')
        if date_from:
            date_from_dt = self._parse_iso_datetime(date_from)
            if date_from_dt:
                devices_qs = devices_qs.filter(last_used__gte=date_from_dt)

        serializer = serializers.UserDeviceManagementSerializer(devices_qs, many=True)
        return Response({
            'status': status.HTTP_200_OK,
            'message': 'Devices retrieved successfully',
            'data': serializer.data,
            'count': devices_qs.count()
        }, status=status.HTTP_200_OK)

    def _get_active_users(self, request):
        """Handle active-users query type."""
        threshold_minutes = int(request.query_params.get('threshold_minutes', self.DEFAULT_THRESHOLD_MINUTES))
        org_id = request.query_params.get('org_id')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')

        # Parse time window
        threshold_time = self._parse_iso_datetime(
            date_from, 
            timezone.now() - timedelta(minutes=threshold_minutes)
        )
        threshold_end = self._parse_iso_datetime(date_to, timezone.now())

        # Get active devices in time window
        active_devices_query = models.UserDeviceManagement.objects.filter(
            last_used__gte=threshold_time,
            last_used__lte=threshold_end
        )
        active_devices_query = self._apply_org_filter(active_devices_query, org_id)

        # Get currently active devices
        currently_active_query = models.UserDeviceManagement.objects.filter(is_active=True)
        currently_active_query = self._apply_org_filter(currently_active_query, org_id)

        # Get all devices
        total_devices_query = models.UserDeviceManagement.objects.all()
        total_devices_query = self._apply_org_filter(total_devices_query, org_id)

        # Calculate breakdowns
        active_device_breakdown = self._calculate_breakdown(
            active_devices_query, self.DEVICE_TYPES, 'device_type'
        )
        active_os_breakdown = self._calculate_breakdown(
            active_devices_query, self.OS_TYPES, 'device_os'
        )
        total_device_breakdown = self._calculate_breakdown(
            total_devices_query, self.DEVICE_TYPES, 'device_type'
        )
        total_os_breakdown = self._calculate_breakdown(
            total_devices_query, self.OS_TYPES, 'device_os'
        )

        return Response({
            'status': status.HTTP_200_OK,
            'message': 'Active users retrieved successfully',
            'data': {
                'time_window': {
                    'from': threshold_time.isoformat(),
                    'to': threshold_end.isoformat(),
                    'threshold_minutes': threshold_minutes
                },
                'in_window': {
                    'active_users': active_devices_query.values('user_id').distinct().count(),
                    'active_devices': active_devices_query.count(),
                    'device_breakdown': active_device_breakdown,
                    'os_breakdown': active_os_breakdown
                },
                'all_time': {
                    'total_devices': total_devices_query.count(),
                    'currently_active_devices': currently_active_query.count(),
                    'device_breakdown': total_device_breakdown,
                    'os_breakdown': total_os_breakdown
                },
                'timestamp': timezone.now().isoformat()
            }
        }, status=status.HTTP_200_OK)
        

class DeviceManagementView(APIView):

    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    ACTION_MESSAGES = {
        'login':  'Device login recorded successfully',
        'logout': 'Device logout recorded successfully',
    }

    def _normalize_device_id(self, device_id):
        return str(device_id or '').strip()

    def post(self, request):
        try:
            serializer = serializers.DeviceActionSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            action = serializer.validated_data.get('action')

            user_id = request.user.id
            device_id = self._normalize_device_id(serializer.validated_data.get('device_id'))

            if not device_id:
                return Response({
                    'status': status.HTTP_400_BAD_REQUEST,
                    'message': 'Invalid data',
                    'errors': {'device_id': ['This field may not be blank.']}
                }, status=status.HTTP_400_BAD_REQUEST)

            payload = {
                'device_type': serializer.validated_data.get('device_type', 'mobile'),
                'model':       serializer.validated_data.get('model', ''),
                'os':          serializer.validated_data.get('os', ''),
                'device_name': serializer.validated_data.get('device_name', device_id),
            }

            # Fire-and-forget — Django thread freed immediately.
            # Worker handles the DB write for both login and logout.
            process_device_management_action.delay(action, user_id, device_id, payload)

            return Response({
                'status': status.HTTP_200_OK,
                'message': self.ACTION_MESSAGES.get(action, 'Action recorded successfully'),
                'data': {}
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'status': status.HTTP_500_INTERNAL_SERVER_ERROR,
                'message': 'Error processing request',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

