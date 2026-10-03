from django.db import models
from verification.models import BaseModel
from app_farm.models import crop_master,organizations,user,farm
# Create your models here.
from payment.models import Payment,Payout,UserBankAccount,CastlerVirtualAccount

from app_farm.utils.constants import TYPE_OF_PROCUREMENT

class ProcurementRegister(BaseModel):
    name= models.CharField(max_length=300)
    organization=models.ForeignKey(to=organizations,on_delete=models.CASCADE,related_name="procurement_register_organization")
    status= models.BooleanField(default=True)
    user=models.ForeignKey(to=user,on_delete=models.CASCADE,related_name="procurement_register_user")

    def __str__(self) -> str:
        return self.name

class Procurement(BaseModel):
    crop= models.ForeignKey(to=crop_master,on_delete=models.CASCADE,related_name="procurement_crop")
    procure_register=models.ForeignKey(to=ProcurementRegister,on_delete=models.CASCADE,related_name="procurement_procurement_register")
    user_from=models.ForeignKey(to=user,on_delete=models.CASCADE,related_name="procurement_user_from")
    user_to=models.ForeignKey(to=user,on_delete=models.CASCADE,related_name="procurement_user_to")
    # farm=models.ForeignKey(to=farm,on_delete=models.CASCADE,related_name="procurement_farm",null=True,blank=True)
    variety=models.CharField(max_length=200,null=True,blank=True)
    qty=models.IntegerField(default=0)
    rate=models.IntegerField(default=0)
    amount=models.IntegerField(default=0)
    description=models.TextField(null=True,blank=True)
    payment=models.ForeignKey(to=Payment,on_delete=models.SET_NULL,related_name="procurement_payment",null=True,blank=True)
    payout=models.ForeignKey(to=Payout,on_delete=models.SET_NULL,related_name="procurement_payout",null=True,blank=True)
    status=models.IntegerField(default=0)# 0 for pending, 1 for success,2 for failed
    type = models.CharField(max_length=50,choices=[("single","Single"),("bulk","Bulk")],blank=True,null=True)
    def __str__(self):
        return self.user_from.full_name+" "+self.user_to.full_name
    
    

class ProcurementImage(BaseModel):
    procurement=models.ForeignKey(to=Procurement,on_delete=models.CASCADE,related_name="procurement_img")
    image_url=models.ImageField(max_length=400)


class AxisBankOrganization(BaseModel):
    organization=models.OneToOneField(to=organizations,on_delete=models.CASCADE,related_name="axis_bank_organisation_organisation")
    user=models.OneToOneField(to=user,on_delete=models.CASCADE,related_name="axis_bank_organisation_user")
    corp_code=models.CharField(max_length=100,unique=True)
    corp_account_number=models.CharField(max_length=100,unique=True)
