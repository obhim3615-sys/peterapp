from django.shortcuts import render
from rest_framework.views import APIView
from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.response import Response
from app_farm.models import farm,language_master
from .models import *
from app_farm.utils import response as res
from rest_framework import status
from .serializers import *
from datetime import datetime
from libraries.neoperk_soil import NeoPerkAPI
import requests
from app_farm.utils import helper
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
# Create your views here.



class GetPopActivity(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request,farmid):
        try:
            farm_data=farm.objects.filter(id=farmid).get()
        except Exception as e:
            return res.req_response("Farm not found",False,"POP-GPA-GET-01",status.HTTP_404_NOT_FOUND)
        
        sowing_date=farm_data.sowing_date

       
        if sowing_date:
            last_suggestion=next_suggestion=[]

            # Calculate the difference in days between sowing_date and today
            today = datetime.now().date()
            difference_in_days = (today - sowing_date.date()).days

            try:
                check_last_pop_date=ActivityPOP.objects.filter(crop_id=farm_data.crop_id_id).last()
            except ActivityPOP.DoesNotExist:
                check_last_pop_date=None
            is_pop_completed=False
            if check_last_pop_date and difference_in_days>check_last_pop_date.from_das:
                next_suggestion=last_suggestion=None
                is_pop_completed=True
            else:
                next_suggestion=ActivityPOP.objects.filter(from_das__gt=difference_in_days,crop_id=farm_data.crop_id_id).first()
                last_suggestion=ActivityPOP.objects.filter(from_das__lt=difference_in_days,crop_id=farm_data.crop_id_id).last() 

                

                if last_suggestion:                   
                    last_suggestion=ActivityPOPSerializer(last_suggestion,context={'farm_id': farmid,'sowing_date':sowing_date})
                    if last_suggestion:
                        last_suggestion=last_suggestion.data   
                
                if next_suggestion:
                    next_suggestion=ActivityPOPSerializer(next_suggestion,context={'farm_id': farmid,'sowing_date':sowing_date})
                    if next_suggestion:
                        next_suggestion=next_suggestion.data

            data={
                    "lastsuggestion":last_suggestion,
                    "next_suggestion":next_suggestion,
                    "farmer_id":farm_data.user_id,
                    "farm_id":farmid,
                    "is_pop_completed":is_pop_completed,
                    "message_pop_complete":"Previous Crop harvested. Kindly update the crop and sowing info.",
                    "static_fields":[
                        #{"name":"day_after_sowing","type":"int", "is_required":True },
                        {"name":"date_of_activity","type":"date","is_required":True},
                        {"name":"image","type":"string","is_required":False}
                    ]
                    }
                
            return res.req_response("Data found",True,"",status.HTTP_200_OK,data)
            #return res.req_response("Activity not found",False,"POP-GPA-GET-03",status.HTTP_404_NOT_FOUND)


        return res.req_response("No sowing date found",False,"POP-GPA-GET-02",status.HTTP_400_BAD_REQUEST)
    

from django.db.models import Min
from datetime import timedelta

class ActivityFullPop(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, farmid, varietyid=None):
        try:
            farm_data = farm.objects.only("id", "user_id", "crop_id_id", "sowing_date", "pop_group_id").get(id=farmid)
        except farm.DoesNotExist:
            return res.req_response("Farm not found", False, "POP-GPA-GET-01", status.HTTP_404_NOT_FOUND)

        sowing_date = farm_data.sowing_date
        if not sowing_date:
            return res.req_response("No sowing date found", False, "POP-GPA-GET-02", status.HTTP_400_BAD_REQUEST)

        today = datetime.now().date()
        das_today = (today - sowing_date.date()).days

        if farm_data.pop_group_id:
            pops_qs = ActivityPOP.objects.filter(pop_group_id=farm_data.pop_group_id)
            # get minimum DAS (can be negative)
            
        else:
            pops_qs = ActivityPOP.objects.filter(crop_id=farm_data.crop_id_id)

            if farm_data.crop_variety_id:
                pops_qs.filter(variety_id=farm_data.crop_variety_id_id)

        pops_qs = pops_qs.select_related("activity_records_id", "stage", "sub_stage").order_by("from_das")

        if varietyid:
            pops_qs = pops_qs.filter(variety_id=varietyid)
        
        min_from_das = (
                pops_qs.filter(crop_id=farm_data.crop_id_id).aggregate(min_das=Min("from_das"))
            )["min_das"]

        # calculate actual start date
        if min_from_das is not None:
            start_date = sowing_date.date() + timedelta(days=min_from_das)
        else:
            start_date = sowing_date.date()

        das_qs = (
            DASActivityRecord.objects
            .filter(farm_id=farmid, date_of_activity__gte=start_date)
            .select_related("activity")
            .order_by("date_of_activity")
        )
        # Map: activity_id → list of records
        das_map = {}
        for rec in das_qs:
            das_map.setdefault(rec.activity_id, []).append(rec)

        timeline = []
        counts = {
            "total": 0,
            "completed": 0,
            "pending": 0,
            "missed": 0,
            "upcoming": 0,
        }

        bucket_count=0
        bucket_check={}

        for pop in pops_qs:
            counts["total"] += 1

            bucket = das_map.get(pop.activity_records_id_id, [])
            matched_records = []
            check_i_id=True
            for i in bucket:
                day_of_sowing = i.day_of_sowing if i.day_of_sowing is not None else (i.date_of_activity - sowing_date).days
                if i.id not in bucket_check.keys():
                    bucket_count+=1
                    bucket_check[i.id]=True
                    matched_records.append(i)
                    
                    check_i_id=False
                    break
                else:
                    check_i_id=True
               

            completed_details = []
            for r in matched_records:
                day_of_sowing = r.day_of_sowing if r.day_of_sowing is not None else (r.date_of_activity - sowing_date).days
                completed_details.append({
                    "id": r.id,
                    "date_of_activity": r.date_of_activity,
                    "day_of_sowing": day_of_sowing,
                    "activity_data": r.activity_data,
                    "image_url": r.image_url,
                    "latitude": str(r.latitude),
                    "longitude": str(r.longitude),
                })
            
            
            if matched_records:
                status_flag = "completed"
                counts["completed"] += 1
            else:
                if check_i_id:
                    if das_today < pop.from_das:
                        status_flag = "upcoming"
                        counts["upcoming"] += 1
                    elif pop.from_das <= das_today <= pop.to_das:
                        status_flag = "pending"
                        counts["pending"] += 1
                    else:
                        status_flag = "missed"
                        counts["missed"] += 1

            stage_data = {"id": pop.stage.id, "name": pop.stage.name} if pop.stage else None
            sub_stage_data = {"id": pop.sub_stage.id, "name": pop.sub_stage.name} if pop.sub_stage else None

            activity_name = pop.activity_records_id.name if pop.activity_records_id else None

            timeline.append({
                "id": pop.id,
                "activity_records_id": pop.activity_records_id_id,
                "activity_name": activity_name,
                "from_das": pop.from_das,
                "to_das": pop.to_das,
                "stage": stage_data,
                "sub_stage": sub_stage_data,
                "jsondata": pop.jsondata,
                "is_activity_added": len(matched_records),
                "status": status_flag,
                "completed_details": completed_details,
            })
        
        left = counts["pending"] + counts["missed"] + counts["upcoming"]
        is_pop_completed = (left == 0 and counts["total"] > 0)

        if farm_data.crop_id:
            farm_crop = farm_data.crop_id.crop_name
        else:
            farm_crop=None
        if farm_data.crop_variety_id:
            farm_crop_variety=farm_data.crop_variety_id.crop_variety
        else:
            farm_crop_variety=None

        return res.req_response("Data found", True, "", status.HTTP_200_OK,{
            "timeline": timeline,
            "summary": {
                "total_pop": counts["total"],
                "completed": counts["completed"],
                "left": left,
                "pending": counts["pending"],
                "missed": counts["missed"],
                "upcoming": counts["upcoming"],
            },
            "farmer_id": farm_data.user_id,
             "farmer_name": farm_data.name,
            "crop_name": farm_crop,
            "crop_variety_name": farm_crop_variety,
            "total_area": farm_data.total_area,
            "unit": farm_data.area_unit,
            "farmer_contact": farm_data.farmer_contact,
            "org_name": farm_data.org_id.org_name,
            "farm_id": farmid,
            "date_of_sowing": farm_data.sowing_date.date().isoformat(),
            "today_das": das_today,
            "today_date": today.isoformat(),
            "is_pop_completed": is_pop_completed,
            "message_pop_complete": "Previous Crop harvested. Kindly update the crop and sowing info." if is_pop_completed else "",
            "static_fields": [
                {"name": "date_of_activity", "type": "date", "is_required": True},
                {"name": "image", "type": "string", "is_required": False},
            ],
        })

from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from django.utils import timezone
from libraries.push_notification import FirebaseHelper 


class SendPopNotifications(APIView):

    def get(self, request):
        try:
            today = timezone.now().date()

            eligible_farms = (
                farm.objects
                .filter(
                    org_id__send_pop_notifications=True,
                    sowing_date__isnull=False,
                    user__firebase_token__isnull=False
                )
                .select_related(
                    "org_id", "user", "crop_id", "crop_variety_id"
                )
            )

            if not eligible_farms.exists():
                return res.req_response("No farms found", False, "", status.HTTP_404_NOT_FOUND)

            # Preload POPs
            all_pops = ActivityPOP.objects.select_related(
                "activity_records_id"
            ).order_by("from_das")

            pops_by_crop = defaultdict(list)
            pops_by_group = defaultdict(list)

            for p in all_pops:
                if p.pop_group_id:
                    pops_by_group[p.pop_group_id].append(p)
                else:
                    pops_by_crop[p.crop_id].append(p)

            farms_by_farmer = defaultdict(list)
            for f in eligible_farms:
                farms_by_farmer[f.user_id].append(f)

            firebase_helper = FirebaseHelper(use_adc=True)
            notifications_sent = 0

            def process_farmer(farmer_id, farms):
                nonlocal notifications_sent

                farmer = farms[0].user
                device_token = farmer.firebase_token

                for f in farms:
                    try:
                        sowing_date = f.sowing_date.date()
                        das_today = (today - sowing_date).days

                        if f.pop_group_id:
                            pops = pops_by_group.get(f.pop_group_id, [])
                        else:
                            pops = pops_by_crop.get(f.crop_id_id, [])

                        if f.crop_variety_id:
                            pops = [p for p in pops if p.variety_id == f.crop_variety_id_id]

                        next_pop = next((p for p in pops if p.from_das > das_today), None)

                        if not next_pop:
                            PopNotificationLog.objects.create(
                                farm=f,
                                farmer=farmer,
                                activity=None,
                                organization=f.org_id,
                                status="skipped",
                                message=None,
                                error="No upcoming POP"
                            )
                            continue

                        if PopNotificationLog.objects.filter(
                            farm=f, activity=next_pop, created_at__date=today
                        ).exists():
                            PopNotificationLog.objects.create(
                                farm=f,
                                farmer=farmer,
                                activity=next_pop,
                                organization=f.org_id,
                                status="skipped",
                                message=None,
                                error="Duplicate for today"
                            )
                            continue

                        name_abbr = helper.truncate_text(f.name.split()[0], 10)
                        msg = f"Hi {name_abbr}, next POP activity is '{next_pop.activity_records_id.name}'."

                        result = firebase_helper.send_push_notification(
                            [device_token],
                            "Upcoming POP Activities",
                            msg,
                            "default",
                            {}
                        )

                        success = result.get("success")

                        PopNotificationLog.objects.create(
                            farm=f,
                            farmer=farmer,
                            activity=next_pop,
                            organization=f.org_id,
                            status="success" if success else "failed",
                            message=msg,
                            response=result,
                            error=None if success else str(result)
                        )

                        if success:
                            notifications_sent += 1

                    except Exception as e:
                        PopNotificationLog.objects.create(
                            farm=f,
                            farmer=farmer,
                            activity=None,
                            organization=f.org_id,
                            status="failed",
                            message=None,
                            error=str(e)
                        )

            with ThreadPoolExecutor(max_workers=10) as executor:
                for farmer_id, farms in farms_by_farmer.items():
                    executor.submit(process_farmer, farmer_id, farms)

            return res.req_response(
                f"POP notifications processed for {notifications_sent} farmers.",
                True,
                "",
                status.HTTP_200_OK
            )

        except Exception as e:
            return res.req_response(str(e), False, "POP-NOTIFY-ERR", status.HTTP_500_INTERNAL_SERVER_ERROR)


def add_soil_test_plot(farm_id,user):    
    
    try:
        farm_=farm.objects.filter(id=farm_id).get()
    except farm.DoesNotExist:
        return False, res.req_response("Farm not found.",False,"ASTP-POST-02",status.HTTP_404_NOT_FOUND)

    # Initialize and call NeoPerk API
    try:
        token_obj = farm_.org_id.organization_soil_testing  # NO .get()
        access_token = token_obj.soil_testing_token

    except OrganizationSoilTestingToken.DoesNotExist:
        return False, res.req_response(
            "Soil testing token not found for organization.",
            False,
            "ASTP-POST-03",
            status.HTTP_400_BAD_REQUEST
        )
    farm_data={
        "upcoming_crop_cycle":farm_.crop_id.crop_name,
        "district":farm_.farm_district, 
        "farmer_name":farm_.name,
        "operator_note":farm_.id, 
        "operator_user":user.mobile_number,
        "mobile_number":farm_.farmer_contact,
        "village":farm_.farm_village,
        "farm_area":farm_.total_area,
        "state":farm_.farm_state,
        "country":farm_.farm_country,
        "district":farm_.farm_district
    }

    result={}
    
    api = NeoPerkAPI(access_token)
    result = api.add_soil_test_plot_data(farm_data)

    if "error" in result:
        return False, res.req_response("Request failed",False,"POP-GPA-GET-02",status.HTTP_400_BAD_REQUEST,result)
    
    current_month = datetime.now().month
    
    data = FarmSoilTested.objects.filter(farm_value_id=farm_id,created_at__month__gte=current_month).first()
    if not data:
        data = FarmSoilTested.objects.create(farm_value=farm_,sample_id=result['sample_id'],project_id=result['project_id'])
    return True, FarmSoilTestedSerializer(data).data

from django.utils.dateparse import parse_datetime, parse_date
from django.shortcuts import get_object_or_404

class AddPopShareLog(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            data = request.data

            required_fields = [
                "farm_id",
                "user_id",
                "pop_id",
                # "crop_id",
                # "variety_id",
                # "activity_id",
            ]

            # --- Validate presence ---
            missing = [f for f in required_fields if not data.get(f)]
            if missing:
                return res.req_response(
                    f"Missing fields: {', '.join(missing)}",
                    False,
                    "POP-SHARE-001",
                    status.HTTP_400_BAD_REQUEST
                )

            # --- Parse IDs safely ---
            try:
                farm_id = int(data["farm_id"])
                user_id = int(data["user_id"])
                pop_id = int(data["pop_id"])
                # crop_id = int(data["crop_id"])
                # variety_id = int(data["variety_id"])
                # activity_id= int(data["activity_id"])
            except (ValueError, TypeError):
                return res.req_response(
                    "All IDs must be integers.",
                    False,
                    "POP-SHARE-002",
                    status.HTTP_400_BAD_REQUEST
                )

            # --- Validate FK existence ---
            farm_obj = get_object_or_404(farm, id=farm_id)
            user_obj = get_object_or_404(user, id=user_id)
            pop_obj = get_object_or_404(ActivityPOP, id=pop_id)
            

            # --- Optional sowing date ---
            sowing = None
            if data.get("sowing_date"):
                sowing = parse_datetime(data["sowing_date"]) or parse_date(data["sowing_date"])
                if not sowing:
                    return res.req_response(
                        "Invalid sowing_date format. Use ISO format.",
                        False,
                        "POP-SHARE-003",
                        status.HTTP_400_BAD_REQUEST
                    )

            # --- Create log ---
            PopShareLog.objects.create(
                farm=farm_obj,
                user_shared=user_obj,
                pop=pop_obj,
                crop=pop_obj.crop,
                variety=pop_obj.variety,
                activity=pop_obj.activity_records_id,
                sowing=sowing
            )

            return res.req_response(
                "POP share log added successfully.",
                True,
                "",
                status.HTTP_201_CREATED
            )

        except Exception as e:
            return res.req_response(
                str(e),
                False,
                "POP-SHARE-500",
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AddSoilTestPlotAPIView(APIView):
    """
    APIView to receive plot data and forward to NeoPerk API.
    """
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Extract data from request body
        data = request.data
        
        farm_id= data.get('farm_id')
        current_month= datetime.now().month
        
        if not farm_id:
            return res.req_response("Please select a farm.",False,"ASTP-POST-01",status.HTTP_400_BAD_REQUEST)
        count=FarmSoilTested.objects.filter(farm_value_id=farm_id,file_response__isnull=True,created_at__month__gte=current_month).count()

        if count:
            return res.req_response("Your request is already pending",False,"ASTP-POST-01",status.HTTP_400_BAD_REQUEST)
        flag,result= add_soil_test_plot(data.get('farm_id'),request.user)
        
        if not flag:
            return result
        
        return res.req_response("Report sent",True,"",status.HTTP_200_OK,result)


class GetSoilReportsOfFarm(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]


    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=FarmSoilTested    

    def get_queryset(self,farm_id):
        queryset=FarmSoilTested.objects.filter(farm_value_id=farm_id)
        return queryset.order_by('-id')
        
    def get(self,request,farm_id):
        queryset = self.get_queryset(farm_id)   
          
        page =  self.paginate_queryset(queryset,request)

        task=None
        if page:          
            task=FarmSoilTestedSerializer(page,many=True).data
            task=self.get_paginated_response(task).data
        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,task)
    

class NeoPerkWebhookReceiver(APIView):
    def post(self, request):
        data = request.data

        # Check if report URL is provided
        report_url = data.get("soil_test_report_url")
        sample_id = data.get("sample_id")



        if not report_url:
            return Response({
                "message": "Missing 'soil_test_report_url' in data",
                "status": False,
                "error_code": "NEO-WEBHOOK-01"
            }, status=status.HTTP_400_BAD_REQUEST)
        farm_id=data.get('operator_note')
        farm_data=None
        if farm_id and farm_id!='':
            try:
                farm_data = farm.objects.filter(id=farm_id).get()
            except farm.DoesNotExist:
                return res.req_response("Farm not found",False,"NEO-WEBHOOK-04",status.HTTP_404_NOT_FOUND)

        try:
            sample_farm=FarmSoilTested.objects.filter(sample_id=sample_id).get()
        except FarmSoilTested.DoesNotExist:
            if farm_data:
                sample_farm=FarmSoilTested.objects.create(sample_id=data.get('sample_id'),
                                            farm_value=farm_data,
                                            project_id=data.get('project_id'))
            else:
                sample_farm=FarmSoilTested.objects.create(sample_id=data.get('sample_id'),
                                            project_id=data.get('project_id'))
            # return res.req_response("Sample not found",False,"NEO-WEBHOOK-04",status.HTTP_404_NOT_FOUND)

        try:
            # Download the report from the provided URL
            file_response = requests.get(report_url)
            file_response.raise_for_status()
            file_content = file_response.content

            # Prepare a Django InMemoryUploadedFile
            from io import BytesIO
            from django.core.files.uploadedfile import InMemoryUploadedFile
            import sys

            file_io = BytesIO(file_content)
            file_name = report_url.split("/")[-1].split("?")[0] or "soil_report.pdf"
            uploaded_file = InMemoryUploadedFile(
                file_io, None, file_name, file_response.headers.get('Content-Type', 'application/pdf'),
                sys.getsizeof(file_io), None
            )

            # Upload the file using helper
            uploaded_url = helper.image_upload(uploaded_file)
            sample_farm.file_response=uploaded_url
            sample_farm.json_response=data
            if farm_data:
                sample_farm.farm_value=farm_data
            sample_farm.save()
            return res.req_response("File uploaded successfully",True,"",status.HTTP_200_OK,{ "uploaded_url": uploaded_url})
       
        except requests.exceptions.RequestException as e:
            return res.req_response("Failed to download file",False,"NEO-WEBHOOK-02",status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as ex:
            return Response({
                "message": "Unexpected error occurred",
                "status": False,
                "error": str(ex),
                "error_code": "NEO-WEBHOOK-03"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SessionListView(APIView):
    def get(self, request):
        crop_id = request.query_params.get('crop_id')
        if crop_id:
            # Return sessions related to the given crop
            crop_sessions = CropSession.objects.filter(crop_id=crop_id).select_related('session', 'crop')
            sessions = [
                {
                    "session_id": cs.session.id,
                    "session_name": cs.session.name,
                    "from_month": cs.from_month,
                    "to_month": cs.to_month,
                    "crop_id": cs.crop.id,
                    "crop_name": cs.crop.crop_name,
                    "crop_unselected_icon_url": cs.crop.crop_unselected_icon_url,
                    "crop_selected_icon_url": cs.crop.crop_selected_icon_url
                }
                for cs in crop_sessions
            ]
            return Response({"sessions": sessions}, status=status.HTTP_200_OK)
        else:
            # Return all sessions and their related crops
            all_sessions = Session.objects.all()
            data = []
            for session in all_sessions:
                crops = CropSession.objects.filter(session=session).select_related('crop')
                crop_list = [
                    {
                        "crop_id": cs.crop.id,
                        "crop_name": cs.crop.crop_name,  # adjust field name as per your crop_master
                        "from_month": cs.from_month,
                        "to_month": cs.to_month,
                        "crop_unselected_icon_url": cs.crop.crop_unselected_icon_url,
                        "crop_selected_icon_url": cs.crop.crop_selected_icon_url
                    }
                    for cs in crops
                ]
                data.append({
                    "session_id": session.id,
                    "session_name": session.name,
                    "crops": crop_list
                })
            return Response({"sessions": data}, status=status.HTTP_200_OK)

class FarmSessionCheckView(APIView):
    def get(self, request):
        farm_id = request.query_params.get('farm_id')
        # 3. Get current month
        current_month = datetime.now().month
        if not farm_id:
            return Response({"error": "farm_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        # 1. Check if soil is tested
        
        soil_test = FarmSoilTested.objects.filter(farm_value_id=farm_id,created_at__month__gte=current_month).first()
        if not soil_test:
            return Response({"soil_tested": False, "message": "Soil not tested for this farm."}, status=status.HTTP_200_OK)
        # 2. Get crop_id from farm
        try:
            farm_obj = farm.objects.get(id=farm_id)
            crop_id = farm_obj.crop_id_id
            crop_obj = farm_obj.crop_id
        except farm.DoesNotExist:
            return Response({"error": "Farm not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # 4. Find session(s) for this crop and month
        sessions = CropSession.objects.filter(
            crop_id=crop_id,
            from_month__lte=current_month,
            to_month__gte=current_month
        ).select_related('session', 'crop')
        if not sessions.exists():
            return Response({"soil_tested": True, "session": None, "message": "No session found for this crop and month."}, status=status.HTTP_400_BAD_REQUEST)
        session_data = [
            {
                "session_id": cs.session.id,
                "session_name": cs.session.name,
                "crop_id": cs.crop.id,
                "crop_name": cs.crop.crop_name,
                "from_month": cs.from_month,
                "to_month": cs.to_month,
                "crop_unselected_icon_url": cs.crop.crop_unselected_icon_url,
                "crop_selected_icon_url": cs.crop.crop_selected_icon_url
            }
            for cs in sessions
        ]
        return Response({
            "soil_tested": True,
            "crop_id": crop_obj.id if crop_obj else None,
            "crop_name": crop_obj.crop_name if crop_obj else None,
            "crop_unselected_icon_url": crop_obj.crop_unselected_icon_url if crop_obj else None,
            "crop_selected_icon_url": crop_obj.crop_selected_icon_url if crop_obj else None,
            "sessions": session_data
        }, status=status.HTTP_200_OK)
    

# class GetActivityComplianceSummary(APIView, PageNumberPagination):
#     # authentication_classes = [CustomTokenAuthentication]
#     # permission_classes = [IsAuthenticated]

#     page_size = 25
#     max_page_size = 100

#     def get_queryset(self, org_id, listing_id):
#         # 1. Get farms linked to this org + listing
#         farms = FarmListing.objects.filter(
#             listing_id=listing_id, 
#             farm__org_id=org_id
#         ).select_related("farm")

#         return farms

#     def get(self, request, org_id, listing_id):
#         farms = self.get_queryset(org_id, listing_id)

#         # 2. Get all POP activities for this listing
#         pops = ActivityPOP.objects.filter(
#             pop_group__listingpop__listing_id=listing_id
#         ).select_related("activity_records_id")

#         response_data = []
#         for farm_link in farms:
#             farm = farm_link.farm
#             farm_row = {"farm_id": farm.id, "farm_name": farm.name, "activities": []}

#             for pop in pops:
#                 activity = pop.activity_records_id
#                 planned_from, planned_to = pop.from_das, pop.to_das

#                 # check if farmer submitted this activity
#                 das = DASActivityRecord.objects.filter(
#                     farm=farm, activity=activity
#                 ).first()

#                 if das:
#                     if das.day_of_sowing >= planned_from and das.day_of_sowing <= planned_to:
#                         status_flag = "done_on_time"   # ✅ green
#                     else:
#                         status_flag = "done_late"      # 🟡 yellow
#                 else:
#                     status_flag = "not_done"          # 🔴 red

#                 farm_row["activities"].append({
#                     "activity_id": activity.id,
#                     "activity_name": activity.name,
#                     "status": status_flag
#                 })

#             response_data.append(farm_row)

#         page = self.paginate_queryset(response_data, request)
#         if page:
#             task = self.get_paginated_response(page).data
#         else:
#             task = response_data

#         return res.req_response("Activity compliance summary found", True, "", status.HTTP_200_OK, task)



class ActivityPOPFromPOPGroup(APIView):
    permission_classes = [AllowAny]
    def get(self,request,pop_group_id):
        try:
            activity_pop=ActivityPOP.objects.filter(pop_group_id=pop_group_id).all()
        except ActivityPOP.DoesNotExist:
            return res.req_response("Activity Pop group not found ",False,"APFP_GET-01",status.HTTP_500_INTERNAL_SERVER_ERROR)
     
        data_activity = ActivityPOPSecondSerializer(activity_pop,many=True).data
    
        return res.req_response("Activity pop found", True, "", status.HTTP_200_OK, data_activity)

class GetActivityComplianceSummary(APIView, PageNumberPagination):
    # authentication_classes = [CustomTokenAuthentication]
    # permission_classes = [IsAuthenticated]

    page_size = 25
    max_page_size = 100

    def get_queryset(self, org_id, listing_id):
        # 1. Farms linked to this org + listing
        farms = FarmListing.objects.filter(
            listing_id=listing_id,
            farm__org_id=org_id
        ).select_related("farm")
        return farms

    def get(self, request, org_id, listing_id):
        farms = self.get_queryset(org_id, listing_id)

        # 2. POP activities planned for this listing
        pops = ActivityPOP.objects.filter(
            pop_group__listingpop__listing_id=listing_id
        ).select_related("activity_records_id")

        response_data = []

        for farm_link in farms:
            farm = farm_link.farm
            farm_row = {
                "farm_id": farm.id,
                "farm_name": farm.name,
                "activities": []
            }

            for pop in pops:
                activity = pop.activity_records_id
                planned_from, planned_to = pop.from_das, pop.to_das

                das = DASActivityRecord.objects.filter(
                    farm=farm,
                    activity=activity
                ).first()

                if das:
                    if planned_from <= das.day_of_sowing <= planned_to:
                        status_flag = "done_on_time"   # ✅ green
                    else:
                        status_flag = "done_late"      # 🟡 yellow
                else:
                    status_flag = "not_done"          # 🔴 red

                farm_row["activities"].append({
                    "activity_id": activity.id,
                    "activity_name": activity.name,
                    "description": pop.jsondata,
                    "status": status_flag,
                    "planned_from": planned_from,
                    "planned_to": planned_to,
                    "stage": pop.stage.name,
                    "sub_stage": pop.sub_stage.name,
                    "actual_date": das.date_of_activity if das else None,
                })

            response_data.append(farm_row)

        # Pagination
        page = self.paginate_queryset(response_data, request)
        if page:
            task = self.get_paginated_response(page).data
        else:
            task = response_data

        return res.req_response(
            "Activity compliance summary found",
            True,
            "",
            status.HTTP_200_OK,
            task
        )
import uuid
from django.utils import timezone   

class CreatePOPGroupFromPrithviPro(APIView):
    # permission_classes = [CustomTokenAuthentication]   # use your API-token guard
    # permission_classes = [AllowAny]

    def post(self, req):
        try:
            payload = req.data
            

            timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
            unique_id = uuid.uuid4().hex[:6]  # 6-char random suffix
            buyer_id = payload.get('buyer_id')
            crop_id = payload.get('crop_id')
            variety_id = payload.get('variety_id')
            name = f"pp_{payload.get('buyer_id')}_{crop_id}_{variety_id}_{timestamp}_{unique_id}"

            pop = POPGroup.objects.create(
                name=name,
                created_by_buyer_id=buyer_id,
                created_from_prithvipro=True,
                csv_upload_status='created',
                crop_id=crop_id,
                variety_id=variety_id
            )

            # optionally store metadata in a JSONField or a separate table (not required here)

            return res.req_response("Pop group created",True,"",status.HTTP_200_OK,{"pop_group_id": pop.id})
           
        except Exception as e:
            return res.req_response("Pop group creation failed",False,"PM_CPPG_POST-01",status.HTTP_500_INTERNAL_SERVER_ERROR,{"error":  str(e)})




class UploadPOPActivitiesFromPrithviPro(APIView):
    permission_classes = [AllowAny]
    def post(self, req):
        try:
            pop_group_id = req.data.get('pop_group_id')
            crop_id = req.data.get('crop_id')
            variety_id = req.data.get('variety_id')
            activities = req.data.get('activities', [])
            stages = req.data.get('stages', [])
            substages = req.data.get('substages', [])
            extra_json = req.data.get('extra_json', [])

            if not pop_group_id:
                return res.req_response("POP group id is required", False, "", status.HTTP_400_BAD_REQUEST)

            try:
                pop_group = POPGroup.objects.get(id=pop_group_id)
            except POPGroup.DoesNotExist:
                return res.req_response("POPGroup not found", False, "PM_UPAFPP_POST-01", status.HTTP_404_NOT_FOUND)

            if not isinstance(activities, list) or not isinstance(stages, list) or not isinstance(substages, list):
                return res.req_response("Activities, stages, substages must be lists", False, "", status.HTTP_400_BAD_REQUEST)

            created, skipped, errors = 0, 0, []

            # Iterate through all activity indexes
            for idx, activity_id in enumerate(activities, start=1):
                try:
                    stage_id = stages[idx] if idx < len(stages) else None
                    substage_id = substages[idx] if idx < len(substages) else None
                    jsondata = extra_json[idx] if idx < len(extra_json) else {}

                    # Resolve activity record (id or name)
                    activity_rec = None
                    if activity_id:
                        try:
                            activity_rec = ActivityRecord.objects.get(pk=int(activity_id))
                        except Exception:
                            activity_rec = ActivityRecord.objects.filter(name__iexact=str(activity_id)).first()

                    # Create or update ActivityPOP
                    ActivityPOP.objects.update_or_create(
                        pop_group=pop_group,
                        activity_records_id=activity_rec,
                        defaults={
                            'crop_id': crop_id,
                            'variety_id': variety_id,
                            'stage_id': stage_id,
                            'sub_stage_id': substage_id,
                            'jsondata': jsondata if isinstance(jsondata, dict) else {},
                        }
                    )
                    created += 1
                except Exception as exc_row:
                    skipped += 1
                    errors.append({"index": idx, "error": str(exc_row), "activity_id": activity_id})

            pop_group.csv_upload_status = 'completed' if created else 'failed'
            pop_group.save(update_fields=['csv_upload_status'])

            return res.req_response("Upload success", True, "", status.HTTP_200_OK, {
                "pop_group_id": pop_group.id,
                "created_rows": created,
                "skipped_rows": skipped,
                "errors": errors
            })

        except Exception as e:
            if 'pop_group' in locals():
                pop_group.csv_upload_status = 'failed'
                pop_group.save(update_fields=['csv_upload_status'])
            return res.req_response("Pop upload failed", False, "PM_UPAFPP_POST-03", status.HTTP_500_INTERNAL_SERVER_ERROR, {"error": str(e)})

        


class POPGroupsFromPrithviPro(APIView, PageNumberPagination):
    # permission_classes = [CustomTokenAuthentication]
    page_size = 25
    max_page_size = 100

    def get(self, req):
        buyer_id = req.GET.get('buyer_id')
        crop_id = req.GET.get('crop_id')
        variety_id = req.GET.get('variety_id')
        status_get = req.GET.get('status')

        qs = POPGroup.objects.filter(created_from_prithvipro=True)
        if buyer_id:
            qs = qs.filter(created_by_buyer_id=buyer_id)
        if crop_id:
            # you may want to join ActivityPOP or store crop at group level
            qs = qs.filter(crop_id=crop_id).distinct()
        if variety_id:
            qs = qs.filter(variety_id=variety_id).distinct()
        if status_get:
            qs = qs.filter(csv_upload_status=status_get)

        page = self.paginate_queryset(qs, req)
        data = []
        for pop in page or qs:
            data.append({
                "pop_group_id": pop.id,
                "name": pop.name,
                "created_by_buyer_id": pop.created_by_buyer_id,
                "csv_upload_status": pop.csv_upload_status,
                "created_at": pop.created_at,
            })

        if page:
            resp = self.get_paginated_response(data)
            return res.req_response("Found data",True,"",status.HTTP_200_OK,resp.data)
        return res.req_response("data",True,"",status.HTTP_200_OK,data)

from libraries.prithvi_pro import PrithviProLibrary


class PrithviProRequirementAPIView(APIView):
    """
    Fetch requirement list from Prithvi Pro with pagination support
    """
    # permission_classes = [IsAuthenticated]  # enable if auth is required

    def get(self, request):
        crop_id = request.query_params.get("crop_id")
        variety_id = request.query_params.get("variety_id")
        page = request.query_params.get("page")
        token = request.query_params.get("token")  # optional override

        try:
            prithvi = PrithviProLibrary()
            result = prithvi.get_requirement(
                crop_id=crop_id,
                variety_id=variety_id,
                page=page,
                token=token
            )

            if result.get("success") is False:
                # Remote API failed or returned invalid data
                return res.req_response(
                    "Failed to fetch requirements from Prithvi Pro",
                    False,
                    "PM_PPR_REQ-01",
                    status.HTTP_502_BAD_GATEWAY,
                    {"error": result}
                )

            # ✅ SUCCESS
            return res.req_response(
                "Prithvi Pro requirements fetched successfully",
               True,
                "",
                status.HTTP_200_OK,
                result.get('data')
            )

        except Exception as e:
            # ✅ INTERNAL ERROR
            return res.req_response(
                "Unexpected error while fetching requirements",
                False,
                "PM_PPR_REQ-02",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                {"error": str(e)}
            )
        

    
class AcceptRequirementData(APIView):
    permission_classes = [CustomTokenAuthentication]   # use your API-token guard
    permission_classes = [IsAuthenticated]

    def post(self,request):
        # create api to accept requirement 
        # when accepted assign pop group to selected farmers, 
        # save accepted fpo data to prithvi pro requirement table 
        # save farm with listing and Listing with pop 
        data= request.data
        farms_list = data.get('farm_ids')
        requirement_id = data.get('requirement_id')
        farms_list_obj=[]
        if not farms_list:
            return res.req_response(
                "Farm list is required in farm_ids",
                False,
                "ARD-POST-02",
                status.HTTP_400_BAD_REQUEST,
            )
        
        if not requirement_id:
            return res.req_response(
                "requirement_id is required",
                False,
                "ARD-POST-02",
                status.HTTP_400_BAD_REQUEST,
            )
        for i in farms_list:
            try:
                temp_farm = farm.objects.filter(id=i)
            except farm.DoesNotExist:
                return res.req_response(
                f"Farm with id - {i} not found",
                False,
                "ARD-POST-01",
                status.HTTP_400_BAD_REQUEST,
            )
            farms_list_obj.append(temp_farm)
        prithvipro= PrithviProLibrary()
        response = prithvipro.accept_requorement(requirement_id,request.user.organization.id)
        
        if response.get('success'):
            pop_group_id= response.get('data').get('requirement').get('pop_group_id')
            listing_id=response.get('data').get('listing_require').get('id')
            farm.objects.filter(id__in=farms_list).update(pop_group_id=response.get('data').get('requirement').get('pop_group_id'))
            for i in farms_list:
                FarmListing.objects.create(listing_id=listing_id, farm_id=i,pop_group_id=pop_group_id)
            
            return res.req_response("Request Accepted",True,"",status.HTTP_200_OK,response)

        return res.req_response(
                f"Something went wrong",
                False,
                "ARD-POST-01",
                status.HTTP_400_BAD_REQUEST,
                response
            )
from django.db.models import Count, Sum
from rest_framework.permissions import AllowAny

class OrgFarmStatsAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Accepts a JSON body like:
        {
            "org_ids": [1, 2, 3]
        }
        """
        org_ids = request.data.get("org_ids")

        if not org_ids or not isinstance(org_ids, list):
            return Response(
                {"success": False, "message": "org_ids must be a list of organization IDs"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Filter farms by the provided org_ids
        qs = farm.objects.filter(org_id__in=org_ids)

        # Aggregate total farms & total area
        agg = qs.aggregate(
            total_farms=Count('id'),
            total_acres=Sum('total_area')
        )


        return res.req_response(
                "Farm statistics retrieved successfully",
               True,
                "",
                status.HTTP_200_OK,
                 {
                    # "org_ids": org_ids,
                    "total_farms": agg["total_farms"] or 0,
                    "total_acres": float(agg["total_acres"] or 0)
                }
            )





class ListingCountAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Accepts a JSON body like:
        {
            "listing_id": 123
        }
        """
        pop_group_id = request.data.get("pop_group_id")
        org_id = request.data.get("org_id")

        if not pop_group_id or not org_id:
            return Response(
                {"success": False, "message": "pop_group_id and org_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Correct filter using pop_group_id
        qs = farm.objects.filter(pop_group_id=pop_group_id,org_id_id=org_id)

        # Aggregate total farms & total area
        agg = qs.aggregate(
            total_farms=Count('id', distinct=True),
            total_acres=Sum('total_area')
        )

        return Response(
            {
                "success": True,
                "message": "Farm statistics retrieved successfully",
                "data": {
                    "pop_group_id": pop_group_id,
                    "total_farms": agg["total_farms"] or 0,
                    "total_acres": float(agg["total_acres"] or 0)
                }
            },
            status=status.HTTP_200_OK
        )
    
from django.db.models import Q
from django.utils.timezone import localtime
class OwnPOPGroupsFromPrithviPro(APIView, PageNumberPagination):
    page_size = 25
    max_page_size = 100

    def get(self, req,buyer_id):
        
        crop_id    = req.GET.get("crop_id")
        variety_id = req.GET.get("variety_id")
        search     = req.GET.get("search")

        # ✅ Build Q filters (use pop_group__)
        filters = Q(pop_group__created_from_prithvipro=True) & Q(pop_group__created_by_buyer_id=buyer_id)
        if crop_id:
            filters &= Q(pop_group__crop_id=crop_id)
        if variety_id:
            filters &= Q(pop_group__variety_id=variety_id)
       
        if search:
            filters &= (
                Q(pop_group__name__icontains=search) |
                Q(pop_group__crop__crop_name__icontains=search)
            )

        # ✅ Single JOIN query
        qs = (
            ActivityPOP.objects
            .filter(filters)
            .select_related(
                "pop_group", "crop", "variety", "stage", "sub_stage"
            )
            .values(
                "pop_group__id",
                "pop_group__name",
                "pop_group__created_by_buyer_id",
                "pop_group__csv_upload_status",
                "pop_group__created_at",
                "pop_group__crop__crop_name",
                "pop_group__variety__crop_variety",
                "id",
                "from_das",
                "to_das",
                "crop__crop_name",
                "variety__crop_variety",
                "stage__name",
                "sub_stage__name",
                "jsondata",
                "created_at",
            )
            .order_by("-pop_group__created_at", "pop_group__id")
        )

        # ✅ Pagination
        page = self.paginate_queryset(qs, req)
        rows = page or qs

        # ✅ Convert to JSON-serializable
        results = []
        for r in rows:
            results.append({
                "pop_group_id": r["pop_group__id"],
                "group_name": r["pop_group__name"],
                "group_crop": r["pop_group__crop__crop_name"],
                "group_variety": r["pop_group__variety__crop_variety"],
                "created_by_buyer_id": r["pop_group__created_by_buyer_id"],
                "csv_upload_status": r["pop_group__csv_upload_status"],
                "group_created_at": localtime(r["pop_group__created_at"]).strftime("%Y-%m-%d %H:%M:%S"),

                # ActivityPOP details
                "activity_id": r["id"],
                "from_das": r["from_das"],
                "to_das": r["to_das"],
                "activity_crop": r["crop__crop_name"],
                "activity_variety": r["variety__crop_variety"],
                "stage": r["stage__name"],
                "sub_stage": r["sub_stage__name"],
                "jsondata": r["jsondata"],
                "activity_created_at": localtime(r["created_at"]).strftime("%Y-%m-%d %H:%M:%S"),
            })

        if page:
            resp = self.get_paginated_response(results)
            return res.req_response("Found data", True, "", status.HTTP_200_OK, resp.data)
        return res.req_response("Found data", True, "", status.HTTP_200_OK, results)
    
from django.core.paginator import Paginator

class StageListCreateAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """List all Stage records (paginated)."""
        stages = Stage.objects.all().order_by('-id')
        paginator = Paginator(stages, request.GET.get('page_size', 25))
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        serializer = StageSerializer(page_obj, many=True)
        return res.req_response(
            "Found data", True, "", status.HTTP_200_OK,
            {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "results": serializer.data
            }
        )

    def post(self, request):
        """Create a new Stage record."""
        serializer = StageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return res.req_response(
                "Stage created successfully", True, "", status.HTTP_201_CREATED,
                serializer.data
            )
        return res.req_response(
            "Validation failed", False, serializer.errors, status.HTTP_400_BAD_REQUEST,
            {}
        )


class SubStageListCreateAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """List all SubStage records (paginated)."""
        substages = SubStage.objects.all().order_by('-id')
        paginator = Paginator(substages, request.GET.get('page_size', 25))
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        serializer = SubStageSerializer(page_obj, many=True)
        return res.req_response(
            "Found data", True, "", status.HTTP_200_OK,
            {
                "count": paginator.count,
                "num_pages": paginator.num_pages,
                "results": serializer.data
            }
        )

    def post(self, request):
        """Create a new SubStage record."""
        serializer = SubStageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return res.req_response(
                "SubStage created successfully", True, "", status.HTTP_201_CREATED,
                serializer.data
            )
        return res.req_response(
            "Validation failed", False, serializer.errors, status.HTTP_400_BAD_REQUEST,
            {}
        )