from django.db import models

from core.models import BaseModel
from app_farm.utils.constants import INSURANCE_GENDERS,KUTUMB_MODEL_COMPLETION_STATUS,RELATIONSHIPS
from payment.models import Payment
from app_farm.models import user
# Create your models here.
class Member(BaseModel):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50,null=True,blank=True)
    dob = models.CharField(max_length=10)
    gender = models.CharField(max_length=10,choices=INSURANCE_GENDERS)
    phone = models.BigIntegerField()
    aadhaar_num = models.BigIntegerField(null=True,blank=True)
    masked_aadhaar = models.CharField(max_length=12)
    email = models.CharField(max_length=50,blank=True,null=True)
    address1 = models.CharField(max_length=200)
    address2 = models.CharField(max_length=200)
    # address3 = models.CharField(max_length=100,blank=True,null=True)
    # address4 = models.CharField(max_length=100,blank=True,null=True)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)
    country = models.CharField(max_length=10)
    front_aadhaar = models.ImageField(max_length=500,null=True,blank=True)
    back_aadhaar = models.ImageField(max_length=500,null=True,blank=True)
    bank_acc = models.ForeignKey(to='payment.BankAccount',on_delete=models.SET_NULL,related_name='member_bank',null=True,blank=True)
    height= models.CharField(max_length=50,null=True,blank=True)
    weight= models.CharField(max_length=50,null=True,blank=True)
    face_closeup_img= models.ImageField(max_length=500,null=True,blank=True)
    height_determination_img= models.ImageField(max_length=500,null=True,blank=True)
    
    def __str__(self):
        return self.first_name + ' ' + self.last_name

class Kutumb(BaseModel):
    kutumb_id = models.CharField(max_length=200,unique=True)
    husband = models.ForeignKey(to=Member,on_delete=models.SET_NULL,related_name='husband',null=True)
    wife = models.ForeignKey(to=Member,on_delete=models.SET_NULL,related_name='wife',null=True)
    status = models.CharField(max_length=200, choices=KUTUMB_MODEL_COMPLETION_STATUS, default='husband_aadhaar')
    payment = models.ForeignKey(to='payment.Payment',on_delete=models.CASCADE,related_name='kutumb_payment',null=True,blank=True,editable=False)
    added_by_org = models.ForeignKey(to='app_farm.organizations',on_delete=models.CASCADE,related_name='kutumb_org')
    valid_until = models.DateField(blank=True,null=True)
    def __str__(self):
        return self.kutumb_id

    
class Nominee(BaseModel):
    kutumb = models.ForeignKey(to=Kutumb,on_delete=models.CASCADE,related_name='nominee_family')
    name = models.CharField(max_length=50,null=True,blank=True)
    relationship = models.CharField(max_length=10,choices=RELATIONSHIPS)
    phone = models.BigIntegerField(null=True,blank=True)
    assignee = models.CharField(max_length=50,null=True,blank=True)
    assignee_relationship = models.CharField(max_length=11,choices=RELATIONSHIPS,blank=True,null=True)
    
    def __str__(self):
        return self.name + '-' + self.relationship
    




class InsuranceEnrollment(models.Model):
    added_by=models.ForeignKey(to=user,on_delete=models.CASCADE,related_name="insurane_added_by",null=True,blank=True)
    aadhaar_number = models.CharField(max_length=12)
    front_aadhaar = models.CharField(max_length=500,null=True,blank=True)
    back_aadhaar = models.CharField(max_length=500,null=True,blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField()
    gender = models.CharField(max_length=20)
    mobile = models.CharField(max_length=10)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    pin = models.CharField(max_length=6)

    occupation = models.CharField(max_length=100)
    education = models.CharField(max_length=50)
    smoker_status = models.CharField(max_length=10)

    photograph_upload = models.CharField(max_length=500, null=True,blank=True)

    nominee_first_name = models.CharField(max_length=100)
    nominee_last_name = models.CharField(max_length=100)
    nominee_gender = models.CharField(max_length=20)
    nominee_dob = models.DateField()
    nominee_relation = models.CharField(max_length=50)
    nominee_mobile = models.CharField(max_length=10)
    nominee_email = models.EmailField(blank=True, null=True)

    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=30)
    ifsc = models.CharField(max_length=15)
    height = models.CharField(max_length=10)
    weight = models.CharField(max_length=10)
    amount =models.IntegerField(default=0)
    social_scheme = models.CharField(max_length=100, blank=True, null=True)
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    status_esign= models.IntegerField(default=0)# 0 for pending, 1 for success,2 for failed
    payment=models.ForeignKey(to=Payment,on_delete=models.SET_NULL,related_name="adhar_enroll_payment",null=True,blank=True)

    bank_acc = models.ForeignKey(to='payment.BankAccount',on_delete=models.SET_NULL,related_name='insurance_bank',null=True,blank=True)
    bank_verified = models.IntegerField(default=0)# 0 for pending, 1 for success,2 for failed
    status=models.IntegerField(default=0)# 0 for pending, 1 for success,2 for failed
