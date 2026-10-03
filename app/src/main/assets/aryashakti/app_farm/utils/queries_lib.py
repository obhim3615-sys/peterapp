from app_farm.models import organizations,farm,user
from django.db.models import Count
import datetime
from datetime import datetime
from django.conf import settings

def org_counts(from_date="",to_date="",bd_name=""):
    from_query_user=from_query_farm=to_query_user=to_query_farm=bd_query=""
    user_query_params = []
    farm_query_params = []
    
    date_threshold="2023-03-18"
    if(from_date):
        
        if(from_date < date_threshold):
            
            from_query_user=" and timestamp >= %s"
            user_query_params.append(from_date)
        else:
            from_query_user=" and timestamp_first_login >= %s"
            user_query_params.append(from_date)
        
        from_query_farm=" and timestamp >= %s"
        farm_query_params.append(from_date)
    if(to_date):
        if(to_date <=date_threshold):
            from_query_user+=" and timestamp <= %s"
            user_query_params.append(to_date)
        else:
            from_query_user+=" and timestamp_first_login >= %s"
            user_query_params.append(from_date)
        to_query_farm=" and timestamp <= %s"
        farm_query_params.append(to_date)
    if(bd_name):
        bd_query+=" where relationship_manager_name = %s"
    
    user_subquery_filters = [
        "app_farm_user.organization_id = app_farm_organizations.id",
        "firebase_token IS NOT NULL",
    ]
    if from_query_user:
        user_subquery_filters.append(from_query_user.strip().replace("and ", "", 1))
    if to_query_user:
        user_subquery_filters.append(to_query_user.strip().replace("and ", "", 1))

    farm_subquery_filters = [
        "app_farm_farm.org_id_id = app_farm_organizations.id",
    ]
    if from_query_farm:
        farm_subquery_filters.append(from_query_farm.strip().replace("and ", "", 1))
    if to_query_farm:
        farm_subquery_filters.append(to_query_farm.strip().replace("and ", "", 1))

    outer_where = ""
    if bd_query:
        outer_where = " " + bd_query.strip()

    query_value = (
        "SELECT *, "
        "(SELECT COUNT(1) FROM app_farm_user "
        "WHERE " + " AND ".join(user_subquery_filters) + ") AS user_count, "
        "(SELECT COUNT(1) FROM app_farm_farm "
        "WHERE " + " AND ".join(farm_subquery_filters) + ") AS farm_count "
        "FROM app_farm_organizations" + outer_where
    )
    query_params = user_query_params + farm_query_params
    if bd_name:
        query_params.append(bd_name)
    org= organizations.objects.raw(query_value, query_params)
    # print(query_value)
    org_dict={}
    for o in org:
        if o.relationship_manager_name in org_dict.keys():
            org_dict[o.relationship_manager_name]['user_count']=org_dict[o.relationship_manager_name]['user_count']+o.user_count
            org_dict[o.relationship_manager_name]['farm_count']=org_dict[o.relationship_manager_name]['farm_count']+o.farm_count
        else:
             org_dict[o.relationship_manager_name]={
                 'user_count':o.user_count,
                 'farm_count':o.farm_count
             }

    return org_dict


def getAllBD():
    return organizations.objects.values('relationship_manager_name').annotate(total_count=Count('relationship_manager_name'))

def org_details_counts(bd_name,from_date="",to_date=""):
    org = user.objects.select_related('organization').filter(organization__relationship_manager_name=bd_name,timestamp_first_login__isnull=False, firebase_token__isnull=False).all()
    org_dict={}
    for o in org:        
        # print(o.__dict__)
        date_value= o.timestamp_first_login.date()
        if date_value in org_dict.keys():
            org_dict[date_value]['user_count']=org_dict[date_value]['user_count']+1
        else:
             org_dict[date_value]={
                 'user_count':1,
             }

    return org_dict

def org_details_counts_farm(bd_name,from_date="",to_date=""):    
   
    org = farm.objects.select_related('org_id').filter(org_id__relationship_manager_name=bd_name).all()
    org_dict={}
    for o in org:        
        # print(o.__dict__)
        date_value= o.timestamp.date()
        if o.timestamp in org_dict.keys():
            org_dict[date_value]['farm_count']=org_dict[date_value]['farm_count']+1
        else:
             org_dict[date_value]={
                 'farm_count':1
             }

    return org_dict



def getDistanceValidation(lat, long,id=False):
    query_params = [long, lat, settings.DISTANCE_VALUE_FOR_POSTGIS]
    where_clauses = [
        "geometry IS NOT NULL",
        "ST_DistanceSphere(geometry, (SELECT point FROM target_point)) < %s",
    ]
    if id is not False:
        where_clauses.append("id!=%s")
        query_params.append(id)
    query_data = (
        "WITH target_point AS (SELECT ST_MakePoint(%s, %s) AS point) "
        "SELECT id FROM app_farm_farm, target_point "
        "WHERE " + " AND ".join(where_clauses)
    )
    #query_data= "SELECT id,Count(1) as num FROM app_farm_farm WHERE  (ST_DistanceSphere(geometry,ST_MakePoint("+str(long)+", "+str(lat)+")))  < "+str(settings.DISTANCE_VALUE_FOR_POSTGIS)+" "+query_id+" GROUP BY id"
    # print(query_data)
    data= farm.objects.raw(query_data, query_params)
    if (data and len(data)>0):
        return False
    return True