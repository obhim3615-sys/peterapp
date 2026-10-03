from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import json, requests
from io import StringIO
from django.conf import settings

from app_farm.utils import constants,response as res
from app_farm.models import user
from app_farm.utils.response import req_response
from app_farm.authentication import CustomTokenAuthentication
from app_farm.utils.mixin.subscription import SubscriptionRequiredMixin
from . import models, serializer, validator
from libraries.push_notification import FirebaseHelper
from app_farm.utils.helper import deductValidityNumber
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination


from broadcast.models import *
from broadcast.serializer import *
# Create your views here.
class GetSmsTemplateList(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self, request):
        try:
            language = request.GET.get("language")
            if not language:
                return req_response(constants.INVALID_BODY, False, 'BV-GSTLGET-1', status.HTTP_400_BAD_REQUEST)
            
            if language != '2':
                language = '1'
            
            content = models.SmsTemplate.objects.filter(language=language).order_by('order')
            data = serializer.GetSmsTemplateListSerializer(content, many=True)

            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data.data)
        except Exception as e:
            return req_response(constants.ERROR, False, 'BV-GSTLGET-2', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)


class GetSmsTemplateDetail(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self, request):
        try:
            sms_template_id = request.GET.get("template_id")
            if not sms_template_id:
                return req_response(constants.INVALID_BODY, False, 'BV-GSTDGET-1', status.HTTP_400_BAD_REQUEST)

            content = models.SmsTemplate.objects.get(id=sms_template_id)
            data = serializer.GetSmsTemplateDetailSerializer(content, many=False)

            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data.data)
        except Exception as e:
            return req_response(constants.ERROR, False, 'BV-GSTDGET-2', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)

# Function to send notifications
def send_notification(contacts, msg):
    # Fetch the user tokens
    tokens = user.objects.filter(mobile_number__in=contacts,firebase_token__isnull=False).distinct().values_list('firebase_token', flat=True)
    firebasehelper=FirebaseHelper(use_adc=True)
    # Convert the queryset to a list
    tokens_list = list(tokens)
    # Define the batch size
    batch_size = 500
    # Split the list of tokens into batches
    token_batches = [tokens_list[i:i + batch_size] for i in range(0, len(tokens_list), batch_size)]

    for batch in token_batches:
        # Send notifications for each batch of tokens
        firebasehelper.send_push_notification(list(batch), 'Message from Admin', msg, 'ggnotisound.mp3')

class SendGroupSms(APIView, SubscriptionRequiredMixin):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []
    def post(self, request):
        try:
            if request.data == None:
                return req_response(constants.EMPTY_REQ_BODY, False, 'BV-SGSPOS-1', status.HTTP_400_BAD_REQUEST)

            # Check the request body validity
            body_data = request.data
            if type(body_data) == str:
                body_data = json.loads(body_data)
            validation = validator.SendGroupSmsValidator(data=body_data)

            if not validation.is_valid():
                return req_response(constants.INVALID_BODY, False, 'BV-SGSPOS-2', status.HTTP_400_BAD_REQUEST, validation.errors)

            # Check the validity for SMS service
            data = self.check_service(request,'sms')
            if not data['status']:
                data['error_code']="BV-SGSPOS-03"
                return req_response(data['message'],data['status'],data['error_code'],data['status_code'])
            
            remaining_service = data['remaining']
            requested_number_of_contact=len(body_data['contacts'])
            if requested_number_of_contact>remaining_service:
                return req_response("You do not have enough sms remaining to send", False, "BV-SGSPOS-04", status.HTTP_400_BAD_REQUEST)
            
            # Prepare the CSV content
            csv_content = "Phone\n"
            for phone in body_data['contacts']:
                csv_content += phone + "\n"

            # Create a CSV file-like object from the content
            csv_file = StringIO(csv_content)

            # Call the Group SMS api
            url = settings.SMS_URL
            payload = {
                'userid': settings.SMS_USER_ID,
                'password': settings.SMS_PASSWORD,
                'msg': body_data['msg'],
                'senderid': settings.SMS_SENDER_ID,
                'duplicatecheck': 'true',
                'output': 'json',
                'sendMethod': 'bulkupload',
                'msgType': body_data['msg_type'],
                'dltTemplateId': body_data['template_id']
            }
            files=[
                ('file',('sample_file.csv',csv_file,'text/csv'))
            ]
            headers = {
                'apikey': settings.SMS_API_KEY,
                'Cookie': 'SERVERID=webC1'
            }

            response = requests.request("POST", url, headers=headers, data=payload, files=files)
            response = json.loads(response.text)
            if response['status'] == 'success':
                # If the Group SMS api is success then deduct that number of msgs from SMS service
                deductValidityNumber(request.user,'sms',len(body_data['contacts']))

                if body_data['send_notification']:
                    send_notification(body_data['contacts'], body_data['msg'])
                return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)
            
            return req_response(constants.ERROR, False, 'BV-SGSPOS-5', status.HTTP_500_INTERNAL_SERVER_ERROR, None, response['reason'])
        except Exception as e:
            print(e)
            return req_response(constants.ERROR, False, 'BV-SGSPOS-6', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)


class GetCommunitiesShare(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=CommunitiesShare 

    def get_queryset(self):
        organization= self.request.user.organization

        # Fetch all values where organization is either null or matches current user's organization
        queryset = CommunitiesShare.objects.filter(
            Q(organization__isnull=True) | Q(organization=organization),
            status=True
        )

        return queryset

    def get(self,request):
        queryset = self.get_queryset()      
        page =  self.paginate_queryset(queryset,request)

        communities=None
        if page:          
            communities=CommunitiesShareSerializer(page,many=True).data
            if communities:
                communities=self.get_paginated_response(communities).data
        
        if not communities:
            communities=None
        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,communities)