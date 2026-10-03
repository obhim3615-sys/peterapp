from django.db import models
from verification.models import BaseModel
from app_farm.models import user as userModel
from app_farm.utils.constants import SUBSCRIPTION_TYPES
from django.utils.text import slugify 
# Create your models here.

class Service(BaseModel):
    name=models.CharField(max_length=200)
    slug=models.SlugField(editable=False,unique=True)
    type=models.CharField(max_length=200,choices=[("farmer","Farmer"),("fpo","Organization")])
    status=models.BooleanField(default=True)
    price=models.DecimalField(max_digits=10,decimal_places=2,)
    unit=models.CharField(max_length=200, choices=[("min","Minute"),("days","Days"),("number","Number")])

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Service, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name+" / "+self.slug

class Subscription(BaseModel):
    name=models.CharField(max_length=200)
    slug=models.SlugField(editable=False,unique=True)
    type=models.CharField(max_length=200,choices=[("farmer","Farmer"),("fpo","Organization")])
    status=models.BooleanField(default=True)
    price=models.DecimalField(max_digits=10,decimal_places=2,default=0.0)
    validity=models.IntegerField(default=0)
    package_type=models.CharField(max_length=200,choices=SUBSCRIPTION_TYPES,default='subscription')
    color=models.CharField(max_length=200,blank=True,null=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Subscription, self).save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name+" / "+self.slug
    
class SubscriptionService(BaseModel):
    subscription=models.ForeignKey(to=Subscription,on_delete=models.CASCADE,related_name="subscription_service")
    service=models.ForeignKey(to=Service,on_delete=models.CASCADE, related_name="service_subscription")
    validity=models.IntegerField()

    def __str__(self) -> str:
        return self.subscription.name+" / "+self.service.name
    
    
class UserSubscription(BaseModel):
    user=models.ForeignKey(to=userModel,on_delete=models.CASCADE,related_name="user_subscription")
    subscription=models.ForeignKey(to=Subscription,on_delete=models.CASCADE,related_name="subscription_user")
    validity=models.DateTimeField()
    sponsored_by=models.ForeignKey(to=userModel,on_delete=models.CASCADE,related_name="user_sponsored_by")


    def __str__(self) -> str:
        return self.user.full_name+" / "+self.subscription.name


class UserServiceManager(models.Manager):
    def get_remaining(self,service_slug:str,user_id:list):
        return self.filter(service__slug=service_slug,user_id__in=user_id,remaining__gt=0)



class UserService(BaseModel):
    user=models.ForeignKey(to=userModel,on_delete=models.CASCADE,related_name="user_service")
    service=models.ForeignKey(to=Service,on_delete=models.CASCADE,related_name="service_user")
    user_subscription=models.ForeignKey(to=UserSubscription,on_delete=models.CASCADE,related_name="user_subscription_service")
    validity=models.IntegerField()
    remaining=models.IntegerField(default=0)
    objects=UserServiceManager()
    
    def __str__(self) -> str:
        return self.user.full_name+" / "+self.service.name


class Coupon(BaseModel):
    name=models.CharField(max_length=6)
    value=models.IntegerField(default=0)
    type=models.CharField(max_length=100,choices=[('farmer',"Farmer"),('fpo',"FPO")])

    def __str__(self) -> str:
        return self.name+" / "+str(self.value)+"% / "+self.type

class CouponUser(BaseModel):
    coupon=models.ForeignKey(to=Coupon,on_delete=models.CASCADE,related_name="coupan_user")
    user=models.ForeignKey(to=userModel,on_delete=models.CASCADE,related_name="user_coupan")

    def __str__(self) -> str:
        return self.coupon.name+" / "+self.user.full_name
