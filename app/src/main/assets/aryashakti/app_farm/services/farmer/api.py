from rest_framework.views import APIView
from app_farm import models
from app_farm.utils import constants,helper,response as res
from app_farm import serializers
from rest_framework.response import Response
from rest_framework import status
from django.db.models import F,Q
import math
from app_farm.authentication import CustomTokenAuthentication
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from app_farm.utils.response import req_response
import json
from . import validator
from . import serializer as farmer_serializer
from django.db import connection
from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db import IntegrityError
import csv
from django.apps import apps
from core.views import BaseView, BaseViewWithoutAuthentication
from django.conf import settings


class farm_stress(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            org_id  = request.GET.get("org_id")
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret_key")
            is_list = request.GET.get("is_list")

            if org_id == None or not org_id.isnumeric() or int(org_id) < 1:
                result = res.ErrRes()
                result['message'] = constants.INVALID_ORG_ID
                result['error_code'] = "AFSFA-FSGET-01"
                return Response(result, status=result['status_code'])

            fields = ['id','farmer_contact','my_plot_id','graph_image_url','season_id','name','name_telugu','user_id','farm_img','is_location','total_area','area_unit','area_unit_telegu','biotic_stress','nutrient_stress','moisture','featured','healthy','stressed','crop_name','crop_name_telegu','country_code','crop_id']

            qs = models.tb_application_access.objects.filter(key=key)
            serializer = serializers.key_serializer(qs, many=True)

            if len(serializer.data) != 0:
                result = res.SuccPageRes()
                if is_list:
                    result['records_per_page'] = constants.DEFAULT_PAGE_RECORDS
                else:
                    result['records_per_page'] = constants.DEFAULT_HOME_PAGE_RECORDS
                
                start, end, current_page = helper.get_pagination_start_end(page_number, result['records_per_page'])

                data = models.farm.objects.filter(org_id=org_id,stressed=True).annotate(crop_name=F('crop_id__crop_name'),crop_name_telegu=F('crop_id__crop_name_telegu'),country_code=F('user__country__mobile_code')).order_by('-biotic_stress').values(*fields)[start:end]
                tot = models.farm.objects.filter(org_id=org_id,stressed=True).values('id').count()

                result['records'] = len(data)
                result['current_page'] = current_page 
                if result['records'] > 0:   
                    if is_list:
                        tot=math.ceil(tot/(result['records_per_page']))
                        result['total_pages'] = tot                          
                    result['message'] = constants.SUCCESS
                    result['data'] = data
                else:
                    result['status_code'] =status.HTTP_202_ACCEPTED
                    result['status'] = False
                    result['message'] = constants.NO_CONTENT
                    result['data'] = []
                return Response(result, status=result['status_code'])
            else:
                result = res.ErrRes()
                result['status_code'] =status.HTTP_400_BAD_REQUEST
                result['message'] = constants.INVALID_KEY
                result['error_code'] = "AFSFA-FSGET-02"
                return Response(result, status=result['status_code'])
        except:
            result = res.ErrRes()
            result['status_code'] =status.HTTP_500_INTERNAL_SERVER_ERROR
            result['message'] = constants.ERROR
            result['error_code'] = "AFSFA-FSGET-03"
            return Response(result, status=result['status_code'])
        
class SmsFarmerList(APIView, PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

    @classmethod
    def get_extra_actions(cls):
        return []
    def post(self, request):
        try:
            if request.data == None:
                return req_response(constants.EMPTY_REQ_BODY, False, 'AFSFA-SFLPOS-1', status.HTTP_400_BAD_REQUEST)

            body_data = request.data
            if type(body_data) == str:
                body_data = json.loads(body_data)
            validation = validator.SmsFarmerListValidator(data=body_data)

            if not validation.is_valid():
                return req_response(constants.INVALID_BODY, False, 'AFSFA-SFLPOS-2', status.HTTP_400_BAD_REQUEST, validation.errors)

            query_filter = Q()
            filter_kwargs = {}
            if body_data.get('search_by_name') is not None:
                query_filter &= Q(name__icontains=body_data['search_by_name']) | Q(farmer_contact__icontains=body_data['search_by_name'])
              
            filter_kwargs['org_id'] = body_data['org_id']

            if body_data.get('stressed') is not None :
                if body_data['stressed'] == 1:
                    filter_kwargs['stressed'] = True

                elif body_data['stressed'] == 0:
                    filter_kwargs['stressed'] = False

            if body_data.get('featured') is not None:
                if body_data['featured'] == 1:
                    filter_kwargs['featured'] = True

                elif body_data['featured'] == 0:
                    filter_kwargs['featured'] = False

            if body_data.get('healthy') is not None:
                if body_data['healthy'] == 1:
                    filter_kwargs['healthy'] = True

                elif body_data['healthy'] == 0:
                    filter_kwargs['healthy'] = False

            if body_data.get('state') is not None:
                filter_kwargs['farm_state'] = body_data['state']

            if body_data.get('district') is not None:
                filter_kwargs['farm_district'] = body_data['district']

            if body_data.get('taluka') is not None:
                filter_kwargs['farm_taluka'] = body_data['taluka']

            if body_data.get('village') is not None:
                filter_kwargs['farm_village'] = body_data['village']

            if body_data.get('crop_id') is not None:
                c1 = body_data['crop_id'].split(";")
                filter_kwargs['crop_id__in'] = [i for i in c1 if i]

            if body_data.get('stress_type') :
                if body_data.get('stress_type')=="biotic":
                    filter_kwargs['biotic_stress__gt'] = constants.STRESS_THRESHOLD
                    
                elif body_data.get('stress_type')=="abiotic":
                    filter_kwargs['abiotic_stress__gt'] = constants.STRESS_THRESHOLD
                    
                elif body_data.get('stress_type')=="nutrient":
                    filter_kwargs['nutrient_stress__gt'] = constants.STRESS_THRESHOLD
                    

            ordering = ['featured']

            if body_data.get('sort_by') is not None :
                if body_data['sort_by'] == 0:
                    ordering.append('name')

                if body_data['sort_by'] == 1:
                    ordering.append('-name')

                if body_data['sort_by'] == 2:
                    ordering.append('total_area')

                if body_data['sort_by'] == 3:
                    ordering.append('-total_area')

            if body_data.get('stressed') is not None :
                if body_data['stressed'] == 1:
                    ordering.append('-biotic_stress')
                elif body_data['stressed'] == 0:
                    ordering.append('biotic_stress')

            qs = models.farm.objects.filter(query_filter, **filter_kwargs).order_by(*ordering).distinct()

            total_count = qs.count()
            if total_count == 0:
                return req_response(constants.NO_CONTENT, True, '', status.HTTP_204_NO_CONTENT, [])

            self.page = None  
            page_size = self.get_page_size(request) or self.page_size
            paginator = self.django_paginator_class(qs, page_size)
            page_number = request.query_params.get(self.page_query_param, 1)
            try:
                page_obj = paginator.page(page_number)
            except Exception:
                page_obj = paginator.page(1)

            serializer = farmer_serializer.SmsFarmerListSerializer(page_obj.object_list, many=True)
            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, {
                'count': total_count,
                'total_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'next': page_obj.next_page_number() if page_obj.has_next() else None,
                'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
                'results': serializer.data,
            })
        except Exception as e:
            return req_response(constants.ERROR, False, 'AFSFA-SFLPOS-3', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)
        
class UpdateFarmer(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []
    def post(self, request):
        try:
            if request.data.get('data') == None:
                return req_response(constants.EMPTY_REQ_BODY, False, 'AFSFA-UFPOS-1', status.HTTP_400_BAD_REQUEST)

            body_data = request.data['data']
            if type(body_data) == str:
                body_data = json.loads(body_data)

            validation = validator.UpdateFarmerValidator(data=body_data)

            if not validation.is_valid():
                return req_response(constants.INVALID_BODY, False, 'AFSFA-UFPOS-2', status.HTTP_400_BAD_REQUEST, validation.errors)
            
            image_url = None
            
            if request.data.get('image') != None and  request.data.get('image')!="" :
                image_url = helper.image_upload(request.data['image'])
            
            user= models.user.objects.filter(id = request.user.id)
            user.update(
                full_name = body_data['name'],
                address_pincode = body_data['pincode'],
                address_country = body_data['country'],
                address_state = body_data['state'],
                address_district = body_data['district'],
                address_taluka = body_data['taluka'],
                address_village = body_data['village'],
                latitude = body_data['lat'],
                longitude = body_data['long'],
                designation = body_data['designation'],
                user_profile_img = image_url,
                
            )

            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)
        except Exception as e:
            return req_response(constants.ERROR, False, 'AFSFA-UFPOS-4', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)

class DeleteFarmer(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request):
        # if 'is_nithin' in data.keys() and data['is_nithin'] and data['is_nithin']=="sdfghjksdfghjkestrdyfyugue456546'';''":
        #     models.user.objects.update(is_deleted=False)
        # else:
        models.user.objects.filter(id=request.user.id).update(is_deleted=True)
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)


class CreateFarmerBySponsor(BaseView):
    def create_farmer_by_sponser(self, request, err_code, req_data):
        user = models.user.objects.create(
            full_name = req_data['name'],
            mobile_number = req_data['phone'],
            added_by = request.user,
            country_id = req_data['country_id']
        )
        models.farm.objects.create(
            user = user,
            added_by = request.user,
            updated_by_id = request.user
        )
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, {
            'id': user.id,
            'name': user.full_name,
            'phone': user.mobile_number
        })
    
    def post(self, request):
        return self.common_function(request, "AFSFA-CFBSPOS-", validator.CreateFarmerBySponsorValidator, self.create_farmer_by_sponser)

class GetAddress(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def post(self, request):
        try:
            if request.data == None:
                return req_response(constants.EMPTY_REQ_BODY, False, 'AFSFA-GAPOS-1', status.HTTP_400_BAD_REQUEST)

            body_data = request.data
            if type(body_data) == str:
                body_data = json.loads(body_data)

            if body_data.get('pincode'):
                validation = validator.PincodeValidator(data=body_data)
            else:
                validation = validator.LatLongValidator(data=body_data)

            if not validation.is_valid():
                return req_response(constants.INVALID_BODY, False, 'AFSFA-GAPOS-2', status.HTTP_400_BAD_REQUEST, validation.errors)
            
            if not helper.verify_secret_key(body_data['secret_key']):
                return req_response(constants.INVALID_KEY, False, 'AFSAA-CFPOS-03', status.HTTP_400_BAD_REQUEST)
            
            if body_data['country_id'] != settings.IDS_COUNTRY_INDIA:
                return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, helper.kenya_address)

            if body_data.get('pincode'):
                address_data = helper.get_address_from_pincode(body_data['pincode'])
                location = helper.get_lat_long_from_pin(body_data['pincode'])

                address_data['lat'] = location['lat']
                address_data['long'] = location['lng']
            else:
                address_data = helper.get_address_data(body_data['lat'], body_data['long'])

            if address_data['flag']:
                return req_response(constants.INVALID_BODY, False, 'AFSFA-GAPOS-4', status.HTTP_400_BAD_REQUEST)

            del address_data['flag']
            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, address_data)
        except Exception as e:
            return req_response(constants.ERROR, False, 'AFSFA-GAPOS-5', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)
        
class GetRoles(BaseViewWithoutAuthentication):
    def get_roles(self, request, err_code, req_data):
        if not helper.verify_secret_key(req_data['secret_key']):
            return req_response(constants.INVALID_KEY, False, err_code+'3', status.HTTP_400_BAD_REQUEST)
        
        roles = models.user_roles.objects.filter(show_in_list=True, countries=req_data['country_id'])
        data = farmer_serializer.GetRolesSerializer(roles, many=True)
        if len(data.data) == 0:
            return req_response(constants.NO_CONTENT, True, '', status.HTTP_204_NO_CONTENT)
        
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data.data)
        
    def get(self, request):
        return self.common_function(request, 'AFSAA-GRGET-', validator.GetRolesValidator, self.get_roles)


def update_crops():
    try:
        orgs = models.organizations.objects.exclude(crop_interest__isnull=True).exclude(crop_interest__exact=[])
        for org in orgs:
            try:
                org.crops_interest.add(*org.crop_interest)
            except Exception as e:
                print('org-'+str(org.id) + ' --> ' + str(e))

        users = models.user.objects.exclude(crop_interest__isnull=True).exclude(crop_interest__exact=[])
        for usr in users:
            try:
                usr.crops_interest.add(*usr.crop_interest)
            except Exception as e:
                print('usr-'+str(usr.id) + ' --> ' + str(e))
        
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return req_response(constants.ERROR, False, 'AFSFA-GRGET-2', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)
    
# update_crops()


class GetSoilReport(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self, request):
        try:
            try:
                report = models.SoilReport.objects.get(farmer= request.user.id)
            except models.SoilReport.DoesNotExist:
                return  req_response(constants.NO_CONTENT, True, '', status.HTTP_204_NO_CONTENT, None)
            report = farmer_serializer.GetSoilReportSerializer(report, many=False).data

            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, report)
        except Exception as e:
            return req_response(constants.ERROR, False, 'AFSFA-GSRGET-1', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)
        
@api_view(['GET'])
@authentication_classes([CustomTokenAuthentication])
@permission_classes([IsAuthenticated])
def testroute(request,**args):
    user=None
    try:
        print("reached")
        # user=models.user.objects.filter(id=1).get()
        # print(connection.queries)
        # print(user)
        # crop=models.crop_master.objects.filter(id=1).get()
        # org=models.organizations.objects.filter(id=1).get()
        # for i in range(1000):
        #     models.farm.objects.create(
        #         name="testing user",
        #         user=user,
        #         crop_id=crop,
        #         org_id=org,
        #         added_by=user,
        #         stage = 'Vegetative',
        #         stage_telugu = 'वनस्पतिक',
        #         farm_cget_rolesountry ="India",
        #         farm_img="dsldlkafalflk",
        #         latitude=14.9281,
        #         longitude=77.6746,
        #     )
    except Exception as e:
        print(connection.queries)
        print(user)
        print(e)
    return Response({"success":"hii"}, status=200)



class social_list(APIView,PageNumberPagination):
    # number of items per page by default
    page_size = 50
    # max number of items per page
    max_page_size = 50
    model=models.social_post

    def get(self, request):
        try:
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                social_list= models.social_post.objects.filter(approved=True).distinct().order_by('-timestamp')
                activity_list= self.paginate_queryset(queryset=social_list,request=request)
                serializer = serializers.sociallistSerializer(social_list, many=True)
                if len(serializer.data) > 0  :
                    response= self.get_paginated_response(serializer.data)
                    response.data['status']= status.HTTP_200_OK
                    response.data['message']='success'
                else:
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response.data, status=response.data['status'])

            else :
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
                return Response(response, status=response['status'])

        except :
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])


class activity_list(APIView,PageNumberPagination):
    # number of items per page by default
    page_size = 50
    # max number of items per page
    max_page_size = 50
    model=models.social_post

    def get(self, request):
        try:
            key = request.GET.get("secret-key")
            qs1 = models.tb_application_access.objects.filter(key=key)
            user_id=request.GET.get('user_id')
            serializer1 = serializers.key_serializer(qs1, many=True)
            if len(serializer1.data) != 0 :
                activity_list= models.activity.objects.filter(user_id=user_id).distinct()
                activity_list= self.paginate_queryset(queryset=activity_list,request=request)
                serializer = serializers.activitylistSerializer(activity_list, many=True)
                if len(serializer.data) > 0  :
                    response= self.get_paginated_response(serializer.data)
                    response.data['status']= status.HTTP_200_OK
                    response.data['message']='success'
                else:
                    response = {'status': status.HTTP_204_NO_CONTENT,'message':'No content','data':serializer.data }
                return Response(response.data, status=response.data['status'])

            else :
                response = {'status': status.HTTP_400_BAD_REQUEST ,'message':'Incorrect key'}
                return Response(response, status=response['status'])

        except :
            response = {'status': status.HTTP_400_BAD_REQUEST,'message':'Bad Request'}
            return Response(response, status=response['status'])



class GetAllFarmersList(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 
    # number of items per page by default
    page_size = 50
    # max number of items per page
    max_page_size = 100
    model=models.user 

    def get_queryset(self):
        mobile_number = self.request.GET.get('mobile_number')
        added_by = self.request.GET.get('added_by')
        queryset = models.user.objects.get_user_by_role("Farmer")

        if added_by:
            queryset= queryset.filter(added_by_id=added_by)
        if mobile_number:
            queryset = queryset.filter(mobile_number__contains=mobile_number)
        return queryset

    def get(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset,request)
        if page is not None:
            serializer = serializers.FarmerSerializer(page, many=True)
            return res.req_response("Data found",True,"",status.HTTP_200_OK,self.get_paginated_response(serializer.data).data)

        # If pagination is not applied, return the full response
        serializer = serializers.FarmerSerializer(queryset, many=True)
        return res.req_response("Data found",True,"",status.HTTP_200_OK,serializer.data)

class UploadUserCSV(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 

    def post(self,request):
        try:
            if not request.FILES['csv_upload']:
                return res.req_response("Please enter valid data.",False,"AF-FAUUC-POST-01",status.HTTP_400_BAD_REQUEST)
            
            response=helper.upload_csv(request.FILES["csv_upload"],models.user,["full_name","mobile_number","latitude","longitude","gender"],{"added_by_id":request.user.id},["mobile_number"])     

            if response['success']:
                list_farm=[]
                for i in response["data"]:
                    list_farm.append({
                        "updated_by_id_id":request.user.id,
                        "added_by_id":request.user.id,
                        "user_id":i.id
                    })

                models.farm.objects.bulk_create([models.farm(**item) for item in list_farm])
            if response["data"]:
                response["data"]=serializers.signuperializer(response['data'],many=True).data
            return res.req_response(response["message"],response["success"],"",status.HTTP_200_OK,response["data"])
        
        except IntegrityError as e:
            print(e)
            return res.req_response("User already exist",False,"",status.HTTP_400_BAD_REQUEST)




class DownloadUserUploadCSV(APIView):
    def get(self,request):
        # Create CSV data in memory
        csv_data = ["full_name","mobile_number","latitude","longitude","gender"]

        # Create the HttpResponse object with CSV content type
        response= helper.downloadCsvSampleCSV(csv_data)

        return response
    
from datetime import datetime

class UpdateSowingDateCrop(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        if request.data.get('data'):
            if isinstance(request.data.get('data'), str):
                data = json.loads(request.data.get('data'))
            else:
                data = request.data.get('data')
        else:
            data = {}
            for key in request.data.keys():
                if key != 'image':  
                    value = request.data.get(key)
                    if isinstance(value, str):
                        value = value.strip('"')
                    data[key] = value
        
        farm_ids = request.data.getlist("farm_ids") or data.get("farm_ids", [])

        if isinstance(farm_ids, str):
            farm_ids = [farm_ids]

        if not isinstance(farm_ids, list):
            farm_ids = [farm_ids]

        try:
            farm_ids = [int(x) for x in farm_ids]
        except Exception:
            return res.req_response("Invalid farm_ids", False, "", status.HTTP_400_BAD_REQUEST)

        if not farm_ids:
            return res.req_response("farm_ids are required", False, "", status.HTTP_400_BAD_REQUEST)

        farm_data = models.farm.objects.filter(id__in=farm_ids)
        if farm_data.count() != len(set(farm_ids)):
            return res.req_response(
                "Farm not found", False, "", status.HTTP_400_BAD_REQUEST
            )

        if not any(key in data for key in ['sowing_date', 'crop_id']):
            return res.req_response(
                "Sowing date or crop is required",
                False,
                "",
                status.HTTP_400_BAD_REQUEST
            )

        if 'sowing_date' in data and data['sowing_date']:
            try:
                datetime.strptime(str(data['sowing_date']), '%Y-%m-%d')
            except ValueError:
                return res.req_response(
                    "Invalid sowing_date format. Expected YYYY-MM-DD",
                    False,
                    "",
                    status.HTTP_400_BAD_REQUEST
                )

        if 'crop_id' in data and data['crop_id']:
            if not models.crop_master.objects.filter(id=data['crop_id']).exists():
                return res.req_response(
                    "Crop not found",
                    False,
                    "",
                    status.HTTP_400_BAD_REQUEST
                )

        if 'variety_id' in data and data['variety_id']:
            if not models.crop_variety_master.objects.filter(id=data['variety_id']).exists():
                return res.req_response(
                    "Crop Variety not found",
                    False,
                    "",
                    status.HTTP_400_BAD_REQUEST
                )

        if 'session_id' in data and data['session_id']:
            try:
                Session = apps.get_model('pop_manage', 'Session')
                if not Session.objects.filter(id=data['session_id']).exists():
                    return res.req_response(
                        "Invalid session_id",
                        False,
                        "",
                        status.HTTP_400_BAD_REQUEST
                    )
            except Exception:
                pass
        message = ""
        if 'sowing_date' in data.keys() and data['sowing_date']:
            sowing_date = datetime.strptime(data['sowing_date'], '%Y-%m-%d')
            for farm_obj in farm_data:
                farm_obj.sowing_date = sowing_date
                # recompute session from CropSession (based on crop and month)
                try:
                    if farm_obj.crop_id:
                        CropSession = apps.get_model('pop_manage', 'CropSession')
                        month = sowing_date.month
                        cs = CropSession.objects.filter(
                            crop=farm_obj.crop_id,
                            from_month__lte=month,
                            to_month__gte=month
                        ).order_by('id').first()
                        if cs:
                            farm_obj.session = cs.session
                except Exception:
                    pass
                farm_obj._changed_by = request.user
                farm_obj.save(update_fields=['sowing_date', 'session'])
            message += "Sowing date "

        if 'crop_id' in data.keys() and data['crop_id']:
            for farm_obj in farm_data:
                farm_obj.crop_id_id = data['crop_id']
                farm_obj._changed_by = request.user
                farm_obj.save(update_fields=['crop_id'])
            message += "Crop "

        if 'variety_id' in data.keys() and data['variety_id']:
            for farm_obj in farm_data:
                farm_obj.crop_variety_id_id = data['variety_id']
                farm_obj._changed_by = request.user
                farm_obj.save(update_fields=['crop_variety_id'])
            message += "Crop Variety"

        if 'name' in data and data['name']:
            for farm_obj in farm_data:
                farm_obj.name = data['name']
                farm_obj._changed_by = request.user
                farm_obj.save(update_fields=['name'])
            message += "name "

        if 'total_area' in data and data['total_area']:
            try:
                area_val = float(data['total_area'])
                for farm_obj in farm_data:
                    farm_obj.total_area = area_val
                    farm_obj._changed_by = request.user
                    farm_obj.save(update_fields=['total_area'])
                message += "total area "
            except ValueError:
                return res.req_response(
                    "Invalid total area",
                    False,
                    "",
                    status.HTTP_400_BAD_REQUEST
                )

        if 'area_unit' in data and data['area_unit']:
            for farm_obj in farm_data:
                farm_obj.area_unit = data['area_unit']
                farm_obj._changed_by = request.user
                farm_obj.save(update_fields=['area_unit'])
            message += "area unit "

        if 'gender' in data and data['gender']:
            valid_genders = [g[0] for g in constants.GENDERS]
            if data['gender'] not in valid_genders:
                return res.req_response(
                    f"Invalid gender. Valid options are: {', '.join(valid_genders)}",
                    False,
                    "",
                    status.HTTP_400_BAD_REQUEST
                )
            user_ids = {farm.user_id for farm in farm_data if farm.user_id}
            if user_ids:
                models.user.objects.filter(id__in=user_ids).update(
                    gender=data['gender']
                )
            message += "gender "
        
        if 'session_id' in data and data['session_id']:
            try:
                Session = apps.get_model('pop_manage', 'Session')
                session_obj = Session.objects.get(id=data['session_id'])
            except Session.DoesNotExist:
                return res.req_response(
                    "Invalid session_id",
                    False,
                    "",
                    status.HTTP_400_BAD_REQUEST
                )
            for farm_obj in farm_data:
                farm_obj.session = session_obj
                farm_obj._changed_by = request.user
                farm_obj.save(update_fields=['session'])
            message += "Session "

        variety_id = data.get('variety_id')
        if data.get('variety_name') and not variety_id:
            variety_name = data.get('variety_name')
            crop_variety = models.crop_variety_master.objects.create(
                crop_id_id=data['crop_id'],
                crop_variety=variety_name
            )
            for farm_obj in farm_data:
                farm_obj.crop_variety_id_id = crop_variety.id
                farm_obj._changed_by = request.user
                farm_obj.save(update_fields=['crop_variety_id'])
            variety_id = crop_variety.id
        image_path = None
        signed_url = None

        if request.FILES.get('image'):
            try:
                image_file = request.FILES['image']
                image_path = helper.private_image_upload(
                    image_file,
                    f"profile_pictures/user_{request.user.id}",
                    overwrite=True
                )

                if not image_path:
                    return res.req_response(
                        "Image upload failed",
                        False,
                        "AFSFA-USDCPOST-IMG-01",
                        status.HTTP_400_BAD_REQUEST,
                    )

                signed_urls = helper.generate_multiple_signed_urls(
                    [image_path],
                    expiration_minutes=1440,
                )
                signed_url = signed_urls.get(image_path)
                if not signed_url:
                    return res.req_response(
                        "Failed to generate image URL",
                        False,
                        "AFSFA-USDCPOST-IMG-02",
                        status.HTTP_400_BAD_REQUEST,
                    )

                user_ids = {farm.user_id for farm in farm_data if farm.user_id}
                if user_ids:
                    models.user.objects.filter(id__in=user_ids).update(
                        user_profile_img=image_path
                    )
                    message += "Profile picture "

            except Exception as e:
                return res.req_response(
                    "Image processing failed",
                    False,
                    "AFSFA-USDCPOST-IMG-03",
                    status.HTTP_400_BAD_REQUEST,
                )
        return res.req_response(
            f"{message.strip()} updated successfully",
            True,
            "",
            status.HTTP_200_OK,
            {
                "signed_url": signed_url
            }
        )
class GetSessions(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []

    def get(self, request):
        try:
            Session = apps.get_model('pop_manage', 'Session')
            sessions = list(
                Session.objects.filter(is_active=True)
                .order_by('name')
                .values('id', 'name')
            )
            if not sessions:
                return req_response(constants.NO_CONTENT, True, '', status.HTTP_204_NO_CONTENT, [])
            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, sessions)
        except Exception as e:
            return req_response(constants.ERROR, False, 'AFSFA-GSESSGET-1', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)