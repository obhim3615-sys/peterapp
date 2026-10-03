from rest_framework.views import APIView
from app_farm import models
from app_farm.utils import constants
from rest_framework import status
import json
import requests
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from . import validator, serializer
from app_farm.utils.response import req_response
from app_farm.utils import helper
from django.db import transaction, IntegrityError
from app_farm.services.auth.serializer import CreateFarmerSerializer
from django.utils import timezone
from django.conf import settings
from app_farm.utils import constants,response as res
from core.views import BaseViewWithoutAuthentication
from rest_framework.pagination import PageNumberPagination


class GetOrgList(BaseViewWithoutAuthentication):
    def get_org_list(self, request, err_code, req_data):
        if not helper.verify_secret_key(req_data['secret_key']):
            return req_response(constants.INVALID_KEY, False, err_code+'3', status.HTTP_400_BAD_REQUEST)
        
        organizations = models.organizations.objects.filter(org_name__icontains= req_data['search_by_name']).annotate(distance=Distance("geometry", Point(float(req_data['long']), float(req_data['lat']), srid=4326))).order_by("-is_verified","distance")[0:20]
        data = serializer.GetOrgListSerializer(organizations, many=True)

        if len(data.data) == 0:
            return req_response(constants.NO_CONTENT, True, '', status.HTTP_204_NO_CONTENT)
        
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data.data)
        
    def post(self, request):
        return self.common_function(request, 'AFSAA-GRGET-', validator.GetOrgListValidator, self.get_org_list)


class GetOrganisationList(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 

    # number of items per page by default
    page_size = 50
    # max number of items per page
    max_page_size = 100
    model=models.user 


    def get_queryset(self,data):
        queryset = models.organizations.objects.all()
        
        if data.get('name'):
            queryset=queryset.filter(org_name__icontains=data.get('name'))
        return queryset
    

    def get(self,request):
        queryset = self.get_queryset(request.GET)
        page = self.paginate_queryset(queryset,request)
        
        serializer_data = serializer.GetOrgListSerializer(page, many=True)
        return res.req_response("Data found",True,"",status.HTTP_200_OK,self.get_paginated_response(serializer_data.data).data)

class GetOrgTypesList(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def post(self, request):
        try:
            if request.data == None:
                return req_response(constants.EMPTY_REQ_BODY, False, 'AFSOA-GOTLPOS-1', status.HTTP_400_BAD_REQUEST)

            body_data = request.data
            if type(body_data) == str:
                body_data = json.loads(body_data)
            validation = validator.GetOrgTypesValidator(data=body_data)

            if not validation.is_valid():
                return req_response(constants.INVALID_BODY, False, 'AFSOA-GOTLPOS-2', status.HTTP_400_BAD_REQUEST, validation.errors)
            
            if not helper.verify_secret_key(body_data['secret_key']):
                return req_response(constants.INVALID_KEY, False, 'AFSOA-GOTLPOS-03', status.HTTP_400_BAD_REQUEST)

            types = models.OrgType.objects.all()
            data = serializer.GetOrgTypesListSerializer(types, many=True)

            if len(data.data) == 0:
                return req_response(constants.NO_CONTENT, True, '', status.HTTP_204_NO_CONTENT)
            
            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data.data)
        except Exception as e:
            return req_response(constants.ERROR, False, 'AFSOA-GOTLPOS-4', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)
        
class GetOrgDetail(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []
    def post(self, request):
        try:
            if request.data == None:
                return req_response(constants.EMPTY_REQ_BODY, False, 'AFSOA-GODPOS-1', status.HTTP_400_BAD_REQUEST)

            body_data = request.data
            if type(body_data) == str:
                body_data = json.loads(body_data)
            validation = validator.GetOrgDetailValidator(data=body_data)

            if not validation.is_valid():
                return req_response(constants.INVALID_BODY, False, 'AFSOA-GODPOS-2', status.HTTP_400_BAD_REQUEST, validation.errors)

            organization = models.organizations.objects.get(id= body_data['org_id'])

            data = serializer.GetOrgDetailSerializer(organization, many=False)
            data = {
                'org_name': data.data['org_name'],
                'address': {
                    'state': data.data['state'],
                    'district': data.data['district'],
                    'village': data.data['village'],
                    'taluka': data.data['taluka'],
                    'country': data.data['country']
                },
                'directors': {
                    'heading': "Director's Name",
                    'rows': [
                    #     {
                    #     'heading': 'Director',
                    #     'value': 'Hariom Sekhawat'
                    # },{
                    #     'heading': 'Director',
                    #     'value': 'Hariom Sekhawat'
                    # },{
                    #     'heading': 'Director',
                    #     'value': 'Hariom Sekhawat'
                    # },{
                    #     'heading': 'Director',
                    #     'value': 'Hariom Sekhawat'
                    # },{
                    #     'heading': 'Director',
                    #     'value': 'Hariom Sekhawat'
                    # },{
                    #     'heading': 'Director',
                    #     'value': 'Hariom Sekhawat'
                    # }
                    ]
                },
                'profit_loss_section': {
                    'heading': 'Profit Loss Details',
                    'rows': [{
                        'heading': 'Share Capital',
                        'value': data.data['share_capital']
                    },{
                        'heading': 'Paid Capital',
                        'value': data.data['paid_capital']
                    }]
                }
            }
            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data)
        except Exception as e:
            return req_response(constants.ERROR, False, 'AFSOA-GODPOS-3', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)
        
class OrgCreate(BaseViewWithoutAuthentication):
    @classmethod
    def get_extra_actions(cls):
        return []
    
    def org_create(self, request, err_code, req_data):
        if not helper.verify_secret_key(req_data['secret_key']):
            return req_response(constants.INVALID_KEY, False, err_code+'3', status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            try:
                org = models.organizations.objects.create(
                    org_name = req_data['org_name'],
                    acres = req_data['land_size'],
                    number_of_members = req_data['members'],
                    members = req_data['members'],
                    type_of_org_id = req_data['role'],
                    pincode = req_data['pincode'],
                    country = req_data['country'],
                    state = req_data['state'],
                    district = req_data['district'],
                    taluka = req_data['taluka'],
                    village = req_data['village'],
                    latitude = req_data['lat'],
                    longitude = req_data['long'],
                    fpo_contact_no = req_data['phone'],
                    geometry = Point(float(req_data['lat']), float(req_data['long']))
                )
            except IntegrityError:
                return req_response(constants.ERROR, False, err_code+'4', status.HTTP_409_CONFLICT, None, constants.DUPLICATE_ORG)
            
            org.crops_interest.add(*req_data['crop_id'])
            current_time = timezone.now()

            try:
                user = models.user.objects.create(
                    language_selected_id = req_data['language_selected'],
                    mobile_number = req_data['phone'],
                    user_role_id = req_data['role'],
                    otp_verfied = True,
                    installed_app = True,
                    timestamp_first_login = current_time,
                    timestamp_login = current_time,
                    firebase_token = req_data['fcm_token'],
                    full_name = req_data['name'],
                    organization = org,
                    address_pincode = req_data['pincode'],
                    address_country = req_data['country'],
                    address_state = req_data['state'],
                    address_district = req_data['district'],
                    address_taluka = req_data['taluka'],
                    address_village = req_data['village'],
                    latitude = req_data['lat'],
                    longitude = req_data['long'],
                    land_size = req_data['land_size'],
                    land_size_unit = req_data['land_size_unit'],
                    country_id = req_data['country_id'],
                )
            except IntegrityError:
                return req_response(constants.ERROR, False, err_code+'5', status.HTTP_409_CONFLICT, None, constants.DUPLICATE_USER)
            
            user.crops_interest.add(*req_data['crop_id'])

            token= models.AuthenticationToken.objects.create(user=user)
            token.save()
            user = CreateFarmerSerializer(user, many=False)

            return req_response(constants.USER_CREATION_SUCCESS, True, '', status.HTTP_201_CREATED, {
                **user.data,
                'token': str(token)
            })
        
    def post(self, request):
        return self.common_function(request, "AFSOA-OCPOS-", validator.OrgCreateValidator, self.org_create)
        
    
class SendNotification(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def post(self, request):
        try:
            # if request.data == None:
            #     return req_response(constants.EMPTY_REQ_BODY, False, 'AFSOA-SNPOS-1', status.HTTP_400_BAD_REQUEST)

            # body_data = request.data
            # if type(body_data) == str:
            #     body_data = json.loads(body_data)
            # validation = validator.SendNotificationValidator(data=body_data)

            # if not validation.is_valid():
            #     return req_response(constants.INVALID_BODY, False, 'AFSOA-SNPOS-2', status.HTTP_400_BAD_REQUEST, validation.errors)

            # users = models.user.objects.filter(organization= body_data['org_id'])
            # data = serializer.SendNotificationSerializer(users, many=True)

            # for user in data.data:
            #     try:
            #         deviceToken = user['firebase_token']
            #         if deviceToken:
            #             url1 = settings.GOOGLE_PUSH_NOTIFICATION_URL+settings.GOOGLE_SERVER_TOKEN
                    
            #             payload1 = json.dumps({
            #                 "to": deviceToken,
            #                 "notification": {
            #                     "body": body_data['msg'],
            #                     "title": 'Message from Admin',
            #                     "sound": "ggnotisound.mp3"
            #                 }
            #             })
            #             headers1 = {
            #                 'Content-Type': 'application/json',
            #                 'Authorization': 'key='+settings.GOOGLE_SERVER_TOKEN
            #             }

            #             response1 = requests.request("POST", url1, headers=headers1, data=payload1)
            #             if json.loads(response1.text)['success'] == 0:
            #                 print(response1.text)
            #     except:
            #         print("Notification not sent to " + str(user['mobile_number']))
            
            return req_response("API is deprecated", False, '', status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return req_response(constants.ERROR, False, 'AFSOA-SNPOS-3', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)


class UploadOrganizationDoc(APIView):
    def post(self,request):
        data= request.POST
        validation = validator.UploadDocValidator(data=data)
        if not validation.is_valid():
                return req_response(constants.INVALID_BODY, False, 'AFSOA-OCPOS-2', status.HTTP_400_BAD_REQUEST, validation.errors)
        
        if not helper.verify_secret_key(data['secret_key']):
                return req_response(constants.INVALID_KEY, False, 'AFSOA-OCPOS-03', status.HTTP_400_BAD_REQUEST)
        
        user= models.user.objects.filter(id=data['user_id']).get()
        organization= models.organizations.objects.filter(id=data['org_id']).get()
        # print(organization)
        msg="Bad Request"
        if user and organization:
            files= request.FILES.getlist('docs')
            # print(files)

            if isinstance(files,list):
                if len(files)>0:
                    for i in files:
                        url=helper.image_upload(i)
                        if(url):
                            models.OrganizationDoc.objects.create(
                                user=user,
                                organization=organization,
                                doc_url=url
                            )
                            return req_response("Doc uploaded", True, '', status.HTTP_201_CREATED, {
                            })

                        else:
                            msg="Could not upload file"
                    
            else:
                msg="File not found"
        else:
            msg="User not found"

        return req_response(msg, False, '', status.HTTP_400_BAD_REQUEST, {
                        })

class GetTags(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 

    def get(self,request):
        tags = models.Tag.objects.all()
        serialized= serializer.TagSerializer(tags,many=True)
        data=[]
        if serialized:
            data=serialized.data

        return res.req_response("Tag data found",True,"",status.HTTP_200_OK,data)


class GetOrganizationWithTag(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 

    def get(self,request):
        tag_ids=request.GET.get('tag_id')
        name_query=request.GET.get('name_query')
        data=[]
        if(tag_ids):
            tag_ids=tag_ids.split(',')
            organization= models.TagOrganization.objects.filter(tag_id__in=tag_ids)
            if name_query:
                # print(name_query)
                organization=organization.filter(organization__org_name__contains=name_query)
            organization=organization.all()
            serialized=serializer.TagOrganizationSerializer(organization,many=True)
            
            if serialized:
                data= serialized.data

            return res.req_response("Organization of Tag data found",True,"",status.HTTP_200_OK,data)
        return res.req_response("Organization of Tag data not found",False,"",status.HTTP_400_BAD_REQUEST,data)



class GetAgendas(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 

    def get(self,request):
        agenda=[]
        page=models.agenda.objects.filter(status=True).all()
        if page:   
            agenda=serializer.AgendaSerializer(page,many=True).data
            
        return res.req_response("Data found",True,"",status.HTTP_200_OK,agenda)


class UpdateOrganizationValues(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 
    def post(self,request):
        try:
            org_id= request.data.get('org_id')
            turnover= request.data.get('turnover')
            active_date= request.data.get('active_date')
            member_associate= request.data.get('member_associate')

            models.organizations.objects.filter(id=org_id).update(
                turnover=turnover,
                active_date=active_date,
                member_associate=member_associate
            )

            return res.req_response("Data updated",True,"",status.HTTP_200_OK)
        except Exception as e:
            return req_response(constants.ERROR, False, 'AFSOUO-POS-1', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)


