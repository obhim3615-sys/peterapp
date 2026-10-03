from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
import json

from app_farm.utils import constants
from app_farm.authentication import CustomTokenAuthentication
from app_farm.utils.response import req_response
from . import models,serializer,validator
from app_farm.models import user,farm
from app_farm.serializers import org_member_listSerializer,FarmSerializerVikshep
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.http import HttpResponseServerError
from django.core.exceptions import ImproperlyConfigured
from datetime import  date
from django.db.models import Q,F,Value,CharField
from django.db.models.functions import Concat,TruncDate
from io import StringIO
import csv
from libraries.doms import DomsSignedURL
from libraries.noms import NoMS
from cms.models import Setting

class CommonFunctionMixin:
    @classmethod
    def get_extra_actions(cls):
        return []

    def common_function(self, request, err_code, validator, main_function):
        request_data = None
        try:
            request_data = request.GET if request.method == 'GET' else request.data
            if request_data == None:
                return req_response(constants.EMPTY_REQ_BODY, False, err_code+'1', status.HTTP_400_BAD_REQUEST)

            if type(request_data) == str:
                request_data = json.loads(request_data)

            if validator:
                validation = validator(data=request_data)

                if not validation.is_valid():
                    return req_response(constants.INVALID_BODY, False, err_code+'2', status.HTTP_400_BAD_REQUEST, validation.errors)
            
            return main_function(request, err_code, request_data)
        except Exception as e:
            print("Req Body --> ", request_data)
            return req_response(constants.ERROR, False, err_code+'EXC', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)

class BaseView(APIView, CommonFunctionMixin):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

class BaseViewWithoutAuthentication(APIView, CommonFunctionMixin):
    pass

class GetCountryList(BaseViewWithoutAuthentication):
    def get_country_list(self, request, err_code, request_data):
        countries = models.Country.objects.all()
        data = serializer.GetCountriesSerializer(countries, many=True)
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data.data)

    def get(self, request):
        return self.common_function(request, 'CV-GCLGET-', None, self.get_country_list)
    
class GetCustomFormDetails(BaseView):
    def get_custom_form_details(self, request, err_code, req_data):
        """
        Function to get the Form details (Fields) acc to 'form_id' we get from frontend.
        """
        custom_form_details = models.CustomForm.objects.get(id = req_data['form_id'])
        data = serializer.GetCustomeFormSerializer(custom_form_details, many=False)
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data.data)

    def get(self, request):
        return self.common_function(request, 'CV-GCLGET-', validator.GetCustomFormDetails, self.get_custom_form_details)
    
class GetCustomForms(BaseView):
    def get_custom_forms(self, request, err_code, req_data):
        """
        Function to get the Multiple Forms with details (Fields) acc to 'type' we get frontend.
        """
        if req_data.get('type'):
            custom_forms = models.CustomForm.objects.filter(type = req_data['type'])
            
            if req_data.get('id'):
                custom_form_parent_ids = models.CustomFormParent.objects.filter(custom_form_parent_id=req_data.get('id')).values_list('custom_form_child', flat=True)
                custom_forms=custom_forms.filter(id__in= custom_form_parent_ids).all()
        else:
            custom_forms = models.CustomForm.objects.all()
        data = serializer.GetCustomeFormSerializer(custom_forms, many=True)
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data.data)

    def get(self, request):
        return self.common_function(request, 'CV-GCLGET-', None, self.get_custom_forms)

class GetUserAjax(APIView):
    def get(self,request):
        data=request.GET
        user_name= data.get('user')
        
        user_data=None
        if user_name:
            user_data=user.objects.filter(full_name__contains=user_name).order_by('full_name').all()[:50]
            user_data=org_member_listSerializer(user_data,many=True) if user_data else None   
            if user_data:
                user_data=user_data.data
        else:
            user_data=user.objects.all()[:50]
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, user_data)

@require_GET
def liveness(request):
    """
    Liveness probe view.
    """
    return JsonResponse({'status': 'ok'})

@require_GET
def readiness(request):
    """
    Readiness probe view.
    """
    try:
        # Check if database is accessible
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
    except ImproperlyConfigured as e:
        # If database connection fails, return server error
        return HttpResponseServerError('Database connection failed')

    # Add more readiness checks as needed

    return JsonResponse({'status': 'ok'})


class SearchUserByNamePhone(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
        data=request.GET
        user_name= data.get('user')
        organization= request.user.organization
        user_data=None
        if user_name:
            user_data = user.objects.filter(Q(full_name__istartswith=user_name) | Q(mobile_number__icontains=user_name),organization=organization).order_by('full_name')[:50]
            
        else:
            user_data=user.objects.filter(organization=organization).order_by('full_name').all()[:50]

        user_data=org_member_listSerializer(user_data,many=True) if user_data else None   
        if user_data:
            user_data=user_data.data
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, user_data)



class SendDailyFarmAddedDetails(APIView):
    
    def get(self, request):
        # Get the current date
        today_date = date.today()

        # Filter farms created today
        farms_created_today = farms_created_today = farm.objects.filter(
            updated_on_timestamp__date=today_date,
            latitude__isnull=False,
            longitude__isnull=False,
        ).select_related(
            'crop_id', 'org_id'
        ).annotate(
            farmer_name=F('name'),
            farm_area=F('total_area'),
            farm_addition_date=TruncDate('updated_on_timestamp'),
            farmer_mobile_number=F('farmer_contact'),
            farm_latitude=F('latitude'),
            farm_longitude=F('longitude'),
            farm_crop=F('crop_id_id__crop_name'),
            company_id=F('org_id__company_id'),
            org_name=F('org_id__org_name'),
            farm_id=F('id'),
            prakshep_id=Concat(F('org_id__company_id'), Value('_'), F('id'), output_field=CharField()),
        )
        
        # print(farms_created_today)
        
        data={}
        if farms_created_today:
            # Serialize the farms data
            serializer = FarmSerializerVikshep(farms_created_today, many=True)
            data =serializer.data
            # Create CSV data from serialized data
            csv_data = self.create_csv(serializer.data)

            # Upload CSV file to DOMS
            doms_url_handler = DomsSignedURL()
            generate_url_payload = {
                'contentType': 'text/csv',
                'originalFileName': 'daily_farm_data.csv'
            }

            signed_url_response = doms_url_handler.generate_signed_url(generate_url_payload)
            # print(signed_url_response)
            if signed_url_response.get('success') :
                attachment_url= signed_url_response['payload']['downloadUrl']
                # print("----------------------------------- I am here--------------------")
                signed_url = signed_url_response['payload']['signedUrl']
                file_content = csv_data.encode('utf-8')
                content_type = 'text/csv'
                original_file_name = 'daily_farm_data.csv'
                
                upload_payload = {
                    'signed_url': signed_url,
                    'file_content': file_content,
                    'content_type': content_type,
                    'original_file_name': original_file_name
                }
                # print(upload_payload)
                upload_response = doms_url_handler.upload_file(upload_payload)
                # print(upload_response)
                if upload_response.status_code == 200:
                    # Send email
                    try:
                        ccList=Setting.objects.getKey('SEND_FARM_DATA_CSV_TO')
                        if ccList:
                            ccList=ccList.value
                    except Setting.DoesNotExist:
                        ccList=""
                    subject = "CSV data for number of farms"
                    send_to = "nitin.tiwari@arya.ag"
                    text = 'Attached is the daily farm data.'
                    mail_sent=self.send_mail_with_attachment(send_to,subject,text,attachment_url,ccList)
                    # print(mail_sent)
                    # Send email with CSV attachment
                    

        # Respond with success message
        return req_response('Farm details sent via email.', True,"", status.HTTP_200_OK, data)

    def create_csv(self, data):
        # Create a CSV string from the data
        csv_data = StringIO()
        csv_writer = csv.writer(csv_data)
        # Write header
        if len(data):
            csv_writer.writerow(data[0].keys())
            # Write data
            for item in data:
                csv_writer.writerow(item.values())
            return csv_data.getvalue()

    def send_mail_with_attachment(self,send_to, subject, text, attachment,ccList):    
        
        noms= NoMS()
        return noms.send_email(text,"email_default",send_to,"aryaAgInfo",subject,[{"fileName":"Attachments.csv","documentUrl":attachment}],ccList)   