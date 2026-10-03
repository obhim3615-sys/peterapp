from rest_framework import status
from rest_framework.response import Response
from subscription_service.models import *
from app_farm.utils import response as res
from rest_framework import status
from rest_framework import status
from datetime import date
from app_farm.utils.helper import getusersifadmin
from django.db.models import Sum
class SubscriptionRequiredMixin:
    users=[]
    def __init__(self, name):
        self.name=name        
   

    def has_required_service(self,request,name):  
        self.name=name      
        try:
            service=Service.objects.filter(slug=self.name).get()            
        except Service.DoesNotExist:
             service=None
        if service:
            users=[]
            users=getusersifadmin(request.user)
            flag= UserService.objects.filter(service=service, user__in=users).exists()
            if not flag:
                 return False
            self.users=users
        return service

    def check_service(self, request,name):
        # Check if the user has subscribed to the required service or subscription
            
        service= self.has_required_service(request,name)
        if not service :
                result = res.ErrRes()
                result['status']=False
                result['message'] = "You need access to this Service"
                return result
        today_date = date.today()
        # user_service= UserService.objects.filter(user_subscription__validity__gt=today_date,remaining__gt=0,service=service, user__in=self.users).first()
        total_remaining = (
            UserService.objects.filter(
                user_subscription__validity__gt=today_date,
                remaining__gt=0,
                service=service,
                user__in=self.users
            )
            .aggregate(total=Sum('remaining'))
            .get('total') or 0
        )
        if total_remaining > 0:
            return {"status": True, "remaining": total_remaining}
        #UserService.objects.filter(user_subscription__validity__gt=today_date,remaining__gt=0,service=service, user__in=self.users).first()
        #print(user_service.__dict__)
        # if user_service:   
        #     return {"status":True,"remaining":user_service.remaining}     
              
        result = res.ErrRes()
        result['status']=False
        result['status_code']=status.HTTP_403_FORBIDDEN
        result['message'] = "Your subscription has expired"
        return result
            
        

