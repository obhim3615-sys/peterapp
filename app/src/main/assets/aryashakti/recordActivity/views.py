from django.shortcuts import render
from rest_framework.views import APIView
from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import *
from .serializers import *
from app_farm.utils import helper, constants,response as res
from rest_framework.response import Response
import json
from django.db.models import Subquery, OuterRef
from app_farm.serializers import UserWithTaskCountSerializer
from django.db.models import Count,F,Q ,Max
from rest_framework import status
from django.contrib.gis.geos import Point
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from .validators import * 
from django.utils.timezone import make_aware
from datetime import datetime
from libraries.prakshepdb import insert_into_remote_db
from libraries.openai import OpenAIAPIIntegration,OpenAIResponsesClient
from cms.serializer import GetConfigSerializer
from cms.models import Setting
from django.db.models import Q,F,Value,CharField
from django.db.models.functions import Concat,TruncDate
from io import StringIO
import csv
from libraries.doms import DomsSignedURL
from libraries.noms import NoMS
from app_farm.serializers import FarmSerializerVikshep
from datetime import datetime, date
from farm_category.models import FarmsCategory
from libraries.decorators import HasValidTokenPermission
import time
from core.models import CustomForm
import uuid

# Create your views here.


class GetAllActivity(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request):
        organization_id = getattr(request.user, 'organization_id', None)
        crop_id = request.GET.get('crop_id')
        # Query to fetch data based on organization or if there's no organization
        data = ActivityRecord.objects.filter(
            Q(organization_id=organization_id) | Q(organization_id__isnull=True)
        ).order_by('order_value')[:50]
        organization_id= request.user.organization_id

        response=ActivitySerializer(data,many=True,context={'organization':organization_id,'crop_id':crop_id})
        result=res.SuccRes()
        result['data']=response.data
        result['user_id']=request.user.id
        result['static_field']=[
            #{"name":"day_after_sowing","type":"int", "is_required":True },
            {"name":"date_of_activity","type":"date","is_required":True},
            {"name":"image","type":"string","is_required":False}
        ]
        return Response(result,status=result['status_code'])


class GetAllActivityPP(APIView):
    permission_classes = [AllowAny]
    def get(self,request):
        # organization_id = request.user.organization.id
        crop_id = request.GET.get('crop_id')
        # Query to fetch data based on organization or if there's no organization
        data = ActivityRecord.objects.filter(
             Q(organization_id__isnull=True)
        ).order_by('order_value')[:50]
        

        response=ActivitySerializer(data,many=True,context={'crop_id':crop_id})
        result=res.SuccRes()
        result['data']=response.data
        # result['user_id']=request.user.id
        # result['static_field']=[
        #     #{"name":"day_after_sowing","type":"int", "is_required":True },
        #     {"name":"date_of_activity","type":"date","is_required":True},
        #     {"name":"image","type":"string","is_required":False}
        # ]
        return Response(result,status=result['status_code'])



class GetActivityFields(APIView):
    """
    API: GetActivityFields
    Error Codes: 
      RAV-GAF-00 → Success
      RAV-GAF-01 → Farm not found
      RAV-GAF-02 → Activity fields not found
      RAV-GAF-03 → Unexpected error
    """

    def get(self, request, farm_id, activity_record_id):
        try:
            # --- Fetch farm ---
            try:
                farm_data = farm.objects.get(id=farm_id)
            except farm.DoesNotExist:
                return res.req_response(
                    "Farm not found",
                    False,
                    "RAV-GAF-01",
                    status.HTTP_404_NOT_FOUND,
                    []
                )

            crop_id = farm_data.crop_id.id
            variety_id = farm_data.crop_variety_id

            # --- Fetch activity fields ---
            activity_fields = ActivityFields.objects.filter(
                activity_id=activity_record_id
            )

            if crop_id:
                activity_fields=activity_fields.filter(
                    Q(crop_id=crop_id) | Q(crop__isnull=True),
                    status=True
                )
            if variety_id:
                activity_fields.filter( Q(variety_id=variety_id) | Q(variety__isnull=True))
            if not activity_fields.exists():
                return res.req_response(
                    "Activity fields not found",
                    False,
                    "RAV-GAF-02",
                    status.HTTP_404_NOT_FOUND,
                    []
                )

            serializer = ActivityFieldsSerializer(activity_fields, many=True)

            return res.req_response(
                "Data found",
                True,
                "RAV-GAF-00",
                status.HTTP_200_OK,
                serializer.data
            )

        except Exception as e:
            return res.req_response(
                "Something went wrong",
                False,
                "RAV-GAF-03",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                []
            )


class GetFarmerActivity(APIView, PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    page_size = 25
    max_page_size = 100

    def get(self, request, farmerid):
        try:
            date = request.GET.get('date')
            page = request.GET.get('page')

            queryset = DASActivityRecord.objects.filter(
                farm_id=farmerid
            ).order_by('-id')

            if date:
                queryset = queryset.filter(date_of_activity=date)
            paginated_qs = self.paginate_queryset(queryset, request)

            if page and not paginated_qs and queryset.exists():
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": "Page not found"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = DASActivityRecordSerializer(
                paginated_qs, many=True
            )

            response = self.get_paginated_response(serializer.data)
            response.data['status_code'] = status.HTTP_200_OK
            response.data['status'] = True
            response.data['message'] = "Data found"
            return Response(response.data, status=status.HTTP_200_OK)

        except Exception as e:
            result = res.ErrRes()
            result['message'] = "Bad Request"
            return Response(result, status=result['status_code'])


class PPGetFarmerActivity(APIView):
    permission_classes = [AllowAny]
    def get(self,request,farm_id):
        date= request.GET.get('date')
        data=DASActivityRecord.objects.filter(farm_id=farm_id)       
        if date:
            data=data.filter(date_of_activity=date)
        data=data.order_by('-id').all()[:10]
        response=DASActivityRecordSerializer(data,many=True)
        result=res.SuccRes()
        result['data']=response.data
        return Response(result,status=result['status_code'])
   
    
from pop_manage.views import add_soil_test_plot
class CreateActivityDas(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self,request):

        data= request.POST
        
        validator=DASActivitiyValidator(data=data)
        if not validator.is_valid():
            result = res.ErrRes()
            result['message'] = constants.INVALID_BODY
            result['error_code'] = "RAV-CADP-03"
            result['data'] = validator.errors
            return Response(result, status=result['status_code'])


        # try:
        #     farmer= user.objects.filter(id=data['user_id']).get()
        # except user.DoesNotExist:
        #     response= res.ErrRes()
        #     response['status_code']=status.HTTP_404_NOT_FOUND
        #     response['message']="Farmer not found"
        #     response['error_code']="RAV-CADP-01"
        #     return Response(response,status=response['status_code'])

        farmer= request.user
        
        try:
            if isinstance(data['activity_id'], str):
                if data['activity_id'].isdigit():
                    activity_id= int(data['activity_id'])
            activity= ActivityRecord.objects.filter(id=activity_id).get()
        except user.DoesNotExist:
            response= res.ErrRes()
            response['status_code']=status.HTTP_404_NOT_FOUND
            response['message']="Activity not found"
            response['error_code']="RAV-CADP-02"
            return Response(response,status=response['status_code'])
        farm_data=None
        day_of_sowing_value=0
        if 'farm_id' in data.keys():
            farm_id=data['farm_id']
            try:
                farm_data= farm.objects.filter(id=data['farm_id']).get()
                if farm_data.sowing_date:
                    # Calculate the difference in days between sowing date and today
                    today = datetime.now().date()
                    day_of_sowing_value = (today - farm_data.sowing_date.date()).days
                    
            except farm.DoesNotExist:
                return res.req_response("Farm not found",False,"RAV-CADP-04",status.HTTP_404_NOT_FOUND)
        
        images = request.FILES.getlist('image_url')  # Assuming 'image_url' is the name of the file input field

        image_urls = []

        for image in images:
            if image is not None:
                image_url = helper.image_upload(image)
                image_urls.append(image_url)
            else:
                image_urls.append("")

        
        latitude=longitude=0

        if 'latitude' in data.keys():
            latitude=data['latitude']
        if 'longitude' in data.keys():
            longitude=data['longitude']
        point_value=None
        if latitude!=0 and longitude!=0:
            point_value = Point(float(longitude), float(latitude),srid=4326)
        das=DASActivityRecord.objects.create(
            farmer=farmer,
            farm_id=data.get('farm_id'),
            day_of_sowing=day_of_sowing_value,
            date_of_activity=data['date_of_activity'],
            activity=activity,
            activity_data=json.loads(data['data']),
            image_url="",
            latitude=latitude,
            longitude=longitude,
            geometry=point_value
        )
        try:
            id_activity=Setting.objects.getKey('SOIL_TESTING_ACTIVITY_ID')
        except Setting.DoesNotExist:
            id_activity=None
        # print(data['activity_id'],id_activity.value)
        if id_activity and data['activity_id']==id_activity.value:
            # print("hiii")
            check_add= add_soil_test_plot(data.get('farm_id'),request.user)
            # print(check_add[1])
        if das and request.user.organization.company_id=="ABIN001":
            insert_into_remote_db('recordActivity_dasactivityrecord',{
                "activity_data":data['data'],
                "day_of_sowing":day_of_sowing_value,
                "activity_id":activity.id,
                "farmer_id":farmer.id,
                "farm_id":data.get('farm_id'),
                "date_of_activity":data['date_of_activity'],
                "image_url":"",
                "geometry":point_value,
                "latitude":latitude,
                "longitude":longitude,
                "farmer_name":farmer.full_name,
                "activity_name":activity.name,
                "created_at":das.created_at,
                "updated_at":das.updated_at,
            })

        for i in image_urls:      
            if i:
                DASActivityRecordImage.objects.create(
                    image_url=i,
                    activity_record=das
                )

        response=res.SuccRes()
        response['status_code']=status.HTTP_201_CREATED
        response['message']="Activity Added"

        return Response(response,response['status_code'])
            
class EditActivityDas(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, activity_id):

        data = request.data
        files = request.FILES
        validator = UpdateDASActivityValidator(data=data)

        if not validator.is_valid():
            result = res.ErrRes()
            result['message'] = "Invalid data"
            result['error_code'] = "RAV-UADP-01"
            result['data'] = validator.errors
            return Response(result, status=400)

        validated = validator.validated_data
        try:
            das = DASActivityRecord.objects.get(id=activity_id)
        except DASActivityRecord.DoesNotExist:
            return res.req_response("Activity record not found", False, "RAV-UADP-02", 404)

        if "activity_id" in validated:
            try:
                activity = ActivityRecord.objects.get(id=validated["activity_id"])
                das.activity = activity
            except ActivityRecord.DoesNotExist:
                return res.req_response("Activity not found", False, "RAV-UADP-03", 404)

        if "farm_id" in validated:
            try:
                farm_detail = farm.objects.get(id=validated["farm_id"])
                das.farm_id = validated["farm_id"]

                # Recalculate day_of_sowing
                if farm_detail.sowing_date:
                    today = datetime.now().date()
                    das.day_of_sowing = (today - farm_detail.sowing_date.date()).days

            except farm.DoesNotExist:
                return res.req_response("Farm not found", False, "RAV-UADP-04", 404)

        if "data" in validated:
            das.activity_data = validated["data"]

        if "date_of_activity" in validated:
            das.date_of_activity = validated["date_of_activity"]

        lat = validated.get("latitude")
        lng = validated.get("longitude")

        if lat and lng:
            das.latitude = lat
            das.longitude = lng
            das.geometry = Point(float(lng), float(lat), srid=4326)

        das.save()

        if validated.get("delete_existing_images", False):
            DASActivityRecordImage.objects.filter(activity_record=das).delete()

        image_files = files.getlist("image_url")

        for img in image_files:
            url = helper.image_upload(img)
            DASActivityRecordImage.objects.create(
                image_url=url,
                activity_record=das
            )

        response = res.SuccRes()
        response['status_code'] = 200
        response['message'] = "Activity updated successfully"

        return Response(response, 200)


    def get(self, request, activity_id):

        try:
            das = DASActivityRecord.objects.select_related(
                "activity", "farmer", "farm"
            ).get(id=activity_id)
        except DASActivityRecord.DoesNotExist:
            return res.req_response(
                "Activity record not found",
                False,
                "RAV-GDAP-01",
                404
            )

        activity_value_map = {}
        for item in das.activity_data:
            name = item.get("name")
            value = item.get("value")

            if not name or value in [None, ""]:
                continue

            activity_value_map.setdefault(name, []).append(str(value))
        das_data = {
            "id": das.id,
            "farmer_id": das.farmer_id,
            "farmer_name": das.farmer.full_name if das.farmer else None,
            "farm_id": das.farm_id,
            "day_of_sowing": das.day_of_sowing,
            "date_of_activity": das.date_of_activity,
            "activity_id": das.activity_id,
            "activity_name": das.activity.name if das.activity else None,
            "latitude": das.latitude,
            "longitude": das.longitude,
            "geometry": das.geometry.geojson if das.geometry else None,
            "activity_data": das.activity_data,
            "image_url": das.image_url,
            "created_at": das.created_at,
            "updated_at": das.updated_at
        }

        activity_fields = ActivityFields.objects.filter(
            activity=das.activity,
            status=True
        ).order_by("id")

        response_fields = []

        for field in activity_fields:
            values = activity_value_map.get(field.name, [])
            selected_value = ", ".join(values) if values else None

            response_fields.append({
                "id": field.id,
                "created_at": field.created_at,
                "updated_at": field.updated_at,
                "name": field.name,
                "type": field.type,
                "field_possible_value": field.field_possible_value,
                "is_required": field.is_required,
                "status": field.status,
                "organization": field.organization_id,
                "activity": field.activity_id,
                "crop": field.crop_id,
                "variety": field.variety_id,
                "selected_value": selected_value
            })

        return Response({
            "status_code": 200,
            "status": True,
            "message": "Data found",
            "data": {
                "das_activity": das_data,
                "activity_fields": response_fields
            }
        }, status=200)


class GetAllOtherActivity(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request):
        organization_id = getattr(request.user, 'organization_id', None)
        # Query to fetch data based on organization or if there's no organization
        if organization_id:
            data = OneTimeRecord.objects.filter(
                Q(organization_id=organization_id) | Q(organization_id__isnull=True)
            ).order_by('-id')[:20]
        else:
            data = []
        #data=OneTimeRecord.objects.order_by('-id').all()[:10]
        response=OneTimeRecordSerializer(data,many=True)
        result=res.SuccRes()
        result['data']=response.data
        return Response(result,status=result['status_code'  ])
    

class GetFarmerOTRActivity(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request,farmerid):
        data=OTRFarmer.objects.filter(farmer_id=farmerid).order_by('-id').all()[:20]
        response=OTRFarmerSerializer(data,many=True)
        result=res.SuccRes()
        result['data']=response.data
        return Response(result,status=result['status_code'])
    

class CreateOTRDas(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self,request):
        data= request.data
        try:
            farmer= user.objects.filter(id=data['user_id']).get()
        except user.DoesNotExist:
            response= res.ErrRes()
            response['status_code']=status.HTTP_404_NOT_FOUND
            response['message']="Farmer not found"
            response['error_code']="RAV-CODP-01"
            return Response(response,status=response['status_code'])
        
        try:
            record_type= OneTimeRecord.objects.filter(id=data['record_type']).get()
        except user.DoesNotExist:
            response= res.ErrRes()
            response['status_code']=status.HTTP_404_NOT_FOUND
            response['message']="Activity not found"
            response['error_code']="RAV-CODP-02"
            return Response(response,status=response['status_code'])
        
        
        validator=OTRecordValidator(data=data)
        if not validator.is_valid():
            result = res.ErrRes()
            result['message'] = constants.INVALID_BODY
            result['error_code'] = "RAV-CODP-03"
            result['data'] = validator.errors
            return Response(result, status=result['status_code'])


        das=OTRFarmer.objects.create(
            farmer=farmer,
            farm_id=data.get('farm_id'),
            record_type=record_type,
            record_data=json.loads(data['data'])
        )

        if das and request.user.organization.company_id=="ABIN001":
            insert_into_remote_db('recordActivity_otrfarmer',{
                "record_data":data['data'],
                "created_at":das.created_at,
                "updated_at":das.updated_at,
                "farmer_id":farmer.id,
                "farmer_name":farmer.full_name,
                'record_type_id':record_type.id,
                'record_type_name':record_type.name,
                "farm_id":data.get('farm_id'),
            })

        response=res.SuccRes()
        response['status_code']=status.HTTP_201_CREATED
        response['message']="Record Added"

        return Response(response,response['status_code'])


class GetActivityCount(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
        user_data=request.user
        farmer_id = request.GET.get("farmer_id")
        farm_ids = request.GET.getlist("farm_id")
        user_type="admin"
        if user_data.user_role.role_name!="Admin":
            user_type="farmer"
        data= DASActivityRecord.objects.filter(farm__org_id_id=request.user.organization_id)
        if user_type=="farmer":
            data=data.filter(farmer_id=user_data.id)
        if farmer_id:
            data = data.filter(farmer_id=farmer_id)
        if farm_ids:
            data = data.filter(farm_id__in=farm_ids)
        data=data.all().values('activity','activity_id').annotate(total=Count('activity'),activity_name=F('activity__name'))
        #print(data[0])
        data= DASActivityRecordCountSerializer(data, many=True)
        if data:
            data=data.data
        
        response={"status_code":200,
                  "data":data}
        return Response(response,response['status_code'])
        
class GetActivityFPO(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]


    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=DASActivityRecord    

    def get_queryset(self,activity_id,user_data):
        user_type="admin"
        request = self.request
        farmer_id = request.GET.get("farmer_id")
        farm_ids = request.GET.getlist("farm_id")
        if user_data.user_role.role_name!="Admin":
            user_type="farmer"
        queryset=DASActivityRecord.objects.filter(farm__org_id_id=self.request.user.organization_id,activity_id=activity_id)
        if user_type=="farmer":
            queryset=queryset.filter(farmer_id=user_data.id)
        if farmer_id:
            queryset = queryset.filter(farmer_id=farmer_id)
        if farm_ids:
            queryset = queryset.filter(farm_id__in=farm_ids)
        return queryset.order_by('-id')
        
    def get(self,request,activity_id):
        user_data= request.user
        queryset = self.get_queryset(activity_id,user_data)   
          
        page =  self.paginate_queryset(queryset,request)

        task=None
        if page:          
            task=DASActivityRecordSerializer(page,many=True).data
            task=self.get_paginated_response(task).data
        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,task)
    


class CreateTaskBD(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=TaskBD    

    def get_queryset(self,query_text,bd_id):
        user = self.request.user
        
        subtask_latest = SubTaskBD.objects.filter(taskbd=OuterRef('pk')).order_by('-date_time_of_activity')
       
        queryset = (
            TaskBD.objects
            .filter(~Q(status="2"))
            .annotate(total_subtasks=Count('task_subtask'))
            .annotate(last_subtask_title=Subquery(subtask_latest.values('title_of_activity')[:1]))
            .order_by('-id')
        )

        if bd_id:
            org_id = getattr(self.request.user, 'organization_id', None)
            queryset=queryset.filter(assigned_to_id=bd_id,assigned_to__organization_id=org_id)
        else:
            queryset=queryset.filter(assigned_to=user)
            
        if query_text:
            # Use Q objects to construct a complex lookup
            query_filter = Q()
            query_filter |= Q(custom_form_data__0__icontains=query_text )
            query_filter |= Q(custom_form_data__1__icontains=query_text)
            query_filter |= Q(custom_form_data__2__icontains=query_text)
            # Add more conditions if needed
            queryset = queryset.filter(query_filter)
            


        # Get start_date and end_date from query parameters
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        status = self.request.query_params.get('status')

        # If both start_date and end_date are provided, filter by the date range
        if start_date and end_date:
            start_datetime = timezone.datetime.combine(timezone.datetime.strptime(start_date, "%Y-%m-%d").date(), timezone.datetime.min.time())
            end_datetime = timezone.datetime.combine(timezone.datetime.strptime(end_date, "%Y-%m-%d").date(), timezone.datetime.max.time())
            queryset = queryset.filter(created_at__range=(start_datetime, end_datetime))

        if status:
            queryset = queryset.filter(status_task=status)

        return queryset


    def get(self,request):
        data=request.GET
        query_text=data.get('query_text') 
        bd_id = request.GET.get('bd_id', None)
        manager_id = request.GET.get('manager_id', None)
        zonal_manager_id = request.GET.get('zonal_manager_id', None)

        queryset = self.get_queryset(query_text,bd_id)   
          
        page =  self.paginate_queryset(queryset,request)

        task=None
        if page:          
            task=TaskBDSerializer(page,many=True).data
            task=self.get_paginated_response(task).data
        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,task)
    

    def post(self,request):

        data= request.data
        
        validator=TaskBDValidator(data=data)
        if not validator.is_valid():
            result = res.ErrRes()
            result['message'] = constants.INVALID_BODY
            result['error_code'] = "RAV-CTPOST-01"
            result['data'] = validator.errors
            return Response(result, status=result['status_code'])
        custom_form_data=data.get('custom_form_data')
        if custom_form_data:
            custom_form_data=json.loads(custom_form_data)

        assigned_to_id= data.get('assigned_to')
        if not assigned_to_id:
            assigned_to_id=request.user.id
        TaskBD.objects.create(task_name=data['task_name'],
                              sub_task_size=data['sub_task_size'],
                              assigned_by=request.user,
                              assigned_to_id=assigned_to_id,
                              #status="0",  
                              status_task_id=data.get('status'),                            
                              custom_form_data=custom_form_data,
                              custom_form_id=data.get('custom_form_id'),)        

        return res.req_response("Task created",True,"",status.HTTP_200_OK)

class UpdateTaskBD(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request):
        data= request.data
        validator=UpdateTaskBDValidator(data=data)

        if not validator.is_valid():
            errors = validator.errors
            return res.req_response(constants.INVALID_BODY,False,"RAV-UPTBD-POST-01",status.HTTP_400_BAD_REQUEST)
        try:
            task=TaskBD.objects.filter(id=data['task_id'])
        except TaskBD.DoesNotExist:
            return res.req_response("Task not found",False,"RAV-UPTBD-POST-02",status.HTTP_404_NOT_FOUND)

        check= task.update(status_task_id=data['status'])
        if check:
            return res.req_response("Task updated",True,"",status.HTTP_200_OK)
        
        return res.req_response("Task update failed",False,"RAV-UPTBD-POST-03",status.HTTP_400_BAD_REQUEST)




class CreateSubTaskBD(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

     # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=SubTaskBD    

    def get_queryset(self,taskid):   
        try:  
            task= TaskBD.objects.filter(id=taskid).get()
        except TaskBD.DoesNotExist:
            return []     
        if task:
            queryset = SubTaskBD.objects.filter(~Q(status="2"),taskbd=task)
            # Get start_date and end_date from query parameters
            start_date = self.request.query_params.get('start_date')
            end_date = self.request.query_params.get('end_date')

            # If both start_date and end_date are provided, filter by the date range
            if start_date and end_date:
                start_datetime = timezone.datetime.combine(timezone.datetime.strptime(start_date, "%Y-%m-%d").date(), timezone.datetime.min.time())
                end_datetime = timezone.datetime.combine(timezone.datetime.strptime(end_date, "%Y-%m-%d").date(), timezone.datetime.max.time())
                queryset = queryset.filter(date_time_of_activity__range=(start_datetime, end_datetime))

            

            return queryset.order_by('-id')

        return SubTaskBD.objects.none()

    def get(self,request,taskid):
        queryset = self.get_queryset(taskid)      
        page =  self.paginate_queryset(queryset,request)
        
        task=None
        if page:          
            task=SubTaskBDSerializer(page,many=True).data
            task=self.get_paginated_response(task).data
        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,task)
    

    def post(self,request):

        data= request.data
        validator=SubTaskBDValidator(data=data)
        
        if not validator.is_valid():
            errors = validator.errors
            return res.req_response(constants.INVALID_BODY,False,"RAV-CSTPOST-01",status.HTTP_400_BAD_REQUEST)
            
        description=""
        if 'description' in data.keys():
            description=data['description']
        
        task=None
        try:
            task=TaskBD.objects.filter(id=data['taskid']).get()
        except TaskBD.DoesNotExist:
            return res.req_response("Task not found",False,"RAV-CSTPOST-02",status.HTTP_400_BAD_REQUEST)

        images = request.FILES.getlist('image_url')  # Assuming 'image_url' is the name of the file input field

        image_urls = []

        for image in images:
            if image is not None:
                image_url = helper.image_upload(image)
                image_urls.append(image_url)
            else:
                image_urls.append("")

        subtask_count=SubTaskBD.objects.filter(taskbd=task).count()
        if subtask_count>=task.sub_task_size:
            task.sub_task_size=subtask_count+1
            task.save()
        
        custom_form_data=data.get('custom_form_data')
        if custom_form_data:
            custom_form_data=json.loads(custom_form_data)
        subtask=SubTaskBD.objects.create(taskbd=task,
                              date_time_of_activity=data['date_time_of_activity'],
                              title_of_activity=data['title_of_activity'],
                              description=description,
                              latitude=data['latitude'],
                              longitude=data['longitude'],
                              created_by=request.user,
                              custom_form_data=custom_form_data,
                              custom_form_id=data.get('custom_form_id'),
                              status="0")  
        
        if subtask:
            if subtask.title_of_activity=="DSR" and custom_form_data:
                for i in custom_form_data:
                     if i['name']=="FOLLOW UP DATE" and i['value']:
                        FollowUpCalendar.objects.create(subtask=subtask,date=i['value'])

        for i in image_urls:      
            if i:
                SubTaskImage.objects.create(
                    image_url=i,
                    subtask=subtask
                )
        return res.req_response("Sub Task created",True,"",status.HTTP_200_OK)

class GetFollowupCalendar(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

     # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=FollowUpCalendar    

    def get_queryset(self,user_id,date):
        followup_calendar= FollowUpCalendar.objects.filter(subtask__created_by__id=user_id).order_by('-id')
        if date:
            date = make_aware(datetime.strptime(date, '%Y-%m-%d'))
            followup_calendar=followup_calendar.filter(date=date)

            
        return followup_calendar

    def get(self,request):
        data= request.GET
        queryset = self.get_queryset(data.get('user_id',request.user.id),data.get('date'))      
        page =  self.paginate_queryset(queryset,request)
        
        task=None
        if page:          
            task=FollowUpCalendarSerializer(page,many=True).data
            task=self.get_paginated_response(task).data
        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,task)

class GetBDListForManager(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=user   

    def get_queryset(self,user_id,search_query, start_date, end_date,curren_user_role,bd_manager_id):
        
        role_name=constants.SLUGS['USER_ROLES']['BD']
        queryset= user.objects.filter(
            user_role__role_name=role_name,
            # organization_id=org_id
        ).annotate(
            task_count=Count('assigned_to_task')
        )

        if curren_user_role==constants.SLUGS['USER_ROLES']['ZONAL_HEAD']:
            queryset = queryset.filter(
            verified_by_id=user_id)
        else:
            queryset = queryset.filter(
            added_by_id=user_id)

        if bd_manager_id:
            queryset = queryset.filter(added_by_id=bd_manager_id)
        if search_query:
            queryset = queryset.filter(
                Q(full_name__istartswith=search_query) |
                Q(mobile_number__istartswith=search_query)
            )
        
        if start_date and end_date:
            start_date = make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
            end_date = make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
            queryset = queryset.filter(assigned_to_task__created_at__date__range=[start_date, end_date])



        return queryset
        

    def get(self,request):
        search_query = request.GET.get('search', None)
        start_date = request.GET.get('start_date', None)
        end_date = request.GET.get('end_date', None)
        bd_manager_id = request.GET.get('bd_manager_id', None)

        curren_user_role=request.user.user_role.role_name


        queryset = self.get_queryset(request.user.id,search_query, start_date, end_date,curren_user_role,bd_manager_id)      
        page =  self.paginate_queryset(queryset,request)

        bd_user=None
        if page:          
            bd_user=UserWithTaskCountSerializer(page,many=True).data
            bd_user=self.get_paginated_response(bd_user).data
        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,bd_user)




class GetBDManagerList(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=user   

    def get_queryset(self,user_id,search_query,curren_user_role):
        
        role_name=constants.SLUGS['USER_ROLES']['BD_MANAGER']
        queryset= user.objects.filter(
            user_role__role_name=role_name,
            # organization_id=org_id
        ).annotate(
            task_count=Count('assigned_to_task')
        )

        if curren_user_role==constants.SLUGS['USER_ROLES']['ZONAL_HEAD']:
            queryset = queryset.filter(
            verified_by_id=user_id)
        else:
            queryset = queryset.filter(
            added_by_id=user_id)

        if search_query:
            queryset = queryset.filter(
                Q(full_name__istartswith=search_query) |
                Q(mobile_number__istartswith=search_query)
            )
        
        # if start_date and end_date:
        #     start_date = make_aware(datetime.strptime(start_date, '%Y-%m-%d'))
        #     end_date = make_aware(datetime.strptime(end_date, '%Y-%m-%d'))
        #     queryset = queryset.filter(assigned_to_task__created_at__date__range=[start_date, end_date])


        return queryset
        

    def get(self,request):
        search_query = request.GET.get('search', None)       

        curren_user_role=request.user.user_role.role_name


        queryset = self.get_queryset(request.user.id,search_query,curren_user_role)      
        page =  self.paginate_queryset(queryset,request)

        bd_user=None
        if page:          
            bd_user=UserWithTaskCountSerializer(page,many=True).data
            bd_user=self.get_paginated_response(bd_user).data
        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,bd_user)
    

class GetStatusHandle(APIView):

    def get(self,request):
        data= StatusHandle.objects.all()
        if data:
            data= StatusHandleSerializer(data,many=True)
            if data: 
                data= data.data

        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,data)





class CreateAssistantView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        openai_integration = OpenAIAPIIntegration()
        data = request.data
        key = data.get('key')
        name = request.user.organization.org_name

        if not name or not key:
            return res.req_response("organization and key required",False,"CAOAI-VPOST-01",status.HTTP_400_BAD_REQUEST)

           

        assistant_id = openai_integration.create_assistant(name)
        #save assistant id
        if 'error' in assistant_id.keys():
            return res.req_response(assistant_id['error']['message'],False,"CAOAI-VPOST-01",status.HTTP_400_BAD_REQUEST)

        check= Setting.objects.update_or_create(key=key,defaults={"value":assistant_id['id']})
        
        if check:
            return res.req_response("Assistant created",True,"",status.HTTP_200_OK,{"assistant_id": assistant_id})
        return res.req_response("Something went wrong",False,"CAOAI-VPOST-02",status.HTTP_400_BAD_REQUEST)


class UpdateAssistantView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        openai_integration = OpenAIAPIIntegration()
        data = request.data
        prompt = data.get('prompt')
        assistant_id = data.get('assistant_id')
        
        if not prompt or not assistant_id:
            return res.req_response("prompt and assistant_id required",False,"CAOAI-VPOST-01",status.HTTP_400_BAD_REQUEST)

        assistant_id = openai_integration.update_assistant(assistant_id,prompt)
        #save assistant id
        if 'error' in assistant_id.keys():
            return res.req_response(assistant_id['error']['message'],False,"CAOAI-VPOST-01",status.HTTP_400_BAD_REQUEST)

       
        return res.req_response("Assistant updated",True,"",status.HTTP_200_OK,{"assistant_id": assistant_id})
       

class GetAssistantIDViewForCropIdentification(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):

        assistant = Setting.objects.filter(key='OPEN_AI_CROP_IDENTIFY_ASSISTANT_ID').first()
        if not assistant:
            return res.req_response("No assistant found",False,"GAOAI-VPOST-01",status.HTTP_404_NOT_FOUND)

        assistant=GetConfigSerializer(assistant).data
        return res.req_response("Assistant found",True,"",status.HTTP_200_OK,{"assistant_id": assistant})


class CreateThreadViewForCropIdentification(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        openai_integration = OpenAIAPIIntegration()
        data=request.data
        farm_id = data.get('farm_id')
        assistant_id = data.get('assistant_id')

        if not assistant_id:
            return res.req_response("Assistant id is needed",False,"CAOAI-VPOST-02",status.HTTP_400_BAD_REQUEST)

        
        thread_id = openai_integration.create_thread()
        if 'error' in thread_id.keys():
            return res.req_response(thread_id['error']['message'],False,"CAOAI-VPOST-01",status.HTTP_400_BAD_REQUEST)
        if farm_id==0:
            farm_id=None
        
        Thread.objects.create(thread_id=thread_id,assistant_id=assistant_id,farmer_id=request.user.id,farm_id=farm_id)

        return res.req_response("Thread found",True,"",status.HTTP_200_OK,{"thread_id": thread_id})
         

class SendConversationView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        openai_integration = OpenAIAPIIntegration()
        data = request.data
        thread_id = data.get('thread_id')
        # image_url = data.get('image_url')
        posttext = data.get('text_response')
        file = request.FILES.get('file', None) 
        url=None
        if file:
            url= helper.image_upload(file)
        if not thread_id :
            return res.req_response("Invalid request",False,"SIVAOI-VPOST-01",status.HTTP_400_BAD_REQUEST)

        response_content = openai_integration.send_image_with_thread(thread_id, posttext,url)
        return res.req_response("Thread found",True,"",status.HTTP_200_OK,response_content)
    

class RunTheConversationView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        openai_integration = OpenAIAPIIntegration()
        data = request.data
        thread_id = data.get('thread_id')
        assistant_id = data.get('assistant_id')

        if not thread_id :
            return res.req_response("Invalid request",False,"SIVAOI-VPOST-01",status.HTTP_400_BAD_REQUEST)

        response_content = openai_integration.run_thread(thread_id, assistant_id)
        return res.req_response("Thread found",True,"",status.HTTP_200_OK,{})
    


class ListTheRunView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        openai_integration = OpenAIAPIIntegration()
        data = request.data
        thread_id = data.get('thread_id')
        # assistant_id = data.get('assistant_id')

        if not thread_id :
            return res.req_response("Invalid request",False,"SIVAOI-VPOST-01",status.HTTP_400_BAD_REQUEST)

        response_content = openai_integration.list_runs(thread_id)
        return res.req_response("Thread found",True,"",status.HTTP_200_OK,response_content)
    

class GetTheRunView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        openai_integration = OpenAIAPIIntegration()
        data = request.data
        thread_id = data.get('thread_id')
        run_id = data.get('run_id')

        if not thread_id :
            return res.req_response("Invalid request",False,"SIVAOI-VPOST-01",status.HTTP_400_BAD_REQUEST)

        response_content = openai_integration.get_run(thread_id,run_id)
        return res.req_response("Thread found",True,"",status.HTTP_200_OK,response_content)



class GetTheMessagesFromThreadView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        openai_integration = OpenAIAPIIntegration()
        data = request.data
        thread_id = data.get('thread_id')

        assistant_id=data.get('assistant_id')
        content=None
        if not thread_id :
            return res.req_response("Invalid request",False,"SIVAOI-VPOST-01",status.HTTP_400_BAD_REQUEST)
       
        count = 0
        delay = 0.5  # initial delay
        while not content:        
            response_run= openai_integration.run_thread(thread_id,assistant_id)
            time.sleep(delay)
            delay=delay+1
            response_content = openai_integration.get_thread_messages(thread_id )
            if response_content and len(response_content['data'])>0 and len(response_content['data'][0]["content"])>0 and response_content['data'][0]['role']=="assistant":
                content=response_content['data'][0]["content"]
            count=count+1
            if count==5:
                return res.req_response("Cannot get any response please try later",False,"SIVAOI-VPOST-02",status.HTTP_400_BAD_REQUEST)

        response_content = openai_integration.get_thread_messages(thread_id )
        return res.req_response("Thread found",True,"",status.HTTP_200_OK,response_content)
       
        
class UpdateFarm(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request,farm_id):
        data= request.data
        khasra_no= data.get('khasra_no')
        type_of_farming= data.get('type_of_farming')
        farm.objects.filter(id=farm_id).update(khasra_no=khasra_no,type_of_farming=type_of_farming)
        return res.req_response( "Farm updated",True,"",status.HTTP_200_OK) 


class ShowFarmReport(APIView):
    

    def get(self,request,farm_id,report_id):
        try:
            farm_data=farm.objects.filter(id=farm_id).get()
            farm_report=FarmReport.objects.filter(farm_id=farm_id,id=report_id).get()
        except Exception as e:
            farm_data=None
            farm_report=None

        prompt="I am providing you a credit report data of a farmer, kindly summarise and explain this data as if you are explaining it to this farmer. Limit reply to 100 words at max. reply without markdown. ignore the cibil score"
        # Convert the data to a JSON string
        data_json = json.dumps(FarmReportSerializer(farm_report).data)
        
        # Create the full prompt by including the JSON data
        full_prompt = f"{prompt}\n\nData: {data_json}"
        openai=OpenAIAPIIntegration()
        summary= openai.get_response_from_prompt(full_prompt)
        geojson_data=FarmsCategory.objects.filter(farm_id=farm_id).first()
        return render(
            request,
            'farm_cibil_report.html',
            {   
                'farm_data':farm_data,
                'farm_report':farm_report,
                'geojson_data':geojson_data.boundary[0],
                'geojson_data_json':json.dumps(geojson_data.boundary[0]),
                'summary':summary
            }
        )

class GetCurrentRequest(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request,farm_id):
        try:
            farm.objects.filter(id=farm_id).get()
        except Exception as e:
            return res.req_response( "Farm not found",False,"RASRF-FRPOST-01",status.HTTP_400_BAD_REQUEST)
        count=RequestForFarmCredit.objects.filter(farm_id=farm_id,status=False).count()
        return res.req_response( "Request sent",True,"",status.HTTP_200_OK,{"count":count}) 

class GetFarmReportList(APIView, PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model = FarmReport

    def get_queryset(self, farm_id):
        queryset = FarmReport.objects.filter(farm_id=farm_id).order_by('-id')
        return queryset

    def get(self, request, farm_id):
        queryset = self.get_queryset(farm_id)
        page = self.paginate_queryset(queryset, request)

        farm_reports = None
        if page:
            farm_reports = FarmReportSerializer(page, many=True).data
            farm_reports = self.get_paginated_response(farm_reports).data

        return res.req_response( "Data found",True,"",status.HTTP_200_OK,farm_reports) 


class SendRequestForFarmReport(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request, farm_id):
        try:
            farm.objects.filter(id=farm_id).get()
        except Exception as e:
            return res.req_response( "Farm not found",False,"RASRF-FRPOST-01",status.HTTP_400_BAD_REQUEST)
        data=RequestForFarmCredit.objects.create(farm_id=farm_id)
        return res.req_response( "Request sent",True,"",status.HTTP_200_OK) 


class SendMailForRequest(APIView):   
    
    def get(self,request):
        # Get the current date

        # Filter farms created today
        today_date = date.today()
        farm_report_ids = FarmReport.objects.filter(created_at__date=today_date).values('farm_id')

        farms_created_today = farms_created_today = farm.objects.filter(
            id__in=Subquery(farm_report_ids)
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
                upload_response = doms_url_handler.upload_file(upload_payload)
                # print(upload_response)
                if upload_response.status_code == 200:
                    # Send email
                    try:
                        ccList=Setting.objects.getKey('SEND_REQUEST_FARM_CREDIT')
                        if ccList:
                            ccList=ccList.value
                    except Setting.DoesNotExist:
                        ccList=""
                    subject = "CSV data for farm credit"
                    send_to = "nitin.tiwari@arya.ag"
                    text = 'CSV is attached for request'
                    mail_sent=self.send_mail_with_attachment(send_to,subject,text,attachment_url,ccList)
                    # print(mail_sent)
                    # Send email with CSV attachment
                    

        # Respond with success message
        return res.req_response('Farm details sent via email.', True,"", status.HTTP_200_OK, data)

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



from django.db.models import Q
from recordActivity.vector_files.advisory_embeddings import embed_text
from recordActivity.models import CropDiseaseAdvisory
from pgvector.django import CosineDistance

def get_related_advisories(client, crop_name: str, disease_name: str, advisory_text: str, top_k: int = 5):
    """
    Fetch related advisories for a given crop_name, disease_name, and advisory_text.
    Uses partial match and vector similarity ranking.
    """
    # Filter advisories for this client and partial match on crop/disease
    related_qs = CropDiseaseAdvisory.objects.filter(client=client).filter(
        Q(crop_name__icontains=crop_name) | Q(disease_or_pest_name__icontains=disease_name)
    )

    if not related_qs.exists():
        return []

    # Compute embedding for advisory text
    query_embedding = embed_text(advisory_text or "")[0]  # single vector (1D list)

    # Annotate with cosine distance and order by similarity (lower = more similar)
    results = related_qs.annotate(
        similarity=CosineDistance("embedding", query_embedding)
    ).order_by("similarity")[:top_k]

    # Convert to dictionary list
    return [
        {
            "cropname": r.crop_name,
            "disease_or_pest_name": r.disease_or_pest_name,
            "stage_of_crop": r.stage_of_crop,
            "symptom_description": r.symptom_description,
            "causal_organism_or_pest": r.causal_organism_or_pest,
            "economic_threshold_level": r.economic_threshold_level,
            "remedy_recommendation": r.remedy_recommendation,
            "similarity_score": round(1 - r.similarity, 4),  # optional normalized score
        }
        for r in results
    ]


from django.conf import settings


class CropDiagnosisService:

    @staticmethod
    def run_diagnosis(thread, check_advisory=False):

        if thread.structured_response:
            return thread.structured_response

        # choose API key
        if hasattr(thread, "external_client"):
            api_key = thread.external_client.get_openai_secret_key()
        else:
            api_key = settings.OPENAI_SECRET

        openai_client = OpenAIResponsesClient(api_key)

        openai_response = openai_client.diagnose_crop(
            image_url=thread.image,
            language=thread.language,
            crop_name=thread.crop_name
        )

        output_text = next(
            item["text"]
            for block in openai_response["output"]
            for item in block["content"]
            if item["type"] == "output_text"
        )

        structured_json = json.loads(output_text)

        disease_name = structured_json.get("disease_name", "")
        advisory_text = structured_json.get("advisory", "")

        if check_advisory:

            related_advisories = get_related_advisories(
                getattr(thread, "external_client", None),
                thread.crop_name,
                disease_name,
                advisory_text
            )

            structured_json["related_advisories"] = related_advisories

        thread.structured_response = structured_json
        thread.raw_openai_response = openai_response
        thread.save()

        return structured_json




from libraries.gemini import GeminiResponsesClient

import json


class GeminiCropDiagnosisService:

    @staticmethod
    def run_diagnosis(
        thread,
        check_advisory=False,internal=False
    ):
        if internal:
            if thread.structured_response:
                return thread.structured_response
            try:
                value= Setting.objects.getKey('ARYASHKATI_GEMINI_EMAIL')
            except Setting.DoesNotExist:
                value=None
            email =value.value if value else ""
            client = ExternalClient.objects.get(email=email)
            gemini_client = GeminiResponsesClient(
                            client.get_openai_secret_key()
                        )
        else:
            gemini_client = GeminiResponsesClient(
                thread.external_client_id.get_openai_secret_key()
            )

        diagnosis = gemini_client.diagnose_crop(
            image_url=thread.image,
            crop_name=thread.crop_name
        )

        if check_advisory:

            crop_name = diagnosis.get("crop_name")
            disease_name = diagnosis.get("disease_name")
            advisory = diagnosis.get("advisory")

            related_advisories = get_related_advisories(
                thread.external_client_id,
                crop_name,
                disease_name,
                advisory
            )

            diagnosis["related_advisories"] = related_advisories

        thread.structured_response = diagnosis
        thread.raw_openai_response = diagnosis
        thread.save()

        return diagnosis



class ThreadService:

    @staticmethod
    def create_external_thread(client, image_url, language, lat, lng, crop_name):
        

        thread_id = str(uuid.uuid4())
        run_id = "run_" + thread_id[:8]

        thread = ExternalThread.objects.create(
            thread_id=thread_id,
            external_client_id=client,
            image=image_url,
            run_id=run_id,
            language=language,
            lat=lat,
            long=lng,
            crop_name=crop_name
        )

        return thread, thread_id, run_id


    @staticmethod
    def create_internal_thread(user, image_url, language, lat, lng, crop_name):

        thread_id = str(uuid.uuid4())
        run_id = "run_" + thread_id[:8]

        thread = InternalThread.objects.create(
            thread_id=thread_id,
            user=user,
            image=image_url,
            run_id=run_id,
            language=language,
            lat=lat,
            long=lng,
            crop_name=crop_name
        )

        return thread, thread_id, run_id


    @staticmethod
    def build_message_response(thread_id, run_id, image_url):
        return {
            "id": f"msg_{thread_id[:10]}",
            "object": "thread.message",
            "created_at": int(time.time()),
            "assistant_id": None,
            "thread_id": thread_id,
            "run_id": run_id,
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url,
                        "detail": "auto"
                    }
                }
            ],
            "attachments": [],
            "metadata": {}
        }




class SendConversationMS(APIView):

    permission_classes = [HasValidTokenPermission]

    def post(self, request):

        client = request.client
        file = request.FILES.get("file")

        language = request.data.get("language", "English")
        lat = request.data.get("latitude", 0)
        lng = request.data.get("longitude", 0)
        crop_name = request.data.get("crop_name", "")

        if not file:
            return res.req_response(
                "File required",
                False,
                "",
                status.HTTP_400_BAD_REQUEST
            )

        # upload image
        try:
            image_url = helper.image_upload(file)
        except ValueError:
            return res.req_response(
                "Unsupported file type",
                False,
                "INVALID_FILE",
                status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            return res.req_response(
                "File upload failed",
                False,
                "UPLOAD_FAILED",
                status.HTTP_400_BAD_REQUEST
            )

        thread, thread_id, run_id = ThreadService.create_external_thread(
            client,
            image_url,
            language,
            lat,
            lng,
            crop_name
        )

        message = ThreadService.build_message_response(
            thread_id,
            run_id,
            image_url
        )

        return res.req_response(
            "Message sent",
            True,
            "",
            status.HTTP_200_OK,
            message
        )


class GetTheMessagesFromThreadViewMS(APIView):

    permission_classes = [HasValidTokenPermission]

    def post(self, request):

        thread_id = request.data.get("thread_id")
        check_advisory = request.data.get("check_advisory")

        if not thread_id:
            return res.req_response("thread_id required",False,"",status.HTTP_400_BAD_REQUEST)

        try:
            thread = ExternalThread.objects.get(thread_id=thread_id)
        except ExternalThread.DoesNotExist:
            return res.req_response("Thread not found",False,"",status.HTTP_404_NOT_FOUND)

        # result = CropDiagnosisService.run_diagnosis(
        #     thread,
        #     check_advisory=check_advisory
        # )

        result = GeminiCropDiagnosisService.run_diagnosis(
            thread,
            check_advisory=check_advisory
        )
        response_data = result
        language = thread.language
        if language and language.lower() not in ["english", "en"]:
            # openai_client = OpenAIResponsesClient(
            #     thread.external_client_id.get_openai_secret_key()
            # )

            # response_data = openai_client.translate_json(
            #     result,
            #     target_language_code=language
            # )

            gemini_client = GeminiResponsesClient(
                thread.external_client_id.get_openai_secret_key()
            )

            result = gemini_client.translate_json(
                result,
                target_language_code=language
            )
        related_advisories = result.pop("related_advisories", [])
        return res.req_response(
            "response found",
            True,
            "",
            status.HTTP_200_OK,
            [
                {
                    "type": "text",
                    "text": {
                        "value": result  
                    }, "related_advisories": related_advisories
                }
            ]
        )







class SendConversationInternal(APIView):

    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        user = request.user
        file = request.FILES.get("file")

        language = request.data.get("language", "English")
        lat = request.data.get("latitude", 0)
        lng = request.data.get("longitude", 0)
        crop_name = request.data.get("crop_name", "")

        if not file:
            return res.req_response(
                "File required",
                False,
                "",
                status.HTTP_400_BAD_REQUEST
            )

        # upload image
        image_url = helper.image_upload(file)

        thread, thread_id, run_id = ThreadService.create_internal_thread(
            user,
            image_url,
            language,
            lat,
            lng,
            crop_name
        )

        message = ThreadService.build_message_response(
            thread_id,
            run_id,
            image_url
        )

        return res.req_response(
            "Message sent",
            True,
            "",
            status.HTTP_200_OK,
            message
        )


class GetTheMessagesFromThreadViewInternal(APIView):

    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        thread_id = request.data.get("thread_id")

        if not thread_id:
            return res.req_response("Invalid request",False,"",status.HTTP_400_BAD_REQUEST)

        try:
            thread = InternalThread.objects.get(
                thread_id=thread_id,
                user=request.user
            )
        except InternalThread.DoesNotExist:
            return res.req_response("Thread not found",False,"",status.HTTP_404_NOT_FOUND)

        # result = CropDiagnosisService.run_diagnosis(thread)
        result = GeminiCropDiagnosisService.run_diagnosis(
                    thread,False,internal=True
                )

        language = thread.language
        if language and language.lower() not in ["english", "en"]:
            # openai_client = OpenAIResponsesClient(
            #     thread.external_client_id.get_openai_secret_key()
            # )

            # response_data = openai_client.translate_json(
            #     result,
            #     target_language_code=language
            # )

            gemini_client = GeminiResponsesClient(
                thread.external_client_id.get_openai_secret_key(),True
            )

            result = gemini_client.translate_json(
                result,
                target_language_code=language
            )

           

        return res.req_response(
            "Thread found",
            True,
            "",
            status.HTTP_200_OK,
            [
                {
                    "type": "text",
                    "text": {
                        "value": result
                    }
                }
            ]
        )



class RemedySendConversationMS(APIView):
    permission_classes = [HasValidTokenPermission]

    def post(self, request):

        
        data = request.data
        lat = data.get('latitude')
        long = data.get('longitude')
        language = data.get('language')
        crop_name= data.get('crop_name')
        disease_name= data.get('disease_name')
        assistant_id=request.client.assistant_id
        client=request.client

        openai_secret_key = client.get_openai_secret_key()
        
        openai_integration = OpenAIAPIIntegration(openai_secret_key)

        if not assistant_id:
            return res.req_response("Assistant is not available in your account, please contact our team.",False,"SIVAOIMS-VPOST-04",status.HTTP_400_BAD_REQUEST)

        if not lat and not long:
            return res.req_response("Latitude longitude are required field",False,"SIVAOIMS-VPOST-04",status.HTTP_400_BAD_REQUEST)

        try:
            check_crop_data=ExternalCropRemedy.objects.filter(crop_name=crop_name,disease_name=disease_name).get()
        except ExternalCropRemedy.DoesNotExist:
            check_crop_data=None
        
        if check_crop_data :
            return res.req_response("Data Found",True,"",status.HTTP_200_OK,check_crop_data.thread_response)

        # thread_id = data.get('thread_id')
        # image_url = data.get('image_url')
        thread_id = openai_integration.create_thread()
        if 'error' in thread_id.keys():
            return res.req_response(thread_id['error']['message'],False,"SIVAOIMS-VPOST-01",status.HTTP_400_BAD_REQUEST)
        
        posttext = f"- Crop: {crop_name}\
                    - Disease/Pest: {disease_name}"


        if language:
            if not posttext:
                posttext=""
            posttext= posttext+"  - Language: "+language
            # print(posttext)
       
        response_content = openai_integration.get_thread_messages(thread_id['id'] )
       
        if response_content and len(response_content['data'])>0 and len(response_content['data'][0]["content"])>0 and response_content['data'][0]['role']=="assistant":
            
            content=response_content['data']
            for i in content:
                if i['role']=="assistant":
                    value=i['content'][0]['text']['value']
                    if value[0]=="{" :
                        json_value=json.loads(value) 
                        if 'type' in json_value and json_value['type']=="EOC":
                            return res.req_response("Please create a new thread, this thread has ended",False,"",status.HTTP_200_OK,i['content'])

                        # print(value)
        
        response_content = openai_integration.send_image_with_thread(thread_id['id'], posttext)
        ExternalCropRemedy.objects.create(thread_id=thread_id['id'],crop_name=crop_name,disease_name=disease_name,thread_response=response_content)
        return res.req_response("Message sent",True,"",status.HTTP_200_OK,response_content)
    






        

class CreateProjectTask(APIView, PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # Number of items per page by default
    page_size = 25
    # Max number of items per page
    max_page_size = 100
    model = ProjectTask

    def get_queryset(self, project_id):
        try:
            project = Project.objects.filter(id=project_id).get()
        except Project.DoesNotExist:
            return []
        
        if project:
            queryset = ProjectTask.objects.filter(project=project)
            
            # Get start_date and end_date from query parameters
            start_date = self.request.query_params.get('start_date')
            end_date = self.request.query_params.get('end_date')

            # If both start_date and end_date are provided, filter by the date range
            if start_date and end_date:
                start_datetime = timezone.datetime.combine(timezone.datetime.strptime(start_date, "%Y-%m-%d").date(), timezone.datetime.min.time())
                end_datetime = timezone.datetime.combine(timezone.datetime.strptime(end_date, "%Y-%m-%d").date(), timezone.datetime.max.time())
                queryset = queryset.filter(created_at__range=(start_datetime, end_datetime))

            return queryset.order_by('-id')

        return ProjectTask.objects.none()

    def get(self, request, project_id):
        queryset = self.get_queryset(project_id)
        page = self.paginate_queryset(queryset, request)
        
        tasks = None
        if page:
            tasks = ProjectTaskSerializer(page, many=True).data
            tasks = self.get_paginated_response(tasks).data
        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,tasks)

    def post(self, request,project_id):
        data = request.data
        validator = ProjectTaskValidator(data=data)
        
        if not validator.is_valid():
            errors = validator.errors
            return res.req_response(constants.INVALID_BODY,False,"RA-CPT-POST-01",status.HTTP_400_BAD_REQUEST)
            
        project = None
        try:
            project = Project.objects.filter(id=project_id).get()
        except Project.DoesNotExist:
            return res.req_response("Project not found",False,"RA-CPT-POST-02",status.HTTP_404_NOT_FOUND)
            

        custom_form = None
        if 'custom_form_id' in data.keys():
            try:
                custom_form = CustomForm.objects.filter(id=data['custom_form_id']).get()
            except CustomForm.DoesNotExist:
                return res.req_response("Custom Form not found",False,"RA-CPT-POST-03",status.HTTP_404_NOT_FOUND)

        activity = None
        if 'activity_id' in data.keys():
            try:
                activity = ActivityRecord.objects.filter(id=data['activity_id']).get()
            except CustomForm.DoesNotExist:
                return res.req_response("Activity not found",False,"RA-CPT-POST-04",status.HTTP_404_NOT_FOUND)


        project_task = ProjectTask.objects.create(
            task_name=data['task_name'],
            project=project,
            task_type=data['task_type'],
            custom_form=custom_form,
            created_by=request.user,
            activity_record=activity
        )

        

        return res.req_response("Project Task created",True,"",status.HTTP_201_CREATED,ProjectTaskSerializer(project_task).data)
       

class CreateProjectTaskFarm(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]


    # Number of items per page by default
    page_size = 25
    # Max number of items per page
    max_page_size = 100
    model = ProjectTaskUser

    def get_queryset(self,request, user_id, project_task_id=None,):
        project_task=None
        if project_task_id:
            try:
                project_task = ProjectTask.objects.get(id=project_task_id)
            except ProjectTask.DoesNotExist:
                return ProjectTaskUser.objects.none()

        queryset = ProjectTaskUser.objects.filter(assigned_to_id=user_id)

        if project_task:
            queryset= queryset.filter(project_task=project_task)

        # Get start_date and end_date from query parameters
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        farm_id = self.request.query_params.get('farm_id')

        if farm_id:
            queryset= queryset.filter(farm_id=farm_id)

        if start_date and end_date:
            start_datetime = timezone.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S%z")
            end_datetime = timezone.datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S.%f%z")
            queryset = queryset.filter(created_at__range=(start_datetime, end_datetime))

        return queryset.order_by('-id')

    def get(self, request,project_task_id=None):
       
        queryset = self.get_queryset(request,request.user.id,project_task_id)
        page = self.paginate_queryset(queryset, request)

        task_users = None
        if page:
            task_users = ProjectTaskUserSerializer(page, many=True).data
            task_users = self.get_paginated_response(task_users).data
        return res.req_response("Data found",True,"",status.HTTP_200_OK,task_users)


    def post(self, request):
        data = request.data
        assigned_to = data.get('assigned_to_id')
        farm_id = data.get('farm_id')
        project_task_id = data.get('project_task_id')
        json_data= data.get('json_data')
        status_data= data.get('status')

        if data.get('project_task_user_id'):
            project_task_user=ProjectTaskUser.objects.filter(id=data['project_task_user_id']).update(status=status_data,
                    json_data=json_data)
        else:
            try:
                project_task = ProjectTask.objects.get(id=project_task_id)
            except ProjectTask.DoesNotExist:
                return res.req_response("Project Task  not found",False,"RA-CPTF-POST-01",status.HTTP_404_NOT_FOUND)
            
            if not status_data:
                status_data="pending"
            try:
                farm_data = farm.objects.get(id=farm_id)  # Ensure farm exists
            except farm.DoesNotExist:
                return res.req_response("Farm not found",False,"RA-CPTF-POST-02",status.HTTP_404_NOT_FOUND)

            project_task_user = ProjectTaskUser.objects.create(
                assigned_to_id=assigned_to,
                project_task=project_task,
                farm=farm_data,
                status= status_data,
                json_data=json_data
                
            )
        return res.req_response("Project Task Users updated successfully",True,"",status.HTTP_200_OK)

from libraries.ai_task_worker import *

class AssignTask(APIView):

    def post(self,request):
        # try:
            assign_farm_tasks_test()  # Call task function
            return Response({"message": "Farm tasks assigned successfully!"}, status=status.HTTP_200_OK)
        # except Exception as e:
        #     return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from libraries.fyllo import Fyllo
class GetWeatherBasedDetails(APIView):
    def get(self, request, farm):
        try:
            # Fetch plot_id using farm_id
            relation = FarmFylloFarmData.objects.select_related('farm_fyllow').get(farm_id=farm)
            plot_id = relation.farm_fyllow.plot_id
        except FarmFylloFarmData.DoesNotExist:
            return res.req_response("Not Found", False, f"No plot linked to farm {farm}", status.HTTP_404_NOT_FOUND)

        fyllo = Fyllo()
        live_data = {}

        if fyllo.authenticate():
            live_data = fyllo.get_live_data(plot_id=plot_id)
        else:
            return res.req_response("Auth Failed", False, "Failed to authenticate with Fyllo", status.HTTP_401_UNAUTHORIZED)

        return res.req_response("Data", True, "", status.HTTP_200_OK, live_data)



class TrainingExecutionAPI(APIView, PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    page_size = 25
    max_page_size = 100

    # -------------------- GET --------------------
    def get_queryset(self, query_text):
        user = self.request.user

        queryset = (
            Training.objects.filter(is_active=1)
        )


        return queryset

    def get(self, request):
        query_text = request.GET.get("query_text")

        queryset = self.get_queryset(query_text)
        page = self.paginate_queryset(queryset, request)

        data = None
        if page:
            data = TrainingSerializer(page, many=True).data
            data = self.get_paginated_response(data).data

        return res.req_response(
            "Data found",
            True,
            "",
            status.HTTP_200_OK,
            data
        )

    # -------------------- POST --------------------
    def post(self, request):
        data = request.data
        org= request.user.organization
        training_id = data.get("training_id")
        # farm_ids = data.get("farm_ids", [])
        form_response = data.get("form_response")

        # -------------------------
        # Basic validations
        # -------------------------
        if not training_id or not form_response :
            result = res.ErrRes()
            result["message"] = constants.INVALID_BODY
            result["error_code"] = "TRN-EXE-POST-01"
            return Response(result, status=result["status_code"])

        # -------------------------
        # Training existence check
        # -------------------------
        try:
            training = Training.objects.get(id=training_id)
        except Training.DoesNotExist:
            result = res.ErrRes()
            result["message"] = "Invalid training id"
            result["error_code"] = "TRN-EXE-POST-02"
            return Response(result, status=result["status_code"])

        # -------------------------
        # Farm existence check
        # -------------------------
        # valid_farm_ids = set(
        #     farm.objects.filter(id__in=farm_ids).values_list("id", flat=True)
        # )

        # invalid_farm_ids = set(farm_ids) - valid_farm_ids
        # if invalid_farm_ids:
        #     result = res.ErrRes()
        #     result["message"] = f"Invalid farm ids: {list(invalid_farm_ids)}"
        #     result["error_code"] = "TRN-EXE-POST-03"
        #     return Response(result, status=result["status_code"])

        # -------------------------
        # Parse JSON safely
        # -------------------------
        if form_response and isinstance(form_response, str):
            try:
                form_response = json.loads(form_response)
            except json.JSONDecodeError:
                result = res.ErrRes()
                result["message"] = "Invalid form_response JSON"
                result["error_code"] = "TRN-EXE-POST-04"
                return Response(result, status=result["status_code"])

        # -------------------------
        # Create execution
        # -------------------------
        training_execution = TrainingExecution.objects.create(
            training=training,
            conducted_by=request.user,
            form_response=form_response,organization=org
        )

        # -------------------------
        # Map farms (bulk)
        # -------------------------
        # TrainingExecutionFarm.objects.bulk_create([
        #     TrainingExecutionFarm(
        #         training_execution=training_execution,
        #         farm_id=farm_id
        #     )
        #     for farm_id in valid_farm_ids
        # ])

        return res.req_response(
            "Training recorded successfully",
            True,
            "",
            status.HTTP_200_OK
        )



class TrainingFormAPIView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, training_id=False):
        # -------------------------
        # Training existence check
        # -------------------------
        try:
            training = (
                Training.objects
                .select_related("custom_form")
                .get(id=training_id)
            )
        except Training.DoesNotExist:
            result = res.ErrRes()
            result["message"] = "Invalid training id"
            result["error_code"] = "TRN-FRM-GET-01"
            return Response(result, status=result["status_code"])

        # -------------------------
        # Custom form check
        # -------------------------
        if not training.custom_form:
            result = res.ErrRes()
            result["message"] = "No form linked with this training"
            result["error_code"] = "TRN-FRM-GET-02"
            return Response(result, status=result["status_code"])

        serializer = TrainingFormSerializer(training)

        return res.req_response(
            "Form fetched successfully",
            True,
            "",
            status.HTTP_200_OK,
            serializer.data
        )

class TrainingExecutionListAPI(APIView, PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    page_size = 25
    max_page_size = 100

    # -------------------- GET --------------------
    def get_queryset(self):
        user = self.request.user
        org= user.organization
        # print(user,org)
        queryset = (
            TrainingExecution.objects.filter(organization=org,conducted_by=user)
        )


        return queryset

    def get(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset, request)

        data = None
        if page:
            data = TrainingExecutionSerializer(page, many=True).data
            data = self.get_paginated_response(data).data

        return res.req_response(
            "Data found",
            True,
            "",
            status.HTTP_200_OK,
            data
        )


class CtQuestionsAPIView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = CtQuestions.objects.filter(is_active=True).order_by("id")
        serializer = CtQuestionSerializer(queryset, many=True)

        return res.req_response(
            "Questions fetched successfully",
            True,
            "",
            status.HTTP_200_OK,
            serializer.data,
        )


class CtQuestionsFarmAPIView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, question_id, user_id,farm_id):
        try:
            user_obj = user.objects.get(id=user_id)
        except user.DoesNotExist:
            result = res.ErrRes()
            result["message"] = "Invalid user id"
            result["error_code"] = "CT-RES-GET-01"
            return Response(result, status=result["status_code"])

        try:
            farm_obj = farm.objects.get(id=farm_id)
        except farm.DoesNotExist:
            result = res.ErrRes()
            result["message"] = "Invalid farm id"
            result["error_code"] = "CT-RES-GET-02"
            return Response(result, status=result["status_code"])

        try:
            question = CtQuestions.objects.get(id=question_id, is_active=True)
        except CtQuestions.DoesNotExist:
            result = res.ErrRes()
            result["message"] = "Invalid question id"
            result["error_code"] = "CT-RES-GET-03"
            return Response(result, status=result["status_code"])

        pending_response = (
            CtQuestionsFarm.objects.filter(
                ct_question_id=question_id,
                user=user_obj,
                farm=farm_obj,
                status="pending",
            )
            .select_related("ct_question", "user", "farm")
            .order_by("-updated_at")
            .first()
        )

        if pending_response:
            serializer = CtQuestionsFarmSerializer(pending_response)
            return res.req_response(
                "Pending draft fetched successfully",
                True,
                "",
                status.HTTP_200_OK,
                serializer.data,
            )

        return res.req_response(
            "Question details fetched successfully",
            True,
            "",
            status.HTTP_200_OK,
            {},
        )

    def post(self, request):
        validator = CtQuestionResponseValidator(data=request.data)
        if not validator.is_valid():
            return Response(validator.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = validator.validated_data
        record_id = validated_data.get("id")
        question_id = validated_data.get("question_id")
        farm_id = validated_data.get("farm_id")
        response_data = validated_data.get("response")
        status_value = validated_data.get("status", "pending")
        user_id = validated_data.get("user_id", request.user.id)

        try:
            question = CtQuestions.objects.get(id=question_id, is_active=True)
        except CtQuestions.DoesNotExist:
            result = res.ErrRes()
            result["message"] = "Invalid question id"
            result["error_code"] = "CT-RES-POST-01"
            return Response(result, status=result["status_code"])

        try:
            farm_obj = farm.objects.get(id=farm_id)
        except farm.DoesNotExist:
            result = res.ErrRes()
            result["message"] = "Invalid farm id"
            result["error_code"] = "CT-RES-POST-02"
            return Response(result, status=result["status_code"])

        try:
            user_obj = user.objects.get(id=user_id)
        except user.DoesNotExist:
            result = res.ErrRes()
            result["message"] = "Invalid user id"
            result["error_code"] = "CT-RES-POST-03"
            return Response(result, status=result["status_code"])

        if isinstance(response_data, str):
            try:
                response_data = json.loads(response_data)
            except json.JSONDecodeError:
                result = res.ErrRes()
                result["message"] = "Invalid response JSON"
                result["error_code"] = "CT-RES-POST-04"
                return Response(result, status=result["status_code"])

        response_payload = response_data if response_data is not None else {}

        if record_id:
            try:
                ct_question_response = CtQuestionsFarm.objects.get(id=record_id)
            except CtQuestionsFarm.DoesNotExist:
                result = res.ErrRes()
                result["message"] = "Invalid response id"
                result["error_code"] = "CT-RES-POST-05"
                return Response(result, status=result["status_code"])

            ct_question_response.response = response_payload
            ct_question_response.status = status_value
            ct_question_response.save(update_fields=["response", "status", "updated_at"])
        else:
            ct_question_response = CtQuestionsFarm.objects.create(
                ct_question=question,
                user=user_obj,
                added_by=request.user,
                farm=farm_obj,
                response=response_payload,
                status=status_value,
            )

        serializer = CtQuestionsFarmSerializer(ct_question_response)
        return res.req_response(
            "Question response saved successfully",
            True,
            "",
            status.HTTP_200_OK,
            serializer.data,
        )


class DroneSprayListCreate(APIView, PageNumberPagination):

    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    page_size = 25
    max_page_size = 100

    def _prepare_farm_data(self, base_data, farm_obj, user):
        farm_data = base_data.copy()
        farm_data['farm'] = farm_obj.id
        farm_data['organization'] = farm_obj.org_id.id
        farm_data['farmer'] = farm_obj.user.id if farm_obj.user else None
        farm_data['state'] = farm_obj.farm_state
        farm_data['district'] = farm_obj.farm_district
        farm_data['tehsil'] = farm_obj.farm_taluka
        farm_data['village'] = farm_obj.farm_village
        farm_data['crop'] = farm_obj.crop_id.crop_name if farm_obj.crop_id else None
        farm_data['area_total'] = farm_obj.total_area if farm_obj.total_area is not None else None
        
        # Set audit fields
        farm_data['created_by'] = user.id
        farm_data['requested_by'] = user.id
        
        return farm_data
    
    def _send_booking_request_email(self, booking, user):
        """Send email notification when farmer requests a drone spray"""
        from app_farm.utils import helper
        
        # Get email template from helper
        subject, text_content, html_content = helper.get_drone_spray_booking_request_email_template(booking, user)
        
        # Send email
        success, message = helper.send_email_notification(
            subject=subject,
            text_content=text_content,
            html_content=html_content,
            recipients_key='DRONE_SPRAY_EMAIL_RECIPIENTS'
        )
        
        return success, message

    def get(self, request):
        """Get list of drone spray bookings with filters"""
        try:
            # Base queryset
            queryset = DroneSprayActivity.objects.select_related(
                'farm',
                'farmer',
                'organization',
                'custom_form'
            ).all()
            
            # Apply filters
            farm_id = request.GET.get('farm_id')
            if farm_id:
                queryset = queryset.filter(farm_id=farm_id)
            
            status_filter = request.GET.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter.upper())
            
            district = request.GET.get('district')
            if district:
                queryset = queryset.filter(district__iexact=district)
            
            organization = request.GET.get('organization')
            if organization:
                queryset = queryset.filter(organization_id=organization)
            
            farmer = request.GET.get('farmer')
            if farmer:
                queryset = queryset.filter(farmer_id=farmer)
            
            # Order by created date (newest first)
            queryset = queryset.order_by('-created_at')
            
            # Paginate
            page = self.paginate_queryset(queryset, request)
            
            if page is not None:
                serializer = DroneSprayActivitySerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = DroneSprayActivitySerializer(queryset, many=True)
            return res.req_response(
                "Drone spray bookings retrieved successfully",
                True,
                "RAV-DSL-00",
                status.HTTP_200_OK,
                serializer.data
            )
            
        except Exception as e:
            return res.req_response(
                "An unexpected error occurred",
                False,
                "RAV-DSL-05",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {"error": str(e)}
            )

    def post(self, request):

        try:
            data = request.data.copy()
            
            farm_ids = data.get('farm')
            if not farm_ids:
                return res.req_response(
                    "Farm ID(s) required",
                    False,
                    "RAV-CDSB-02",
                    status.HTTP_400_BAD_REQUEST,
                    {"farm": ["This field is required."]}
                )
            
            if not isinstance(farm_ids, list):
                farm_ids = [farm_ids]
            
            farms = farm.objects.select_related(
                'user', 
                'org_id', 
                'crop_id'
            ).filter(id__in=farm_ids)
            
            farms_dict = {f.id: f for f in farms}
            
            found_ids = set(farms_dict.keys())
            missing_ids = set(farm_ids) - found_ids
            
            created_bookings = []
            failed_bookings = []
            
            for missing_id in missing_ids:
                failed_bookings.append({
                    "farm_id": missing_id,
                    "error": f"Farm with ID {missing_id} does not exist.",
                    "error_code": "RAV-CDSB-03"
                })
            
            for farm_id in farm_ids:
                if farm_id not in farms_dict:
                    continue  
                
                try:
                    farm_obj = farms_dict[farm_id]
                    
                    if not farm_obj.org_id:
                        failed_bookings.append({
                            "farm_id": farm_id,
                            "error": "Farm does not belong to any organization",
                            "error_code": "RAV-CDSB-04"
                        })
                        continue
                    
                    farm_data = self._prepare_farm_data(data, farm_obj, request.user)
                    
                    serializer = DroneSprayActivitySerializer(data=farm_data)
                    
                    if not serializer.is_valid():
                        failed_bookings.append({
                            "farm_id": farm_id,
                            "error": serializer.errors,
                            "error_code": "RAV-CDSB-01"
                        })
                        continue
                    
                    drone_spray = serializer.save()
                    created_bookings.append(DroneSprayActivitySerializer(drone_spray).data)
                    
                    # Send booking request email notification
                    try:
                        self._send_booking_request_email(drone_spray, request.user)
                    except Exception as email_error:
                        # Log email error but don't fail the booking creation
                        pass
                    
                except Exception as farm_error:
                    failed_bookings.append({
                        "farm_id": farm_id,
                        "error": str(farm_error),
                        "error_code": "RAV-CDSB-05"
                    })
            
            if not created_bookings and failed_bookings:
                # All failed
                return res.req_response(
                    "Failed to create any drone spray bookings",
                    False,
                    "RAV-CDSB-06",
                    status.HTTP_400_BAD_REQUEST,
                    {"failed": failed_bookings}
                )
            
            response_data = {
                "created": created_bookings,
                "created_count": len(created_bookings)
            }
            
            if failed_bookings:
                response_data["failed"] = failed_bookings
                response_data["failed_count"] = len(failed_bookings)
            
            return res.req_response(
                f"Successfully created {len(created_bookings)} drone spray booking(s)",
                True,
                "RAV-CDSB-00",
                status.HTTP_201_CREATED,
                response_data
            )
            
        except Exception as e:
            return res.req_response(
                "An unexpected error occurred",
                False,
                "RAV-CDSB-05",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {"error": str(e)}
            )


class ExecuteDroneSprayBooking(APIView):

    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, booking_id):
        """Get booking details with prefilled data for CVRP form"""
        try:
            try:
                booking = DroneSprayActivity.objects.select_related(
                    'farm',
                    'farm__crop_id',
                    'organization'
                ).get(id=booking_id)
            except DroneSprayActivity.DoesNotExist:
                return res.req_response(
                    "Booking not found",
                    False,
                    "RAV-EDSB-02",
                    status.HTTP_404_NOT_FOUND,
                    {"id": ["Booking does not exist."]}
                )
            
            booking_data = DroneSprayActivitySerializer(booking).data
            
            return res.req_response(
                "Booking details retrieved successfully",
                True,
                "RAV-EDSB-00",
                status.HTTP_200_OK,
                booking_data
            )
            
        except Exception as e:
            return res.req_response(
                "An unexpected error occurred",
                False,
                "RAV-EDSB-05",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {"error": str(e)}
            )

    def patch(self, request, booking_id):
        """Update execution details and change status to IN_PROGRESS"""
        try:
            data = request.data.copy()
            
            try:
                booking = DroneSprayActivity.objects.select_related('farm').get(id=booking_id)
            except DroneSprayActivity.DoesNotExist:
                return res.req_response(
                    "Booking not found",
                    False,
                    "RAV-EDSB-02",
                    status.HTTP_404_NOT_FOUND,
                    {"id": ["Booking does not exist."]}
                )
            
            # Validate status transition
            if booking.status not in ['PENDING', 'REQUESTED', 'IN_PROGRESS']:
                return res.req_response(
                    f"Cannot update booking with status {booking.status}",
                    False,
                    "RAV-EDSB-03",
                    status.HTTP_400_BAD_REQUEST,
                    {"status": [f"Booking is in {booking.status} status. Only PENDING, REQUESTED, or IN_PROGRESS bookings can be updated."]}
                )
            
            # ========== UPDATE FARM DATA (if provided) ==========
            farm = booking.farm
            farm_updated = False
            
            if 'farm_data' in data:
                farm_data = data['farm_data']
                
                if 'farm_state' in farm_data:
                    farm.farm_state = farm_data['farm_state']
                    farm_updated = True
                
                if 'farm_district' in farm_data:
                    farm.farm_district = farm_data['farm_district']
                    farm_updated = True
                
                if 'farm_taluka' in farm_data:
                    farm.farm_taluka = farm_data['farm_taluka']
                    farm_updated = True
                
                if 'farm_village' in farm_data:
                    farm.farm_village = farm_data['farm_village']
                    farm_updated = True

                # Save farm if updated
                if farm_updated:
                    farm.updated_by_id = request.user
                    farm.save()
                    booking.state = farm.farm_state
                    booking.district = farm.farm_district
                    booking.tehsil = farm.farm_taluka
                    booking.village = farm.farm_village
                    if not booking.area_sprayed_unit:
                        booking.area_sprayed_unit = farm.area_unit
            
            # Update execution fields
            if 'spray_cycle' in data:
                booking.spray_cycle = data['spray_cycle']
            
            if 'date_of_spraying' in data:
                booking.date_of_spraying = data['date_of_spraying']
            
            if 'crop_stage' in data:
                booking.crop_stage = data['crop_stage']
            
            if 'pest_or_activity' in data:
                booking.pest_or_activity = data['pest_or_activity']
            
            if 'products' in data:
                products = data['products']
                # Validate products format
                if not isinstance(products, list):
                    return res.req_response(
                        "Products must be a list",
                        False,
                        "RAV-EDSB-01",
                        status.HTTP_400_BAD_REQUEST,
                        {"products": ["Must be a list of product objects"]}
                    )
                
                for idx, product in enumerate(products):
                    if not isinstance(product, dict):
                        return res.req_response(
                            f"Product at index {idx} must be an object",
                            False,
                            "RAV-EDSB-01",
                            status.HTTP_400_BAD_REQUEST,
                            {"products": [f"Product at index {idx} is not a valid object"]}
                        )
                    
                    required_keys = ['product_name', 'dosage', 'unit']
                    missing_keys = [key for key in required_keys if key not in product]
                    if missing_keys:
                        return res.req_response(
                            f"Product at index {idx} missing required fields",
                            False,
                            "RAV-EDSB-01",
                            status.HTTP_400_BAD_REQUEST,
                            {"products": [f"Product at index {idx} missing: {', '.join(missing_keys)}"]}
                        )
                
                booking.products = products
            
            if 'area_sprayed' in data:
                area_sprayed = data['area_sprayed']
                
                # Validate area_sprayed is not greater than area_total
                if booking.area_total and float(area_sprayed) > float(booking.area_total):
                    return res.req_response(
                        "Area sprayed cannot exceed total area",
                        False,
                        "RAV-EDSB-01",
                        status.HTTP_400_BAD_REQUEST,
                        {"area_sprayed": [f"Area sprayed ({area_sprayed}) cannot exceed total area ({booking.area_total})"]}
                    )
                
                booking.area_sprayed = area_sprayed
            
            if 'area_sprayed_unit' in data:
                booking.area_sprayed_unit = data['area_sprayed_unit']
            
            # Change status to IN_PROGRESS
            booking.status = 'IN_PROGRESS'
            booking.save()
            
            # Build success message
            message = "Execution details updated successfully"
            if farm_updated:
                message = "Execution details and farm data updated successfully"
            
            return res.req_response(
                message,
                True,
                "RAV-EDSB-00",
                status.HTTP_200_OK,
                DroneSprayActivitySerializer(booking).data
            )
            
        except Exception as e:
            return res.req_response(
                "An unexpected error occurred",
                False,
                "RAV-EDSB-05",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {"error": str(e)}
            )


class DroneSprayStatusUpdate(APIView):

    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def patch(self, request, booking_id):
        """Update status to REJECTED, CANCELLED, or FAILED"""
        try:
            data = request.data
            
            new_status = data.get('status')
            if not new_status:
                return res.req_response(
                    "Status is required",
                    False,
                    "RAV-DSSU-01",
                    status.HTTP_400_BAD_REQUEST,
                    {"status": ["This field is required."]}
                )
            
            allowed_statuses = ['REJECTED', 'CANCELLED', 'FAILED']
            if new_status not in allowed_statuses:
                return res.req_response(
                    f"Invalid status. Must be one of: {', '.join(allowed_statuses)}",
                    False,
                    "RAV-DSSU-03",
                    status.HTTP_400_BAD_REQUEST,
                    {"status": [f"Status must be one of: {', '.join(allowed_statuses)}"]}
                )
            
            try:
                booking = DroneSprayActivity.objects.get(id=booking_id)
            except DroneSprayActivity.DoesNotExist:
                return res.req_response(
                    "Booking not found",
                    False,
                    "RAV-DSSU-02",
                    status.HTTP_404_NOT_FOUND,
                    {"id": ["Booking does not exist."]}
                )
            
            booking.status = new_status
            
            if new_status == 'REJECTED':
                rejection_reason = data.get('rejection_reason')
                if not rejection_reason:
                    return res.req_response(
                        "Rejection reason is required for REJECTED status",
                        False,
                        "RAV-DSSU-01",
                        status.HTTP_400_BAD_REQUEST,
                        {"rejection_reason": ["This field is required when status is REJECTED."]}
                    )
                
                booking.rejection_reason = rejection_reason
                booking.rejected_by = request.user
                booking.rejected_at = timezone.now()
            
            if new_status in ['CANCELLED', 'FAILED']:
                reason = data.get('rejection_reason') or data.get('reason')
                if reason:
                    booking.rejection_reason = reason
            
            booking.save()
            
            return res.req_response(
                f"Booking status updated to {new_status}",
                True,
                "RAV-DSSU-00",
                status.HTTP_200_OK,
                DroneSprayActivitySerializer(booking).data
            )
            
        except Exception as e:
            return res.req_response(
                "An unexpected error occurred",
                False,
                "RAV-DSSU-05",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {"error": str(e)}
            )


class DroneSprayDetail(APIView):

    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, booking_id):
        """Get detailed information about a specific booking"""
        try:
            try:
                booking = DroneSprayActivity.objects.select_related(
                    'farm',
                    'farmer',
                    'organization',
                    'custom_form',
                    'created_by',
                    'requested_by',
                    'rejected_by'
                ).get(id=booking_id)
            except DroneSprayActivity.DoesNotExist:
                return res.req_response(
                    "Booking not found",
                    False,
                    "RAV-DSD-02",
                    status.HTTP_404_NOT_FOUND,
                    {"id": ["Booking does not exist."]}
                )
            
            booking_data = DroneSprayActivitySerializer(booking).data
            
            return res.req_response(
                "Booking details retrieved successfully",
                True,
                "RAV-DSD-00",
                status.HTTP_200_OK,
                booking_data
            )
            
        except Exception as e:
            return res.req_response(
                "An unexpected error occurred",
                False,
                "RAV-DSD-05",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {"error": str(e)}
            )

class DroneSprayWebhook(APIView):

    permission_classes = [AllowAny]

    def _validate_and_get_activity(self, reference_id):
        """Validate reference_id and get activity."""
        if not reference_id:
            return None, res.req_response(
                "Missing 'reference_id' in webhook payload",
                False,
                "RAV-DSW-01",
                status.HTTP_400_BAD_REQUEST
            )
        
        try:
            activity = DroneSprayActivity.objects.select_related(
                'farm', 'farmer', 'organization'
            ).get(reference_id=reference_id)
            return activity, None
        except DroneSprayActivity.DoesNotExist:
            return None, res.req_response(
                f"Booking with reference_id '{reference_id}' not found",
                False,
                "RAV-DSW-02",
                status.HTTP_404_NOT_FOUND
            )
    
    def _check_idempotency(self, activity, reference_id):
        """Check if webhook already processed."""
        if activity.status == "COMPLETED":
            return res.req_response(
                "Webhook already processed - booking is COMPLETED",
                True,
                "RAV-DSW-00",
                status.HTTP_200_OK,
                {
                    "reference_id": reference_id,
                    "status": activity.status,
                    "message": "Idempotent webhook - no changes made"
                }
            )
        return None
    
    def _prepare_webhook_payload(self, data):
        """Prepare webhook payload excluding non-serializable objects."""
        webhook_payload_data = {}
        for key, value in data.items():
            if not hasattr(value, 'read'):
                webhook_payload_data[key] = value
        return webhook_payload_data
    
    def _process_geojson(self, activity, request, data):
        """Process GeoJSON file or URL."""
        geojson_features = None
        geojson_file = request.FILES.get("geojson_file")
        geojson_url = data.get("geojson_url")
        
        if geojson_file:
            try:
                geojson_file_url, geojson_features, geometry, calculated_area = self._upload_and_parse_geojson_file(geojson_file)
                activity.geojson_file = geojson_file_url
                activity.spray_area_coordinates = geojson_features
                if geometry:
                    activity.geojson_geometry = geometry
                if calculated_area:
                    activity.geojson_area = calculated_area
            except Exception as e:
                activity.webhook_status = "GEOJSON_UPLOAD_FAILED"
                activity.save()
                raise ValueError(f"Failed to upload GeoJSON file: {str(e)}") from e
        
        elif geojson_url:
            try:
                geojson_file_url, geojson_features, geometry, calculated_area = self._download_and_parse_geojson(geojson_url)
                activity.geojson_file = geojson_file_url
                activity.spray_area_coordinates = geojson_features
                if geometry:
                    activity.geojson_geometry = geometry
                if calculated_area:
                    activity.geojson_area = calculated_area
            except Exception as e:
                activity.webhook_status = "GEOJSON_DOWNLOAD_FAILED"
                activity.save()
                raise ValueError(f"Failed to download GeoJSON file: {str(e)}") from e
        
        return geojson_features
    
    def _update_spray_details(self, activity, area_sprayed_from_webhook, executed_at):
        """Update spray execution details."""
        if area_sprayed_from_webhook:
            try:
                area_value = float(area_sprayed_from_webhook)
                
                if activity.area_total and area_value > float(activity.area_total):
                    return res.req_response(
                        f"Area sprayed ({area_value}) cannot exceed farm area ({activity.area_total})",
                        False,
                        "RAV-DSW-05",
                        status.HTTP_400_BAD_REQUEST
                    )
                
                activity.area_sprayed = area_value
            except (ValueError, TypeError):
                pass
        
        if executed_at:
            try:
                from dateutil import parser
                activity.date_of_spraying = parser.parse(executed_at).date()
            except Exception:
                pass
        
        return None
    
    def post(self, request):

        data = request.data if request.data else request.POST.dict()
        reference_id = data.get("reference_id")
        
        # Validate and get activity
        activity, error_response = self._validate_and_get_activity(reference_id)
        if error_response:
            return error_response
        
        # Check idempotency
        idempotent_response = self._check_idempotency(activity, reference_id)
        if idempotent_response:
            return idempotent_response
        
        # Use atomic transaction
        from django.db import transaction
        
        try:
            with transaction.atomic():
                # Store webhook data
                activity.webhook_payload = self._prepare_webhook_payload(data)
                activity.webhook_received_at = timezone.now()
                activity.webhook_reference_id = data.get("vendor_job_id")
                area_sprayed_from_webhook = data.get("area_sprayed")
                executed_at = data.get("executed_at")
                
                # Process GeoJSON
                try:
                    geojson_features = self._process_geojson(activity, request, data)
                except Exception as e:
                    return res.req_response(
                        str(e),
                        False,
                        "RAV-DSW-04",
                        status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Update spray details
                error_response = self._update_spray_details(activity, area_sprayed_from_webhook, executed_at)
                if error_response:
                    return error_response
                
                # Mark as COMPLETED
                activity.status = "COMPLETED"
                activity.webhook_status = "SUCCESS"
                activity.completed_at = timezone.now()
                activity.save()
                
                return res.req_response(
                    "Webhook processed successfully - booking marked COMPLETED",
                    True,
                    "RAV-DSW-00",
                    status.HTTP_200_OK,
                    {
                        "reference_id": reference_id,
                        "booking_id": activity.id,
                        "status": activity.status,
                        "area_sprayed": str(activity.area_sprayed) if activity.area_sprayed else None,
                        "geojson_area": str(activity.geojson_area) if activity.geojson_area else None,
                        "geojson_uploaded": bool(activity.geojson_file),
                        "spray_area_coordinates": geojson_features if geojson_features else None,
                        "completed_at": activity.completed_at.isoformat() if activity.completed_at else None,
                        "vendor_job_id": activity.webhook_reference_id
                    }
                )
        
        except Exception as e:
            return res.req_response(
                "An unexpected error occurred processing webhook",
                False,
                "RAV-DSW-06",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {"error": str(e)}
            )
    
    def _calculate_area_from_geojson(self, geojson_features):
        """Calculate area from GeoJSON features and return geometry + area in acres"""
        from django.contrib.gis.geos import GEOSGeometry
        from django.contrib.gis.measure import Area
        
        if not geojson_features:
            return None, None
        
        try:
            # Get the first feature's geometry
            first_feature = geojson_features[0]
            geometry_data = first_feature.get('geometry')
            
            if not geometry_data:
                return None, None
            
            # Convert GeoJSON geometry to Django GEOSGeometry
            geometry = GEOSGeometry(json.dumps(geometry_data))
            
            # Calculate area (result is in square meters for WGS84)
            area_sq_meters = geometry.area
            
            # Convert square meters to acres (1 acre = 4046.86 square meters)
            area_acres = area_sq_meters / 4046.86
            
            return geometry, round(area_acres, 2)
            
        except Exception as e:
            # If calculation fails, return None
            return None, None
    
    def _upload_and_parse_geojson_file(self, geojson_file):
        """Handle direct GeoJSON file upload"""
        import json
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if geojson_file.size > max_size:
            raise ValueError(f"GeoJSON file too large: {geojson_file.size} bytes (max {max_size})")
        
        # Read and parse GeoJSON content
        try:
            file_content = geojson_file.read()
            geojson_data = json.loads(file_content)
            # Extract features for frontend display
            geojson_features = geojson_data.get('features', [])
        except json.JSONDecodeError:
            raise ValueError("Invalid GeoJSON format")
        except Exception as e:
            raise ValueError(f"Error reading GeoJSON file: {str(e)}")
        
        # Calculate area and geometry from features
        geometry, calculated_area = self._calculate_area_from_geojson(geojson_features)
        
        # Reset file pointer for upload
        geojson_file.seek(0)
        
        # Upload file using helper
        uploaded_url = helper.image_upload(geojson_file)
        return uploaded_url, geojson_features, geometry, calculated_area
    
    def _download_and_parse_geojson(self, geojson_url):
        """Handle GeoJSON URL download"""
        import requests
        from io import BytesIO
        from django.core.files.uploadedfile import InMemoryUploadedFile
        import sys
        import json
        
        # Validate URL format
        if not geojson_url.startswith(('https://')):
            raise ValueError("Invalid GeoJSON URL format")
        
        # Download GeoJSON file with timeout
        file_response = requests.get(geojson_url, timeout=30, allow_redirects=True)
        file_response.raise_for_status()
        file_content = file_response.content
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(file_content) > max_size:
            raise ValueError(f"GeoJSON file too large: {len(file_content)} bytes (max {max_size})")
        
        # Parse GeoJSON to extract features
        try:
            geojson_data = json.loads(file_content)
            # Extract features for frontend display
            geojson_features = geojson_data.get('features', [])
        except json.JSONDecodeError:
            raise ValueError("Invalid GeoJSON format")
        
        # Create Django file object
        file_io = BytesIO(file_content)
        file_name = geojson_url.split("/")[-1].split("?")[0] or "drone_spray.geojson"
        
        # Ensure .geojson or .json extension
        if not file_name.lower().endswith(('.geojson', '.json')):
            file_name += '.geojson'
        
        uploaded_file = InMemoryUploadedFile(
            file_io,
            None,
            file_name,
            file_response.headers.get('Content-Type', 'application/geo+json'),
            sys.getsizeof(file_io),
            None
        )
        
        # Upload using helper
        uploaded_url = helper.image_upload(uploaded_file)
        
        # Calculate area from GeoJSON features
        geometry, calculated_area = self._calculate_area_from_geojson(geojson_features)
        
        return uploaded_url, geojson_features, geometry, calculated_area
    