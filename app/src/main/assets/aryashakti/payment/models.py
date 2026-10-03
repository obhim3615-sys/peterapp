try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField
from django.db import models
from verification.models import BaseModel
from app_farm.models import user,user_roles,organizations
from subscription_service.models import Subscription,Coupon
from app_farm.utils.constants import ORDER_STATUS,SUBSCRIPTION_TYPES,PAYMENT_TYPE,PAYMENT_STATUS

# Create your models here.
class Order(BaseModel):
    paid_by = models.ForeignKey(to=user, on_delete=models.CASCADE, related_name="paidby",editable=False)
    paid_by_name = models.CharField(max_length=200,editable=False)
    paid_by_role = models.ForeignKey(to=user_roles, on_delete=models.CASCADE,editable=False)
    paid_by_phone = models.CharField(max_length=15,null=True,blank=True,editable=False)
    services = JSONField(null=True,blank=True,editable=False)
    package = models.ForeignKey(to=Subscription, on_delete=models.CASCADE, related_name="subscription",editable=False)
    package_validity = models.IntegerField(default=0,editable=False)
    package_type = models.CharField(max_length=200,choices=SUBSCRIPTION_TYPES,editable=False)
    coupon = models.ForeignKey(to=Coupon, on_delete=models.CASCADE,null=True,blank=True,related_name="coupon",editable=False)
    coupon_discount = models.DecimalField(decimal_places=2,max_digits=10,null=True,blank=True,editable=False)
    coupon_value = models.DecimalField(decimal_places=2,max_digits=10,null=True,blank=True,editable=False)
    price = models.DecimalField(decimal_places=2,max_digits=10,editable=False)
    total_discount = models.DecimalField(decimal_places=2,max_digits=10,editable=False)
    taxes = models.DecimalField(decimal_places=2,max_digits=10,editable=False)
    final_price = models.DecimalField(decimal_places=2,max_digits=10,editable=False)
    status = models.CharField(max_length=200,choices=ORDER_STATUS)
    payment_object = JSONField(null=True,blank=True)
    payment_id = models.CharField(max_length=200,null=True,blank=True)
    payment_link_status = models.CharField(max_length=200,null=True,blank=True)
    
    def __unicode__(self):
        return self.id
    
    def __str__(self):
        return str(self.id)
    
class UserOrder(BaseModel):
    order = models.ForeignKey(to=Order, on_delete=models.CASCADE,editable=False)
    user = models.ForeignKey(to=user, on_delete=models.CASCADE,related_name="orderuser",editable=False)
    
    def __unicode__(self):
        return self.id
    
    def __str__(self):
        return str(self.id)
    
class UserBankAccount(BaseModel):
    user = models.OneToOneField(to=user, on_delete=models.CASCADE,editable=False)
    name = models.CharField(max_length=100,null=True,blank=True)
    contact = models.BigIntegerField(unique=True)
    email = models.CharField(max_length=100,blank=True,null=True)
    account_num = models.CharField(max_length=40,unique=True)
    ifsc = models.CharField(max_length=11)
    bank_name = models.CharField(max_length=100,blank=True,null=True)
    contact_id = models.CharField(max_length=100,blank=True,null=True)
    fund_account = models.CharField(max_length=100,blank=True,null=True)
    fav_id = models.CharField(max_length=100,blank=True,null=True)
    pams_account_id = models.BigIntegerField(
        null=True,
        blank=True
    )
    
    def __unicode__(self):
        return self.id
    
    def __str__(self):
        return str(self.id)
    
class BankAccount(BaseModel):
    name = models.CharField(max_length=100,null=True,blank=True)
    contact = models.BigIntegerField()
    email = models.CharField(max_length=100,blank=True,null=True)
    account_num = models.CharField(max_length=40,unique=True)
    ifsc = models.CharField(max_length=11)
    bank_name = models.CharField(max_length=100,blank=True,null=True)
    contact_id = models.CharField(max_length=100,blank=True,null=True)
    fund_account = models.CharField(max_length=100,blank=True,null=True)
    fav_id = models.CharField(max_length=100,blank=True,null=True)
    verified_by = models.ForeignKey(to=user,on_delete=models.SET_NULL,null=True)
    status= models.IntegerField(default=0)
    
    def __unicode__(self):
        return self.id
    
    def __str__(self):
        return self.account_num + '-' + self.name


class Payment(BaseModel):
    payment_type = models.CharField(max_length=200,choices=PAYMENT_TYPE,editable=False)
    amount = models.DecimalField(decimal_places=2,max_digits=10)
    response = JSONField(null=True,blank=True,editable=False)
    response_json_status = JSONField(null=True,blank=True,editable=False)
    org = models.ForeignKey(to=organizations,null=True,on_delete=models.SET_NULL,blank=True,related_name="payment_org_if_available")
    status = models.CharField(max_length=200,choices=PAYMENT_STATUS)#0 for pending, 1 for success, 2 for failed
    payment_link_id = models.CharField(max_length=200,null=True,blank=True,editable=False)
    latitude = models.DecimalField(decimal_places=8,max_digits=16,blank = True,null=True)
    longitude = models.DecimalField(decimal_places=8,max_digits=16,blank = True,null=True)
    device_details= models.JSONField(null=True,blank=True)
    
    def __str__(self) -> str:
        return str(self.id) + '-' + self.payment_type + '-' + self.status + '-' + str(self.amount)
    
class Payout(BaseModel):
    payout_id = models.CharField(max_length=200,null=True,blank=True,editable=False)
    amount = models.DecimalField(decimal_places=2,max_digits=10)
    response = JSONField(null=True,blank=True,editable=False)
    status = models.CharField(max_length=200,choices=PAYMENT_STATUS)#0 for pending, 1 for success, 2 for failed

    def __str__(self) -> str:
        return str(self.id) + '-' + '-' + self.status + '-' + str(self.amount)
    

class CastlerVirtualAccount(BaseModel):
    user=models.OneToOneField(to=user,on_delete=models.CASCADE,related_name="castler_virtual_account",editable=False)
    virtual_account_id=models.CharField(max_length=400,editable=False)
    ifsc =models.CharField(max_length=100,editable=False)
    status=models.IntegerField(default=1)

