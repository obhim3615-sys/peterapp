from rest_framework.views import APIView
from . import models
from app_farm.models import organizations
from app_farm.utils.helper import constants
from rest_framework import status
import json
from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from . import validator, serializer
from app_farm.utils.response import req_response
from app_farm.models import user, user_roles
from django.conf import settings

class CreateFpoRequest(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []
    def post(self, request):
        try:
            if request.data == None:
                return req_response(constants.EMPTY_REQ_BODY, False, 'ARV-CFRPOS-1', status.HTTP_400_BAD_REQUEST)

            body_data = request.data
            if isinstance(body_data, str):
                body_data = json.loads(body_data)
            validation = validator.CreateFpoRequest(data=body_data)

            if not validation.is_valid():
                return req_response(constants.INVALID_BODY, False, 'ARV-CFRPOS-2', status.HTTP_400_BAD_REQUEST, validation.errors)
            
            models.Requests.objects.create(
                org_name = body_data['name'],
                org_no = body_data['phone'],
                user = request.user,
                type = "New FPO Request"
            )
            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)
        except Exception as e:
            return req_response(constants.ERROR, False, 'ARV-CFRPOS-3', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)
        
class CreateFarmerToFpoRequest(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []
    def post(self, request):
        try:
            if request.data == None:
                return req_response(constants.EMPTY_REQ_BODY, False, 'ARV-CFTFRPOS-1', status.HTTP_400_BAD_REQUEST)

            body_data = request.data
            if isinstance(body_data, str):
                body_data = json.loads(body_data)
            validation = validator.CreateFarmerToFpoRequest(data=body_data)

            if not validation.is_valid():
                return req_response(constants.INVALID_BODY, False, 'ARV-CFTFRPOS-2', status.HTTP_400_BAD_REQUEST, validation.errors)
            
            models.Requests.objects.create(
                organization = organizations.objects.get(id=body_data['org_id']),
                user = request.user,
                type = "Farmer to FPO Request",
            )
            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)
        except Exception as e:
            return req_response(constants.ERROR, False, 'ARV-CFTFRPOS-3', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)
        
class RequestsList(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []
    def post(self, request):
        try:
            if request.data == None:
                return req_response(constants.EMPTY_REQ_BODY, False, 'ARV-RLPOS-1', status.HTTP_400_BAD_REQUEST)

            body_data = request.data
            if isinstance(body_data, str):
                body_data = json.loads(body_data)
            validation = validator.RequestsListValidator(data=body_data)

            if not validation.is_valid():
                return req_response(constants.INVALID_BODY, False, 'ARV-RLPOS-2', status.HTTP_400_BAD_REQUEST, validation.errors)
            
            requests = models.Requests.objects.filter(organization=body_data['org_id'], status=body_data['status'], type='Farmer to FPO Request')
            data = serializer.RequestsListSerializer(requests, many=True)

            if len(data.data) == 0:
                return req_response(constants.NO_CONTENT, True, '', status.HTTP_204_NO_CONTENT)

            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data.data)
        except Exception as e:
            return req_response(constants.ERROR, False, 'ARV-RLPOS-3', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)

class RequestsUpdate(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []
    def post(self, request):
        try:
            if request.data == None:
                return req_response(constants.EMPTY_REQ_BODY, False, 'ARV-RUPOS-1', status.HTTP_400_BAD_REQUEST)

            body_data = request.data
            if isinstance(body_data, str):
                body_data = json.loads(body_data)


            print(body_data)
            validation = validator.RequestsUpdateValidator(data=body_data)

            if not validation.is_valid():
                return req_response(constants.INVALID_BODY, False, 'ARV-RUPOS-2', status.HTTP_400_BAD_REQUEST, validation.errors)
            
            new_request = models.Requests.objects.get(id=body_data['req_id'])
            new_request.status = body_data['status']
            new_request.save()
            
            if new_request.type == 'Farmer to FPO Request' and body_data['status'] == 1:
                print("status ",body_data['status'] )

                new_user = user.objects.get(id=new_request.user.id)
                new_user.organization = new_request.organization
                new_user.user_role = user_roles.objects.get(id = settings.IDS_FARMER_USER_ROLE)
                new_user.save()

            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)
        except Exception as e:
            return req_response(constants.ERROR, False, 'ARV-RUPOS-3', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)
