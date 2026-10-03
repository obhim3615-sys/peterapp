from django.shortcuts import render
from rest_framework.views import APIView
from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from app_farm.utils.mixin.subscription import SubscriptionRequiredMixin
from rest_framework.response import Response
from app_farm.utils import constants,response as res
from rest_framework import status
from .models import *
from .serializers import *
from django.db.models import OuterRef, Subquery
from datetime import date
from django.db.models import Q,Sum,F
from app_farm.utils import helper

# Create your views here.

class GetSubscription(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 
    def get(self,request):

        user= request.user
        userid=request.GET.get('user_id')
        if userid:
            try:
                user=userModel.objects.filter(id=userid).get()
            except userModel.DoesNotExist:
                return res.req_response("",False,"SS-GSGET-02",status.HTTP_400_BAD_REQUEST)
        trial_subscription=[]
        subscription_trial=UserSubscription.objects
        if userid:
            subscription_trial=subscription_trial.filter(user_id=userid).exists()
        else:
            subscription_trial=subscription_trial.filter(user=user).exists()
            
        if not subscription_trial:
            trial_subscription=Subscription.objects.filter(package_type="trial").all()
        subscription= Subscription.objects.filter(status=True,package_type="subscription").all()
        serialized= SubscriptionSerializer(subscription,many=True)

        trial_serializer=SubscriptionSerializer(trial_subscription,many=True)
        if trial_serializer:
            trial_serializer=trial_serializer.data
        if(serialized):
            #serialized.data["trial_package"]=trial_serializer
            return Response({"status_code": status.HTTP_200_OK,"status": True,"trial_package":trial_serializer,"data":serialized.data,"message": ""},status=200)
            #return res.req_response("",True,"",status.HTTP_200_OK ,serialized.data)            
        
        return res.req_response("",False,"SS-GSGET-01",status.HTTP_400_BAD_REQUEST)


class GetServices(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 
    def get(self,request):
        
        service= Service.objects.filter(status=True).all()
        serialized= ServiceSerializer(service,many=True)
        if(serialized):
            return res.req_response("",True,"",status.HTTP_200_OK ,serialized.data)            
        
        return res.req_response("",False,"SS-GSGET-01",status.HTTP_400_BAD_REQUEST)


class GetServicesUser(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 
    def get(self,request): 
        farmer_id=request.GET.get('farmer_id')  
        is_admin=request.user.user_role.role_name == "Admin" 
        if farmer_id: 
            try:
                farmer= userModel.objects.filter(id=farmer_id).get()
            except userModel.DoesNotExist:
                return res.req_response("User Does not exist",False,"SS-GSGET-02",status.HTTP_400_BAD_REQUEST)
                
            if farmer.organization_id != request.user.organization_id:
                return res.req_response("You dont have permission for this user",False,"SS-GSGET-04",status.HTTP_403_FORBIDDEN)
        all_admins=[]
        if is_admin and not farmer_id:
            all_admins=userModel.objects.get_all_admin(request.user.organization_id)
           
        today_date = date.today()
              
        last_service_user_subquery = UserService.objects.filter(user_subscription__validity__gt=today_date).order_by('id')
        if farmer_id:
            last_service_user_subquery=last_service_user_subquery.filter(user=farmer)
        elif is_admin:
            last_service_user_subquery=last_service_user_subquery.filter(user_id__in=all_admins)
        else:
            last_service_user_subquery=last_service_user_subquery.filter(user=request.user)


        service = Service.objects.filter(status=True).all()

        for k,i in enumerate(service):
            last_service_user_subquery_validity=last_service_user_subquery_remaining=last_service_user_subquery_sponsored_by_id=last_service_user_subquery_sponsored_by_full_name=last_service_user_subquery_service_user_type=last_service_user_subquery
            
            #calculating validity for current service
            validity_sum=last_service_user_subquery_validity.filter(
                service_id=i.id,  # Replace your_service_id with the actual service ID
            ).aggregate(validity_sum=Sum('validity'))['validity_sum'] or None
            

            remaining=None
            if validity_sum:
                remaining=0
            # Calculate remaining for the current service
            remaining = last_service_user_subquery_remaining.filter(
                service_id=i.id,  # Replace your_service_id with the actual service ID
            ).aggregate(remaining_sum=Sum('remaining'))['remaining_sum'] or remaining

            # Get the first sponsored_by_id for the current service
            sponsored_by_id = last_service_user_subquery_sponsored_by_id.filter(
                            service_id=i.id,
                        ).values('user_subscription__sponsored_by_id').first()
            # Get the first sponsored_by_full_name for the current service
            sponsored_by_full_name = last_service_user_subquery_sponsored_by_full_name.filter(
                service_id=i.id,  # Replace your_service_id with the actual service ID
            ).values('user_subscription__sponsored_by__full_name').first()

            # Get the first service_user_type for the current service
            service_user_type = last_service_user_subquery_service_user_type.filter(
                service_id=i.id,  # Replace your_service_id with the actual service ID
            ).values('user_subscription__subscription__package_type').first()

            if sponsored_by_id is not None and 'user_subscription__sponsored_by_id' in sponsored_by_id.keys() :
                sponsored_by_id=sponsored_by_id['user_subscription__sponsored_by_id']
            
            if sponsored_by_full_name is not None and 'user_subscription__sponsored_by__full_name' in sponsored_by_full_name.keys() :
                sponsored_by_full_name=sponsored_by_full_name['user_subscription__sponsored_by__full_name']
            
            if service_user_type is not None and 'user_subscription__subscription__package_type' in service_user_type.keys() :
                service_user_type=service_user_type['user_subscription__subscription__package_type']
            
            service[k].validity = validity_sum
            service[k].remaining = remaining
            service[k].sponsored_by_id = sponsored_by_id
            service[k].sponsored_by_full_name = sponsored_by_full_name
            service[k].service_user_type = service_user_type
            

        if farmer_id:
            user_id=farmer_id
        else:
            user_id=request.user.id
        serialized= ServiceDetailedSerializer(service,many=True,context={"user_ids":all_admins,"is_admin":is_admin,"user_id":user_id})
        if(serialized):
            return res.req_response("",True,"",status.HTTP_200_OK ,serialized.data)            
        
        return res.req_response("",False,"SS-GSGET-01",status.HTTP_400_BAD_REQUEST)



class VerifyCoupon(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]  

    def post(self,request):
        data= json.loads(request.body)
        coupon= data['coupon']
        try:
            check=Coupon.objects.filter(name=coupon).get()
        except Coupon.DoesNotExist:
            check=None
        if not check:
            return res.req_response("Invalid Coupon",False,"SS-VCPOST-01",status.HTTP_400_BAD_REQUEST)
        
         
        check2 = CouponUser.objects.filter(coupon=check,user=request.user).exists()
        if check2:
            return res.req_response("Coupon expired",False,"SS-VCPOST-02",status.HTTP_400_BAD_REQUEST)

        if check.type=="fpo" and request.user.user_role.role_name.lower()!="admin":
            return res.req_response("You are not authorized to use this coupon",False,"SS-VCPOST-03",status.HTTP_400_BAD_REQUEST)

        serialized= CouponSerializer(check).data
        return res.req_response("Coupon verified",True,"",status.HTTP_200_OK,serialized)







class TestFunction(APIView,SubscriptionRequiredMixin):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]   
        
    
    def get(self, request):
        data= self.check_service(request,'sms')
        if not data['status']:
            data['error_code']="SS-TFGET-01"
            return res.req_response(data['message'],data['status'],data['error_code'],data['status_code'])
        
        ###
        helper.deductValidityNumber(request.user,'sms',1)

        return Response({},status=200)