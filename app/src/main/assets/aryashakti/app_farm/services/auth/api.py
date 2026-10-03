from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist
from app_farm import models
from app_farm.utils import constants,helper,response as res
from rest_framework.response import Response
from rest_framework import status
import json, random
from django.utils import timezone
from . import validator
from . import serializer        
from app_farm.utils.response import req_response
from django.conf import settings
from core.views import BaseView, BaseViewWithoutAuthentication
from core.models import WhiteListedMobile
from libraries.noms import NoMS

class OtpVerify(BaseViewWithoutAuthentication):
    def otp_verify(self, request, err_code, req_data):
        if not helper.verify_secret_key(req_data['secret_key']):
            return req_response(constants.INVALID_KEY, False, err_code+'3', status.HTTP_400_BAD_REQUEST)
        phone = req_data['country_code'] + str(req_data['phone'])

        try:
            WhiteListedMobile.objects.get(phone=req_data['phone'],otp=req_data['otp'])
        except ObjectDoesNotExist:
            try:
                models.OTPValidation.objects.get(phone_number=phone,otp_value=req_data['otp'],status=0).delete()
            except ObjectDoesNotExist:
                return req_response(constants.INVALID_OTP, False, err_code+'4', status.HTTP_400_BAD_REQUEST)
            
        users = models.user.objects.filter(mobile_number__icontains=req_data['phone'])
        data = {}
            
        if len(users) == 0:
            data['existing_user'] = False
            return req_response(constants.VALID_OTP, True, '', status.HTTP_200_OK, data)
        
        if('device_name' in req_data.keys()):
            try:
                device= models.DeviceData.objects.filter(device_name=req_data['device_name']).get()
            except models.DeviceData.DoesNotExist:
                device=None
            add_device(users[0],req_data,device)
        
        current_time = timezone.now()
        users[0].firebase_token = req_data['fcm_token']
        users[0].installed_app = True
        users[0].timestamp_login = current_time
        users[0].otp_verfied = True
        if not users[0].timestamp_first_login:
            users[0].timestamp_first_login = current_time
        users[0].save()
        token= models.AuthenticationToken.objects.update_or_create(user=users[0])
        
        user = serializer.VerifyOtpSerializer(users[0], many=False)
        data['token'] = str(token[0])
        data['existing_user'] = True
        data['data'] = user.data
        return req_response(constants.VALID_OTP, True, '', status.HTTP_200_OK, data)
    
    def post(self, request):
        return self.common_function(request, 'AFSAA-OVPOS-', validator.VerifyOtpValidator, self.otp_verify)
        
class OtpVerifyByAdmin(BaseView):
    def otp_verify_by_admin(self, request, err_code, body_data):
        try:
            models.OTPValidation.objects.get(phone_number = body_data['phone'],otp_value=body_data['otp'],status=0).delete()
        except ObjectDoesNotExist:
            return req_response(constants.INVALID_OTP, False, err_code+'4', status.HTTP_400_BAD_REQUEST)

        mobile_number = body_data['phone'].replace('+91', '')
        try:
            user = models.user.objects.get(mobile_number__icontains= mobile_number)
            user.otp_verfied = True
            user.full_name = body_data['name']
            user.verified_by = request.user
            user.save()
        except ObjectDoesNotExist:
            return req_response(constants.USER_NOT_FOUND, False, err_code+'5', status.HTTP_400_BAD_REQUEST)

        return req_response(constants.VALID_OTP, True, '', status.HTTP_200_OK)

    def post(self, request):
        return self.common_function(request, 'AFSAA-OVBAPOS-', validator.VerifyOtpByAdminValidator, self.otp_verify_by_admin)
from cms.models import Setting
class SendOtp(BaseViewWithoutAuthentication):
    def send_otp(self, request, err_code, req_data):
        if not helper.verify_secret_key(req_data['secret_key']):
            return req_response(constants.INVALID_KEY, False, err_code+'3', status.HTTP_400_BAD_REQUEST)
        if not req_data['phone'].startswith(req_data['country_code']):
            phone = req_data['country_code']+str(req_data['phone'])
        else:
            phone = req_data['phone']
            # Remove the country code from the phone number
            #req_data['phone'] = req_data['phone'][len(req_data['country_code']):]
        
        try:
            WhiteListedMobile.objects.values('otp').get(phone=req_data['phone'])
        except ObjectDoesNotExist:
            otp = str(random.randint(100000, 999999))
            msg= "<#> Please use OTP "+otp+" to login to your Aryashakti account and get advisory and help from your FPO and our satellite based farm analysis. "+(req_data.get('unique_id') if req_data.get('unique_id') else "")
            noms = NoMS()

            doms_login_template_id=Setting.objects.getKey('DOMS_LOGIN_TEMPLATE_ID')
            sms_res = noms.send_smsv2(0, 'TRANSACTIONAL', 'User',{
                "parameterMap": "{\"otp\": \""+otp+"\", \"unique_id\" : \""+req_data.get('unique_id')+"\"}",
                "domsTemplateId": int(doms_login_template_id.value),
                "sendTo": req_data['phone'],
                "sendFrom": "aryaMK"
            },language="EN")
            # noms.send_sms(0, 'TRANSACTIONAL', 'User', {
            #     "msgBody": msg,
            #     "templateId": "1707167948516066799",
            #     "sendTo": req_data['phone'],
            #     "sendFrom": "aryaMK"
            # })
            # print(sms_res)

            if not sms_res or not sms_res['success']:               
                error="Sms API is down."
                if sms_res:
                    error=sms_res['errors']
                return req_response(constants.SEND_OTP_FAILED, False, err_code+'4', status.HTTP_400_BAD_REQUEST, error)
        
            models.OTPValidation.objects.update_or_create(
                phone_number = phone,
                defaults = {
                    'otp_value': otp,
                    'phone_number': phone,
                }
            )
        return req_response(constants.SENT_OTP, True, '', status.HTTP_200_OK)

    def post(self, request):
        return self.common_function(request, 'AFSAA-SOPOS-', validator.SendOtpValidator, self.send_otp)


class CreateFarmer(BaseViewWithoutAuthentication):
    def create_farmer(self, request, err_code, req_data):
        if not helper.verify_secret_key(req_data['secret_key']):
            return req_response(constants.INVALID_KEY, False, err_code+'3', status.HTTP_400_BAD_REQUEST)
        
        if req_data.get('is_sponsor') or req_data.get('role') == settings.IDS_BD_USER_ROLE:
            role_id = req_data['role']
        else:
            role_id = settings.IDS_FARMER_WITHOUT_FPO_USER_ROLE
        
        current_time = timezone.now()
        fetched_location = False

        if not req_data.get('lat') or not req_data.get('long'):
            fetched_location = True
            location = helper.get_lat_long_from_pin(req_data['pincode'])

        user_obj = {
            "language_selected_id": req_data['language_selected'],
            "mobile_number": req_data['phone'],
            "user_role_id": role_id,
            "otp_verfied": True,
            "installed_app": True,
            "timestamp_first_login": current_time,
            "timestamp_login": current_time,
            "firebase_token": req_data['fcm_token'],
            "full_name": req_data['name'],
            "country_id": req_data['country_id'],
        }
        
        if req_data.get('role') == settings.IDS_BD_USER_ROLE:
            user_obj['organization_id'] = req_data['org_id']
        else:
            user_obj['full_name_telugu'] = req_data.get('name_telugu')
            user_obj['address_pincode'] = req_data['pincode']
            user_obj['address_country'] = req_data['country']
            user_obj['address_state'] = req_data['state']
            user_obj['address_district'] = req_data['district']
            user_obj['address_taluka'] = req_data['taluka']
            user_obj['address_village'] = req_data['village']
            user_obj['latitude'] = location['lat'] if fetched_location else req_data['lat']
            user_obj['longitude'] = location['lng'] if fetched_location else req_data['long']

            if req_data.get('is_sponsor'):
                user_obj['org_name'] = req_data.get('org_name')
            else:
                user_obj['land_size'] = req_data['land_size']
                user_obj['land_size_unit'] = req_data['land_size_unit']
                user_obj['land_size_unit_telugu'] = req_data.get('land_size_unit_telugu')
                user_obj['user_profile_img'] = req_data.get('user_profile_img')
                user_obj['no_of_plots'] = req_data['no_of_plots']

        user = models.user.objects.create(
            **user_obj
        )
        if not req_data.get('is_sponsor') and req_data.get('role') != settings.IDS_BD_USER_ROLE:
            user.crops_interest.add(*req_data['crop_id'])

        token= models.AuthenticationToken.objects.create(user=user)
        token.save()
        user = serializer.CreateFarmerSerializer(user, many=False)

        return req_response(constants.USER_CREATION_SUCCESS, True, '', status.HTTP_201_CREATED, {
            **user.data,
            'token': str(token)
        })

    def post(self, request):
        body_data = request.data
        if type(body_data) == str:
            body_data = json.loads(body_data)

        if body_data.get('is_sponsor'):
            temp_validator = validator.CreateSponsorValidator
        elif body_data.get('role') == settings.IDS_BD_USER_ROLE:
            temp_validator = validator.CreateBdValidator
        else:
            temp_validator = validator.CreateFarmerValidator
        return self.common_function(request, "AFSAA-CFPOS-", temp_validator, self.create_farmer)

class signup(BaseViewWithoutAuthentication):
    def signup(self, request, err_code, req_data):
        if not helper.verify_secret_key(req_data['secret_key']):
            return req_response(constants.INVALID_KEY, False, err_code+'3', status.HTTP_400_BAD_REQUEST)
        
        current_time = timezone.now()

        user = models.user.objects.create(
            language_selected_id = req_data['language_selected'],
            mobile_number = req_data['phone'],
            organization_id = req_data['org_id'],
            otp_verfied = True,
            installed_app = True,
            timestamp_first_login = current_time,
            timestamp_login = current_time,
            firebase_token = req_data['fcm_token'],
            full_name = req_data['name'],
            full_name_telugu = req_data.get('name_telugu'),
            land_size = req_data['land_size'],
            land_size_unit = req_data['land_size_unit'],
            land_size_unit_telugu = req_data.get('land_size_unit_telugu'),
            address_pincode = req_data['pincode'],
            address_country = req_data['country'],
            address_state = req_data['state'],
            address_district = req_data['district'],
            address_taluka = req_data['taluka'],
            address_village = req_data['village'],
            user_profile_img = req_data['user_profile_img'],
            country_id = req_data['country_id']
        )
        if req_data.get('crop_id'):
            user.crops_interest.add(*req_data['crop_id'])
        
        token= models.AuthenticationToken.objects.create(user=user)
        token.save() 
        user = serializer.VerifyOtpSerializer(user, many=False)

        return req_response(constants.USER_CREATION_SUCCESS, True, '', status.HTTP_201_CREATED, {
            **user.data,
            'token': str(token)
        })
        
    def post(self, request):
        return self.common_function(request, "AFSAA-SPOS-", validator.SignupValidator, self.signup)


def add_device(user,body_data,device):
    if(not device):
        device= models.DeviceData.objects.create(device_name=body_data['device_name'])
    
    try:
        user_device = models.UserDevice.objects.filter(device=device,user=user).first()
    except models.UserDevice.DoesNotExist:
        user_device = None
   
    if not user_device:
        models.UserDevice.objects.create(user=user,device=device)