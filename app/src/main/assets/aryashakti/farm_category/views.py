from rest_framework.views import APIView
import requests
import math
import json
import time, random
from threading import Thread  # Import Thread to run cron job in a separate thread
from rest_framework import status
from django.db import transaction
from django.db.models import Q,Sum,F,DecimalField,Count
from django.conf import settings

from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from app_farm.utils.response import req_response
from . import validator,serializer
from app_farm.models import farm,user,crop_master,input_catalogue,organizations
from app_farm.utils import constants,helper
from farm_category.models import *
from libraries.aryaag import AryaAg
from libraries.crop_price import crop_data
from decimal import Decimal
from app_farm.serializers import addinputcatalogueSerializer,FullOrgDetailSerializer,farmaddSerializer,farmlistSerializer
from django.db.models.functions import Coalesce
from core.views import BaseViewWithoutAuthentication
from datetime import datetime
from rest_framework.pagination import PageNumberPagination
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance 
from libraries.decorators import HasValidTokenPermission


# Create your views here.
class GetFarmDetails(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @classmethod
    def get_extra_actions(cls):
        return []
    def post(self, request):
        try:
            if request.data == None:
                return req_response(constants.EMPTY_REQ_BODY, False, 'FCV-GFDPOS-1', status.HTTP_400_BAD_REQUEST)

            body_data = request.data
            if type(body_data) == str:
                body_data = json.loads(body_data)
            validation = validator.GetFarmDetails(data=body_data)

            stress_type = body_data['type'] if body_data.get('type') else 'biotic'

            if not validation.is_valid():
                return req_response(constants.INVALID_BODY, False, 'FCV-GFDPOS-2', status.HTTP_400_BAD_REQUEST, validation.errors)

            farm_details = farm.objects.get(id= body_data['farm_id'])
            farm_details = serializer.FarmsDetailSerializer(farm_details, many=False, context={'stress_type': stress_type}).data
            # print()
            # print(farm_details['local_boundary'])
            if (('local_boundary' not in farm_details.keys()) or ('local_boundary' in farm_details.keys() and farm_details['local_boundary']==None)) and ('stress_data' in farm_details.keys() and farm_details['stress_data'] and farm_details['stress_data'][stress_type+'_category'] == None) :
                return req_response(constants.NO_CONTENT, False, 'FCV-GFDPOS-3', status.HTTP_204_NO_CONTENT)

            # Fetch the heading and advisory data.
            data= []
            if farm_details['stress_data']:
                data = HeadingAndAdvisory.objects.filter(category=farm_details['stress_data'][stress_type+'_category'], language=body_data['language'])
                if data:
                    data = serializer.HeadingAndAdvisorySerializer(data, many=True)
                    if data:
                        data=data.data
            heading=advisory=""

            if data and len(data)>0:
                if 'heading' in data[0].keys():
                    heading=data[0]['heading']
                
                if 'advisory' in data[0].keys():
                    advisory=data[0]['advisory']
            color=""
            if 'stress_data' in farm_details.keys() and farm_details['stress_data'] and 'color' in farm_details['stress_data'].keys():
                color=farm_details['stress_data']['color']

            point = None

            if  farm_details['stress_data'] and farm_details['stress_data'].get('whole'+'_map'):
                point= farm_details['stress_data']['whole'+'_map']
            elif farm_details['stress_data'] and farm_details['stress_data'][stress_type+'_map']:
                point=farm_details['stress_data'][stress_type+'_map']
            result = {
                'color': color,
                'taluka': farm_details['farm_taluka'],
                'district': farm_details['farm_district'],
                'latitude': farm_details['latitude'],
                'longitude': farm_details['longitude'],
                'heading': heading,
                'advisory': advisory,
                # 'points': farm_details['stress_data']['whole'+'_map']
                'points':  point,
                'local_boundary':farm_details['local_boundary']
            }

            # if result['points'] and farm_details['stress_data'].get('whole'+'_map'):
            #     for i, p in enumerate(result['points']):
            #         if i != 0:
            #             p['properties']['fill'] = '#ede793'

            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, result)
        except Exception as e:
            return req_response(constants.ERROR, False, 'FCV-GFDPOS-4', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)
        
def run_categorization_logic(plot_id, season_id, categories, satelite_date, farm_id):
    stress_map = {
        # 'moisture': 'I002',
        'biotic': 'I003',
        # 'abiotic': 'I004',
        # 'micro_nutrient': 'I005',
        'whole': 'I011'
    }
    
    # Fetch the dates
    url = "https://plots.prakshep.com/myplots/datelist?prakshep_id=" + plot_id + '&season_id='+ season_id + '&secret_key=' + settings.PRAKSHEP_KEY
    dates = requests.get(url)
    if dates.status_code == 204:
        return {
            'success': False,
            'err': "Can't fetch the Dates."
        }
    dates = dates.json()

    # Sort the dates
    dates = sorted(dates['data'], key=lambda x: x['date_of_analysis'], reverse=True)

    # # Fetch the latest date
    # date = dates[0]['date_of_analysis']
    # Fetch the latest date
    date = None
    for d in dates:
        if d['index_id'] == stress_map['whole']:
            date = d['date_of_analysis']
            break

    if date == None:
        date = dates[0]['date_of_analysis']

    if False and satelite_date and satelite_date >= date:
        return {
            'success': False,
            'err': 'No new data.'
        }
    
    result = {
        'success': True,
        'date': date
    }

    # Fetch the boundary
    # Fetch the URL for GEO JSON api
    url = "https://plots.prakshep.com/myplots/plotinfo/?prakshep_id=" + plot_id + '&company_id='+ plot_id.split('_')[0] + '&secret_key=' + settings.PRAKSHEP_KEY
    geo_json_url = requests.get(url)
    if geo_json_url.status_code == 204:
        return {
            'success': False,
            'err': "Can't fetch the boundary URL."
        }
    geo_json_url = geo_json_url.json()

    # Fetch the GEO JSON data
    boundary_points = requests.get(geo_json_url['data'][0]['farm_geojson_url'])
    if boundary_points.status_code == 204:
        return {
            'success': False,
            'err': "Can't fetch the Coordinates."
        }
    boundary_points = boundary_points.json()
    result['boundary'] = boundary_points['features']
    
    
    for stress in stress_map:
        # Fetch the URL for GEO JSON api
        url = "https://plots.prakshep.com/myplots/geojsonview?prakshep_id=" + plot_id + '&season_id='+ season_id + '&secret_key=' + settings.PRAKSHEP_KEY + '&index_id=' + stress_map[stress] + '&date_of_analysis=' + date
        geo_json_url = requests.get(url)
        if geo_json_url.status_code == 204:
            print(str(farm_id) + " =--> ", "Can't fetch the URL for - " + stress_map[stress])
            continue
            # return {
            #     'success': False,
            #     'err': "Can't fetch the URL."
            # }
        geo_json_url = geo_json_url.json()

        # Fetch the GEO JSON data
        points = requests.get(geo_json_url['data'][0]['index_geojson_url'])
        if points.status_code == 204:
            print(str(farm_id) + " =--> ", "Can't fetch the Coordinates for - " + stress_map[stress])
            continue
            # return {
            #     'success': False,
            #     'err': "Can't fetch the Coordinates."
            # }
        points = points.json()

        if stress != 'whole':
            # Calculate the total green, red, yellow points
            total_points = {
                'green': 0,
                'yellow': 0,
                'red': 0
            }
            # print(points)
            # for p in points['features'].copy():
            for p in points['features']:
                if p['properties']['fill'] == '#52ce60':
                    for coordinates in p['geometry']['coordinates']:
                        if p['geometry']['type'] == 'MultiPolygon':
                            for temp_coordinates in coordinates:
                                total_points['green'] += len(temp_coordinates)
                        else:
                            total_points['green'] += len(coordinates)

                    # Remove the green points
                    # points['features'].remove(p)
                elif p['properties']['fill'] == '#e30808':
                    for coordinates in p['geometry']['coordinates']:
                        if p['geometry']['type'] == 'MultiPolygon':
                            for temp_coordinates in coordinates:
                                total_points['red'] += len(temp_coordinates)
                        else:
                            total_points['red'] += len(coordinates)
                elif p['properties']['fill'] == '#cec652':
                    for coordinates in p['geometry']['coordinates']:
                        if p['geometry']['type'] == 'MultiPolygon':
                            for temp_coordinates in coordinates:
                                total_points['yellow'] += len(temp_coordinates)
                        else:
                            total_points['yellow'] += len(coordinates)

            # Ratio of points to 100
            temp_point = []
            for color in total_points:
                temp_point.append(round((total_points[color] / (total_points['green']+total_points['red']+total_points['yellow'])) * 100))

            # Calculate the distance and find min distance from all categories.
            min_distance = math.inf
            index = None
            for i, category in enumerate(categories):
                point = [category.healthy,category.stress,category.damaged]
                distance = math.dist(temp_point, point)
                if distance < min_distance:
                    min_distance = distance
                    index = i

            result[stress+'_category'] = categories[index]
        result[stress+'_points'] = points['features']
            # result['whole_map'] = points['features']

    return result

def update_farm_maps(org_id, skip = None, limit = None):
    print("STARTING!!! -- ", str(int(time.time()*1000)), org_id, skip, limit)
    categories = Category.objects.all()
    # farms = farm.objects.exclude(Q(my_plot_id__isnull=True) | Q(season_id__isnull=True)).exclude(Q(my_plot_id__exact='') | Q(season_id__exact='')).order_by('id')
    if skip and limit:
        farms = farm.objects.exclude(Q(my_plot_id__isnull=True) | Q(season_id__isnull=True)).exclude(Q(my_plot_id__exact='') | Q(season_id__exact='')).exclude(id=898).filter(org_id=org_id,is_manual_updated=False).order_by('id')[skip:limit]
    elif limit:
        farms = farm.objects.exclude(Q(my_plot_id__isnull=True) | Q(season_id__isnull=True)).exclude(Q(my_plot_id__exact='') | Q(season_id__exact='')).exclude(id=898).filter(org_id=org_id,is_manual_updated=False).order_by('id')[:limit]
    else:
        farms = farm.objects.exclude(Q(my_plot_id__isnull=True) | Q(season_id__isnull=True)).exclude(Q(my_plot_id__exact='') | Q(season_id__exact='')).exclude(id=898).filter(org_id=org_id,is_manual_updated=False).order_by('id')
    farms_with_date = serializer.FarmsSerializer(farms, many=True).data

    for i,f in enumerate(farms):
        try:
            result = run_categorization_logic(f.my_plot_id, f.season_id, categories, farms_with_date[i]['date'], f.id)

            if result['success']:
                print(str(f.id) + " --> ", 'SUCCESS')
                FarmsCategory.objects.update_or_create(
                    farm = f,
                    defaults={
                        "satelite_date": result['date'],
                        "biotic_map": result.get('biotic_points'),
                        # "abiotic_map": result['abiotic_points'],
                        # "moisture_map": result['moisture_points'],
                        # "micro_nutrient_map": result['micro_nutrient_points'],
                        "biotic_category": result.get('biotic_category'),
                        # "abiotic_category": result['abiotic_category'],
                        # "moisture_category": result['moisture_category']
                        # "micro_nutrient_category": result['micro_nutrient_category'],
                        "boundary": result['boundary'],
                        "whole_map": result.get('whole_points')
                    }
                )
            else:
                print(str(f.id) + " =--> ", result['err'])
        except Exception as e:
            print(str(f.id) + " --> ", e)
    print("ENDED!!! -- ", str(int(time.time()*1000)))

class RunCronJob(BaseViewWithoutAuthentication):
    def run_cron_job(self, request, err_code, req_data):
        # Start a new thread to run the cron job
        cron_thread = Thread(target=update_farm_maps, args=(req_data['org_id'], req_data.get('skip'), req_data.get('limit')))
        cron_thread.start()

        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)

    def post(self, request):
        return self.common_function(request, 'FCV-RCJPOS-', None, self.run_cron_job)


class FarmCategoryScript(APIView):
    def post(self, request):
        try:
            if request.data == None:
                return req_response(constants.EMPTY_REQ_BODY, False, 'FCV-FCSPOS-1', status.HTTP_400_BAD_REQUEST)

            body_data = request.data
            if type(body_data) == str:
                body_data = json.loads(body_data)

            farm_category = FarmsCategory.objects.get(id=body_data['farm_category_id'])
            farms = farm.objects.exclude(Q(my_plot_id__isnull=True)|Q(my_plot_id__exact=''),Q(season_id__isnull=True)|Q(season_id__exact='')).filter(Q(latitude__isnull=True)|Q(latitude=0.0),Q(longitude__isnull=True)|Q(longitude=0.0),is_manual_updated=False).order_by('id')[:body_data['limit']]

            for f in farms:
                f.latitude = random.randint(body_data['lat_start'], body_data['lat_end']) + (random.randint(1, 9999) / 10000) + (random.randint(1, 9999) / 100000000)
                f.longitude = random.randint(body_data['long_start'], body_data['long_end']) + (random.randint(1, 9999) / 10000) + (random.randint(1, 9999) / 100000000)
                # f.my_plot_id = farm_category.farm.my_plot_id
                # f.season_id = farm_category.farm.season_id
                f.is_manual_updated = True
                f.is_location = True

                with transaction.atomic():
                    f.save()
                    # Update or create farm category
                    FarmsCategory.objects.update_or_create(
                        farm = f,
                        defaults={
                            "satelite_date": farm_category.satelite_date,
                            "biotic_map": farm_category.biotic_map,
                            "biotic_category": farm_category.biotic_category,
                            "whole_map": farm_category.whole_map
                        }
                    )
            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)
        except Exception as e:
            return req_response(constants.ERROR, False, 'FCV-FCSPOS-2', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)



def getOrganizationFarms(organization):
    #all_farmers= user.objects.filter(organization=organization,user_role=settings.IDS_FARMER_USER_ROLE).values_list('id', flat=True)
    
    # Filter FarmsCategory objects associated with the specific user and organization
    filtered_categories = FarmsCategory.objects.filter(
        #farm__user_id__in=all_farmers,
        farm__org_id__id=organization.id,
        # Add other conditions as needed
    )

    return filtered_categories

def getCropwithOrganizationFarm(organization,crop_id):
    filtered_categories=getOrganizationFarms(organization)
    filtered_categories=filtered_categories.filter(
            farm__crop_id__id=crop_id,
            # Add other conditions as needed
        )
    return filtered_categories

class GetProjectedFarms(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request,crop_id):
        try:
            crop=crop_master.objects.filter(id=crop_id).get()
        except crop_master.DoesNotExist:
            return req_response("Crop Not Found",False,"FC-GPF-GET-01",status.HTTP_404_NOT_FOUND,None,"No data of crop found")
        

        organization = request.user.organization

        # Filter FarmsCategory objects associated with the specific user and organization        
        filtered_categories=getCropwithOrganizationFarm(organization,crop_id)
       

        # arya_ag= AryaAg()
        # org_dist=organization.district if organization.district else ""
        # mandi_price=arya_ag.get_mandi_price(crop.crop_name,org_dist)
        mandi_price=None
        # mandi_price=arya_ag.get_mandi_price("Wheat","Baran")
        mandi={}

        
        
        # Calculate the sum of specific columns
        sum_values= filtered_categories.aggregate(Sum('yieldpotential')
                                                  ,Sum('stressmin'),
                                                  Sum('stressmax'),
                                                  Sum('yieldlossmin'),
                                                  Sum('yieldlossmax'),
                                                  Sum('yieldmin'),
                                                  Sum('yieldmax'),
                                                  Sum('productionmin'),
                                                  Sum('productionmax'),
                                                  ) 
        avgprice=0
        if mandi_price and mandi_price['data']['total']>0:
            for pr in mandi_price['data']['cards']:
                if pr['max_price'] !=0 or pr['min_price']:
                    avgprice=Decimal((pr['max_price']+pr['min_price'])/2)
                    break
            

        if crop.crop_name in crop_data.keys() and avgprice==0:
            mandi=crop_data[crop.crop_name]
            # Get the current date
            current_date = datetime.now()

            # Get the month number
            current_month = current_date.month
            if current_month>4:
                quarter=int(current_month/4)
            else:
                quarter=1
                
            if quarter==1:
                avgprice=Decimal(mandi['Q1'])
            elif quarter==2:
                avgprice=Decimal(mandi['Q2'])
            elif quarter==3:
                avgprice=Decimal(mandi['Q3'])
            elif quarter==4:
                avgprice=Decimal(mandi['Q4'])

            
        projected_ideal_earning=0
        
        max_yield=Decimal(sum_values['yieldmax__sum']) if sum_values['yieldmax__sum'] else 0
            
        min_yield=Decimal(sum_values['yieldmin__sum']) if sum_values['yieldmin__sum'] else 0
            
        if max_yield:
            projected_ideal_earning=max_yield*avgprice
        
        projected_earning=0
        if min_yield:
            projected_earning=min_yield*avgprice
        data={
            # "yieldpotential":sum_values['yieldpotential__sum'],
            # "stressmin":sum_values['stressmin__sum'],
            # "stressmax":sum_values['stressmax__sum'],
            # "yieldlossmin":sum_values['yieldlossmin__sum'],
            # "yieldlossmax":sum_values['yieldlossmax__sum'],
            # "yieldmin":sum_values['yieldmin__sum'],
            # "yieldmax":sum_values['yieldmax__sum'],
            # "productionmin":sum_values['productionmin__sum'],
            # "productionmax":sum_values['productionmax__sum'],
            "mandi_price":avgprice,
            "projected_earning":projected_earning,
            "projected_ideal_earning":projected_ideal_earning,
            "projected_ideal_yield":max_yield,
            "projected_yield":min_yield,

        }

        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data)

class GetWholeFarm(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]


    def get(self,request,crop_id):
        organization = request.user.organization
        # Filter FarmsCategory objects associated with the specific user and organization
        filtered_categories=getCropwithOrganizationFarm(organization,crop_id)

        # Extract the first element from the 'whole_map' field
        first_whole_map = filtered_categories.filter(boundary__isnull=False).values(whole_map__0=F('boundary'))
        if organization.id==1:
            first_whole_map =first_whole_map.filter(farm__latitude__gt=18.0, farm__latitude__lt=18.2,farm__longitude__gt=74.0,farm__longitude__lt=75.5)
        first_whole_map =first_whole_map.annotate(farm_name=F('farm__name'),farm_state=F('farm__farm_state'),farm_lat=F('farm__latitude'),farm_long=F('farm__longitude'),farm_id=F('farm_id'),user_id=F('farm__user__id'),user_profile_img=F('farm__user__user_profile_img'),user_name=F('farm__user__full_name'),otp_verified=F('farm__user__otp_verfied'),mobile_number=F('farm__user__mobile_number'),crop_name=F('farm__crop_id__crop_name'))[:70]
        docs=[]
        for i,obj in enumerate(first_whole_map):
            docs = list(user.objects.filter(id=obj['user_id']).get().document_user.filter(status=1).values_list('type', flat=True))
            if obj['otp_verified']:
                docs.append('otp_verified')

            first_whole_map[i]['verified-docs']=docs
        data={}
        if first_whole_map:

            lat1=first_whole_map[0]['farm_lat']
            long1=first_whole_map[0]['farm_long']
            lat2=first_whole_map[len(first_whole_map)-1]['farm_lat']
            long2=first_whole_map[len(first_whole_map)-1]['farm_long']
            if lat1 and long1 and lat2 and long2:
                distance= helper.haversine(lat1,long1,lat2,long2)            
                data["distance"]=distance

        data["mapdata"]=first_whole_map
        
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data)




class GetWholeFarmPrithviPro(APIView):
    # permission_classes = [HasValidTokenPermission]

    def post(self,request):
        data = request.data
        org_id =data.get('org_id')
        crop_id =data.get('crop_id')
        try:
            organization=organizations.objects.filter(id=org_id).get()
        except organizations.DoesNotExist:
            return req_response("Organization not found.",False,"GWFPP-POST-01",status.HTTP_404_NOT_FOUND)
        # Filter FarmsCategory objects associated with the specific user and organization
        filtered_categories=getCropwithOrganizationFarm(organization,crop_id)

        # Extract the first element from the 'whole_map' field
        first_whole_map = filtered_categories.filter(boundary__isnull=False).values(whole_map__0=F('boundary'))
        if organization.id==1:
            first_whole_map =first_whole_map.filter(farm__latitude__gt=18.0, farm__latitude__lt=18.2,farm__longitude__gt=74.0,farm__longitude__lt=75.5)
        first_whole_map =first_whole_map.annotate(farm_name=F('farm__name'),farm_state=F('farm__farm_state'),farm_lat=F('farm__latitude'),farm_long=F('farm__longitude'),farm_id=F('farm_id'),user_id=F('farm__user__id'),user_profile_img=F('farm__user__user_profile_img'),user_name=F('farm__user__full_name'),otp_verified=F('farm__user__otp_verfied'),mobile_number=F('farm__user__mobile_number'),crop_name=F('farm__crop_id__crop_name'))[:70]
        docs=[]
        for i,obj in enumerate(first_whole_map):
            docs = list(user.objects.filter(id=obj['user_id']).get().document_user.filter(status=1).values_list('type', flat=True))
            if obj['otp_verified']:
                docs.append('otp_verified')

            first_whole_map[i]['verified-docs']=docs
        data={}
        if first_whole_map:

            lat1=first_whole_map[0]['farm_lat']
            long1=first_whole_map[0]['farm_long']
            lat2=first_whole_map[len(first_whole_map)-1]['farm_lat']
            long2=first_whole_map[len(first_whole_map)-1]['farm_long']
            if lat1 and long1 and lat2 and long2:
                distance= helper.haversine(lat1,long1,lat2,long2)            
                data["distance"]=distance

        data["mapdata"]=first_whole_map
        data["organization"]=FullOrgDetailSerializer(organization,many=False).data
        
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data)




class GetFarmListWithOrganization(APIView,PageNumberPagination):
    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=farm


    def post(self,request):
        data = request.data
        org_id= data.get('org_id')

        farm.objects.filter(org_id=org_id).all()

    
    def get_queryset(self,org_id):
        queryset= farm.objects.filter(org_id=org_id) 
        
        return queryset

    def get(self,request,org_id):
        data= request.GET

        queryset = self.get_queryset(data.get('org_id'))      
        page =  self.paginate_queryset(queryset,request)

        farms=None
        if page:          
            farms=farmlistSerializer(page,many=True).data
            farms=self.get_paginated_response(farms).data
        
        return req_response("Data found",True,"",status.HTTP_200_OK,farms)



from recordActivity.models import FarmReport
from recordActivity.serializers import FarmReportSerializer
class GetSingleFarmData(APIView):
    def post(self,request,farm_id):
        try:
            farm_data=farm.objects.filter(id=farm_id).get()
            farm_report=FarmReport.objects.filter(farm_id=farm_id).order_by('-id').get()
        except farm.DoesNotExist :
            return req_response("Farm data not found",False,"GSFD-POST-02",status.HTTP_404_NOT_FOUND)
        except FarmReport.DoesNotExist:
            return req_response("Farm report not found",False,"GSFD-POST-01",status.HTTP_404_NOT_FOUND)

        farmdata= farmaddSerializer(farm_data).data
        try:
            geojson_data=FarmsCategory.objects.filter(farm_id=farm_id).first()
        except FarmsCategory.DoesNotExist:
            return req_response("Farm map not found",False,"GSFD-POST-03",status.HTTP_404_NOT_FOUND)
            
        farmreport= FarmReportSerializer(farm_report).data
        data={
            "farmdata":farmdata,
            "farmreport":farmreport,
            "geojson_data":geojson_data.boundary[0]
        }
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data)


class GetOrganizationCrop(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
        filtered_categories=getOrganizationFarms(request.user.organization)

        # Extract unique crop names
        unique_crops = filtered_categories.filter(id__gt=0,farm__crop_id__id__isnull=False).annotate(
            crop_id=F('farm__crop_id__id'),
            crop_name=F('farm__crop_id__crop_name'),
            unselected_icon_url=F('farm__crop_id__crop_unselected_icon_url'),
            selected_icon_url=F('farm__crop_id__crop_selected_icon_url'),
        ).values('crop_name', 'crop_id','unselected_icon_url','selected_icon_url').annotate(
            relation_count=Count('id')
        ).order_by('-relation_count', 'farm__crop_id__id').distinct()
        
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, list(unique_crops))


def getAbioticserialized(data):
    data=addinputcatalogueSerializer(data,many=True)
    if data:
        return data.data
    
    return []
class GetTotalStressedFarm(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
        organization=request.user.organization
        total_biotic_stressed=farm.objects.filter(org_id=organization,biotic_stress__gt=constants.STRESS_THRESHOLD).count()
        total_biotic_stressed_area_hect = farm.objects.filter(
            org_id=organization,
            biotic_stress__gt=constants.STRESS_THRESHOLD,
            area_unit="Hectare",
            total_area__isnull=False
        ).aggregate(total_area_sum_hect=Coalesce(
                Sum('total_area', output_field=DecimalField()), 
                Decimal(0)
            )
        )['total_area_sum_hect']

        total_biotic_stressed_area_acre = farm.objects.filter(
            org_id=organization,
            biotic_stress__gt=constants.STRESS_THRESHOLD,
            area_unit="Acre",
            total_area__isnull=False
        ).aggregate(total_area_sum_acre=Coalesce(
                Sum('total_area', output_field=DecimalField()), 
                Decimal(0)
            )
        )['total_area_sum_acre']

        biotic_products=input_catalogue.objects.filter(product_category__in=constants.BIOTIC_PRODUCT_TYPE).all()
        biotic_products=getAbioticserialized(biotic_products)

        total_abiotic_stressed=farm.objects.filter(org_id=organization,abiotic_stress__gt=constants.STRESS_THRESHOLD).count()
        abiotic_products=input_catalogue.objects.filter(product_category__in=constants.ABIOTIC_PRODUCT_TYPE).all()

        total_abiotic_stressed_area_hect = farm.objects.filter(
            org_id=organization,
            abiotic_stress__gt=constants.STRESS_THRESHOLD,
            area_unit="Hectare",
            total_area__isnull=False
        ).aggregate(total_area_sum_hect=Coalesce(
                Sum('total_area', output_field=DecimalField()), 
                Decimal(0)
            )
        )['total_area_sum_hect']

        total_abiotic_stressed_area_acre = farm.objects.filter(
            org_id=organization,
            abiotic_stress__gt=constants.STRESS_THRESHOLD,
            area_unit="Acre",
            total_area__isnull=False
        ).aggregate(total_area_sum_hect=Coalesce(
                Sum('total_area', output_field=DecimalField()), 
                Decimal(0)
            )
        )['total_area_sum_hect']

        abiotic_products=getAbioticserialized(abiotic_products)

        total_nutrient_stressed=farm.objects.filter(org_id=organization,nutrient_stress__gt=constants.STRESS_THRESHOLD).count()
        nutrient_products=input_catalogue.objects.filter(product_category__in=constants.NUTRIENT_PRODUCT_TYPE).all()

        total_nutrient_stressed_area_hect = farm.objects.filter(
            org_id=organization,
            nutrient_stress__gt=constants.STRESS_THRESHOLD,
            area_unit="Hectare",
            total_area__isnull=False
        ).aggregate(total_area_sum_hect=Coalesce(
                Sum('total_area', output_field=DecimalField()), 
                Decimal(0)
            )
        )['total_area_sum_hect']

        total_nutrient_stressed_area_acre = farm.objects.filter(
            org_id=organization,
            nutrient_stress__gt=constants.STRESS_THRESHOLD,
            area_unit="Acre",
            total_area__isnull=False
        ).aggregate(total_area_sum_hect=Coalesce(
                Sum('total_area', output_field=DecimalField()), 
                Decimal(0)
            )
        )['total_area_sum_hect']

        nutrient_products=getAbioticserialized(nutrient_products)

        #2.47 is for converting hect to acre
        total_biotic_stressed_area_acre=total_biotic_stressed_area_acre+(Decimal(total_biotic_stressed_area_hect) * Decimal(2.47))
        total_abiotic_stressed_area_acre=total_abiotic_stressed_area_acre+(Decimal(total_abiotic_stressed_area_hect) * Decimal(2.47))
        total_nutrient_stressed_area_acre=total_nutrient_stressed_area_acre+(Decimal(total_nutrient_stressed_area_hect) * Decimal(2.47))
        data={
            "total_acre":total_biotic_stressed_area_acre+total_abiotic_stressed_area_acre+total_nutrient_stressed_area_acre,
            "total_stress":total_biotic_stressed+total_abiotic_stressed+total_nutrient_stressed,
            "total_biotic_stressed":total_biotic_stressed,
            "total_biotic_stressed_area_acre":total_biotic_stressed_area_acre,
            "biotic_products":biotic_products,
            "total_abiotic_stressed":total_abiotic_stressed,
            "abiotic_products":abiotic_products,
            "total_abiotic_stressed_area_acre":total_abiotic_stressed_area_acre,
            "total_nutrient_stressed":total_nutrient_stressed,
            "nutrient_products":nutrient_products,
            "total_nutrient_stressed_area_acre":total_nutrient_stressed_area_acre
        }

        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data)
    
class FarmDetails(BaseViewWithoutAuthentication):
    def farm_details(self, request, err_code, req_data):
        # if not helper.verify_secret_key(req_data['secret_key']):
        #     return req_response(constants.INVALID_KEY, False, err_code+'3', status.HTTP_400_BAD_REQUEST)\
            
        print("data from prakshep")
        print(req_data)

        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)

    def post(self, request):
        return self.common_function(request, 'FCV-FDPOS-', None, self.farm_details)
    


class GetNearestWarehouse(APIView,PageNumberPagination):
    
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=Warehouse


    def get_queryset(self,latitude=None,longitude=None):
        # print(latitude,longitude)
        queryset= Warehouse.objects.all()  
        if latitude and longitude:
            reference_point = Point(float(longitude), float(latitude), srid=4326)
            #loaction name filter pincode
            queryset= queryset.filter(
                latitude__isnull=False,
                longitude__isnull=False,
                geometry__isnull=False
            ).annotate(
                distance=Distance('geometry', reference_point)
            ).order_by('distance')
        
        return queryset

    def get(self,request):
        data= request.GET

        queryset = self.get_queryset(data.get('latitude'),data.get('longitude'))      
        page =  self.paginate_queryset(queryset,request)

        warehouse=None
        if page:          
            warehouse=serializer.WarehouseSerializer(page,many=True).data
            warehouse=self.get_paginated_response(warehouse).data
        
        return req_response("Data found",True,"",status.HTTP_200_OK,warehouse)

class GetWarehouseClusterByID(APIView, PageNumberPagination):
    permission_classes = [HasValidTokenPermission]

    def get(self,request,warehouse_id):
        try:
            warehouse = WarehouseIndiaClusture.objects.filter(ogc_fid=warehouse_id).get()
            if warehouse is not None:
                warehouse = serializer.WarehouseIndiaClustureSerializer(warehouse, many=False).data
                return req_response("Data found",True,"",status.HTTP_200_OK,warehouse)

            return req_response("Not found",False,"FC-GWHBI-GET-02",status.HTTP_404_NOT_FOUND)

        except WarehouseIndiaClusture.DoesNotExist:
            return req_response("Not found",False,"FC-GWHBI-GET-01",status.HTTP_404_NOT_FOUND)


class GetWarehouseClusterList(APIView, PageNumberPagination):
    permission_classes = [HasValidTokenPermission]


    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model = WarehouseIndiaClusture

    def get_queryset(self, point):
        # Check if there are any warehouses that contain the point
        queryset = WarehouseIndiaClusture.objects.filter(wkb_geometry__contains=point)

        
        if point and not queryset.exists():
            # If no warehouses contain the point, find the nearest one
            queryset = WarehouseIndiaClusture.objects.annotate(distance=Distance('wkb_geometry', point)).order_by('distance')

        return queryset

    def post(self, request):
        data= request.data
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        pincode = data.get('pincode')

        if (not latitude or not longitude) and not pincode:
            return req_response("Latitude and Longitude or pincode are required parameters",False,"GWL-GET-01",status.HTTP_400_BAD_REQUEST)

        if latitude and longitude:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except ValueError:
                return req_response("Invalid latitude or longitude format.",False,"GWL-GET-02",status.HTTP_400_BAD_REQUEST)

            
            
        else:
            try:
                location= WarehousePincodeLocation.objects.filter(pin_code=pincode).get()
            except WarehousePincodeLocation.DoesNotExist:
                return req_response("Pincode not found",False,"GWL-GET-03",status.HTTP_404_NOT_FOUND)
            latitude=float(location.latitude)
            longitude=float(location.longitude)

        point = Point(longitude, latitude)
        queryset = self.get_queryset(point)
        page = self.paginate_queryset(queryset, request)

        warehouses = None
        if page is not None:
            warehouses = serializer.WarehouseIndiaClustureSerializer(page, many=True).data
            warehouses = self.get_paginated_response(warehouses).data

        return req_response("Data found",True,"",status.HTTP_200_OK,warehouses)
        

class GetBuyersSellers(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=BuyerSellerDetail


    def get_queryset(self,type=None,latitude=None,longitude=None):

        queryset= BuyerSellerDetail.objects.all()  
        if type:
            queryset= queryset.filter(type_user=type)
        

        if latitude and longitude:
            reference_point = Point(float(longitude), float(latitude), srid=4326)
            queryset= queryset.filter(
                latitude__isnull=False,
                longitude__isnull=False,
                geometry__isnull=False
            ).annotate(
                distance=Distance('geometry', reference_point)
            ).order_by('distance')
        
        return queryset


    def get(self,request):
        data= request.GET

        queryset = self.get_queryset(data.get('type'),data.get('latitude'),data.get('longitude'))      
        page =  self.paginate_queryset(queryset,request)

        buyer_seller=None
        if page:          
            buyer_seller=serializer.BuyerSellerDetailSerializer(page,many=True).data
            buyer_seller=self.get_paginated_response(buyer_seller).data
        
        return req_response("Data found",True,"",status.HTTP_200_OK,buyer_seller)
    

class AddInterestUser(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request):
        data = request.data 
        if 'remarks' not in data:
            return req_response("Please provide the remarks field",False,"",status.HTTP_400_BAD_REQUEST)

        interest= UserInterest.objects.create(user=request.user, remarks=data['remarks'],type_interest=data.get('type_interest'),latitude=data.get('latitude'),longitude=data.get('longitude'))   
        if not interest:
            return req_response("Something is wrong",False,"",status.HTTP_500_INTERNAL_SERVER_ERROR)

        interest= serializer.UserInterestSerializer(interest,many=False).data
        return req_response("Interest Added",True,"",status.HTTP_201_CREATED,interest)


class CreateManualFarmBoundary(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request,farm_id):
        data = request.data 
        
        try:
            farm_data= farm.objects.filter(id=farm_id).get()
        except farm.DoesNotExist:
            return req_response("Farm does not exist ",False,"",status.HTTP_400_BAD_REQUEST)

        if farm_data.org_id != request.user.organization:
            return req_response("Farm is not in your organization ",False,"",status.HTTP_400_BAD_REQUEST)

        try:
            farm_category=FarmsCategory.objects.filter(farm=farm_data).get()
            return req_response("Farm boundary already exist ",False,"",status.HTTP_400_BAD_REQUEST)

        except FarmsCategory.DoesNotExist:

            category=FarmsCategory.objects.create(farm=farm_data, boundary=data['boundary'])

            return req_response("Farm boundary added",True,"",status.HTTP_201_CREATED,serializer.AbioticFarmCategoryDetailSerializer(category).data)

  #abhishek             
# class GetWarehouseList(APIView, PageNumberPagination):
    
#     authentication_classes = []
#     permission_classes = []

#     # Number of items per page by default
#     page_size = 25
#     # Max number of items per page
#     max_page_size = 100
#     model = Warehouse

#     def get_queryset(self):
#         # Get the list of all warehouses, you can customize this further if necessary
#         return Warehouse.objects.all()

#     def get(self, request):
#         # Get query parameters if any
#         data = request.GET
        
#         # Get the queryset
#         queryset = self.get_queryset()
        
#         # Paginate the queryset
#         page = self.paginate_queryset(queryset, request)
        
#         warehouse = None
        
#         # If the page has data, serialize it and return the paginated response
#         if page:
#             # Serialize the data
#             warehouse = serializer.WarehouseSimpleSerializer(page, many=True).data
            
#             # Return the paginated response directly
#             return self.get_paginated_response(warehouse)

#         # If no data found, return a response
#         return req_response("No data found", False, "", status.HTTP_404_NOT_FOUND, warehouse)

class GetWarehouseList(APIView):

    authentication_classes = []
    permission_classes = []

    def get_queryset(self):
        return Warehouse.objects.all()

    def get(self, request):
        queryset = self.get_queryset()

        if queryset.exists():
            warehouse = serializer.WarehouseSimpleSerializer(queryset, many=True).data
            return req_response("Data found", True, "", status.HTTP_200_OK, warehouse)

        return req_response("No data found", False, "", status.HTTP_404_NOT_FOUND, [])
    


class ClusterSearchView(APIView):
    """
    Check if given lat/lon lies inside any cluster (sixty or ten)
    Example: /api/clusters/search/?type=sixty&lat=12.97&lon=77.59
    """

    permission_classes = [HasValidTokenPermission]

    def post(self, request):
        
        form_data=request.data
        cluster_type = form_data.get("type")
        lat = form_data.get("lat")
        lon = form_data.get("lon")
        pincode = form_data.get('pincode')

        if (not lat or not lon) and not pincode:
            return req_response("Latitude and Longitude or pincode are required parameters",False,"GWL-GET-01",status.HTTP_400_BAD_REQUEST)


        if lat and lon:
            try:
                lat = float(lat)
                lon = float(lon)
            except ValueError:
                return req_response("Invalid latitude or longitude format.",False,"GWL-GET-02",status.HTTP_400_BAD_REQUEST)

            
            
        else:
            try:
                location= WarehousePincodeLocation.objects.filter(pin_code=pincode).get()
            except WarehousePincodeLocation.DoesNotExist:
                return req_response("Pincode not found",False,"GWL-GET-03",status.HTTP_404_NOT_FOUND)
            lat=float(location.latitude)
            lon=float(location.longitude)

        data =[]
        point = Point(lon, lat, srid=4326)
        return_response={}
        # if found
        # 10 km radius.  --- terchary

        # elif
        # 60 km radius --secondary

        # else
        # primary

        cluster = TenKmCluster.objects
        if point:
            cluster=cluster.filter(wkb_geometry__contains=point)
            
        if cluster:
            data= serializer.TenKmClusterSerializer(cluster,many=True).data
            return_response={
                "market":"Tertiary",
                "data":data
            }
        else:
            cluster = SixtyKmCluster.objects
            if point:
                cluster=cluster.filter(wkb_geometry__contains=point)
                if cluster:
                    data= serializer.SixtyKmClusterSerializer(cluster,many=True).data
                    return_response={
                        "market":"Secondary",
                        "data":data
                    }
        # print(type(len(data)))
        if len(data)== 0:
            return_response={
                "market":"Primary",
                "data":None
            }
        

        return req_response("Data found", True, "", status.HTTP_200_OK, return_response)






class GetLocations(APIView, PageNumberPagination):
 

    # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model = Location

    def get_queryset(self, location_type=None, parent_id=None):
        queryset = Location.objects.all()

        if location_type:
            queryset = queryset.filter(type=location_type)

        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)

        return queryset.order_by("id")

    def get(self, request):
        data = request.GET
        location_type = data.get("type")  # COUNTRY, STATE, DISTRICT, PINCODE, LOCATION
        parent_id = data.get("parent_id")  # optional for filtering children

        queryset = self.get_queryset(location_type, parent_id)
        page = self.paginate_queryset(queryset, request)

        response_data = None
        if page:
            response_data = serializer.LocationSerializer(page, many=True).data
            response_data = self.get_paginated_response(response_data).data

        return req_response("Data found", True, "", 200, response_data)