from django.db import models
from app_farm.models import organizations,user as user2
from django.contrib.auth.models import User as UserDefault
# from ckeditor.fields import RichTextField
from django_ckeditor_5.fields import CKEditor5Field

class BasicModel():
    pass

class BaseModel(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True,verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True,db_index=True,verbose_name='updated at')

    class Meta:
        abstract = True

# Create your models here.
class SignzyAuth(BaseModel):
    auth_token=models.CharField(max_length=200)
    patronid= models.CharField(max_length=200)
    ttl=models.CharField(max_length=200)
    token_created_at=models.DateTimeField( verbose_name='token created at')
    expiry_date=models.DateTimeField()
    reason_creation=models.CharField(max_length=200)

class PanVerificationManager(models.Manager):
    def get_user_pan(self,user_id):
        return self.get(user__id=user_id)
    
class PanVerifcation(BaseModel):
    user= models.ForeignKey(to=user2, on_delete=models.CASCADE)
    organization= models.ForeignKey(to=organizations, on_delete=models.CASCADE, default=1)
    pan_number=models.CharField(max_length=200, )
    pan_dob=models.CharField(max_length=200, null=True,blank=True)
    pan_name=models.CharField(max_length=200, )
    father_name=models.CharField(null=True,blank=True ,max_length=200, )
    response_details= models.TextField(null=True,blank=True)
    response_consolidate= models.TextField(null=True,blank=True)
    leadId=models.IntegerField(null=True,blank=True )
    business_cibil_avg=models.DecimalField(max_digits=16,decimal_places=8,null=True,blank=True)
    cibil_fetch_date=models.DateField(null=True,blank=True)
    cin_number=models.CharField(max_length=250,null=True,blank=True)
    address=models.CharField(max_length=200,null=True,blank=True)
    pincode=models.CharField(max_length=200,null=True,blank=True)
    email=models.CharField(max_length=200,null=True,blank=True)
    state=models.CharField(max_length=200,null=True,blank=True)
    dpd_status=models.CharField(max_length=200,null=True,blank=True)
    write_off_status=models.CharField(max_length=200,null=True,blank=True)
    go_no_go_case_passed=models.CharField(max_length=200,null=True,blank=True)
    bank_uploaded=models.IntegerField(default=0)

    objects=PanVerificationManager()

    def __str__(self) -> str:
        return self.pan_number

class OrganizationConsolidationDirectorManager(models.Manager):
    def get_not_verified_director_count(self,user):
        return self.filter(user=user,is_adhar_verified=False).count()

class OrganizationConsolidationDirector(BaseModel):
    user= models.ForeignKey(to=user2, on_delete=models.CASCADE)
    organization= models.ForeignKey(to=organizations, on_delete=models.CASCADE,default=1)
    pan=models.ForeignKey(to=PanVerifcation,on_delete=models.CASCADE,related_name="directors")
    director=models.CharField(max_length=200)
    director_pan=models.CharField(max_length=200,null=True,blank=True)
    father_name=models.CharField(max_length=200,null=True,blank=True)
    director_state=models.CharField(max_length=200,null=True,blank=True)
    pincode=models.CharField(max_length=200,null=True,blank=True)
    address=models.CharField(max_length=200,null=True,blank=True)
    email=models.CharField(max_length=200,null=True,blank=True)
    dob=models.DateField(null=True,blank=True)
    adhar_req_id=models.CharField(max_length=200,null=True,blank=True)
    mobile_number=models.CharField(max_length=50,null=True,blank=True)
    adhar_url=models.CharField(max_length=500,null=True,blank=True)
    is_adhar_verified=models.BooleanField(default=False)
    adhar_verification_response=models.TextField(blank=True,null=True)
    cibilIndividual=models.DecimalField(max_digits=16,decimal_places=8,null=True,blank=True)
    objects=OrganizationConsolidationDirectorManager()

    def __str__(self) -> str:
        return self.pan.pan_number
    
class AdharVerifcation(BaseModel):
    user= models.ForeignKey(to=user2, on_delete=models.CASCADE)
    response_details= models.TextField()


class GSTData(BaseModel):
    user= models.ForeignKey(to=user2, on_delete=models.CASCADE)
    gstin=models.CharField(max_length=200)
    registrationDate= models.CharField(max_length=200,blank=True,null=True)
    principalAddress= models.TextField(blank=True,null=True)
    response= models.TextField(max_length=100,blank=True,null=True)




class Document(BaseModel):
    name = models.CharField(max_length=200)
    slug= models.CharField(max_length=200,editable=False)
    status= models.BooleanField(default=True)
    is_required= models.BooleanField(default=True)
    created_by=models.ForeignKey(to=UserDefault,null=True, on_delete=models.CASCADE, related_name="created_by")
    updated_by=models.ForeignKey(to=UserDefault,null=True, on_delete=models.CASCADE, related_name="updated_by")


    def __str__(self) -> str:
        return self.name+" "+str(self.created_by)
    
    def save_model(self,request,obj):
        if self.pk:
            obj.updated_by=request.user
        else:
            obj.created_by=request.user
        
        obj.save()


class UserVerificationDocument(BaseModel):
    user= models.ForeignKey(to=user2, on_delete=models.CASCADE, related_name="document_user")
    document_type= models.ForeignKey(to=Document,related_name="documents_type",on_delete=models.CASCADE)
    document_id= models.IntegerField(null=True,blank=True)
    status= models.IntegerField(default=1)
    type = models.CharField( max_length=200, choices=[("verification_adharuser_request","Verification Adhar"),("verification_panuser_request","Verification Pan"),("verification_gstuser_request","Verification GST"),("onemoney_onemoneyconsent_request","Bank Statement"),("payment_bankaccountvalidation_request","Bank Account Validation")])
    verified_by=models.ForeignKey(to=user2,on_delete=models.CASCADE,null=True,blank=True,related_name="verified_document")
    def __str__(self) -> str:
        return self.user.full_name+" -> "+self.document_type.name
    

class UnsecureLoanStepManager(models.Manager):
    def get_loan_document(self):
        return self.filter(id=1).first()
    
class UnsecureLoanStep(BaseModel):
    name= models.CharField(max_length=200)
    slug= models.CharField(max_length=200,editable=False)
    status= models.BooleanField(default=True)
    is_required= models.BooleanField(default=True)
    created_by=models.ForeignKey(to=UserDefault,null=True, on_delete=models.CASCADE, related_name="unsecure_created_by")
    updated_by=models.ForeignKey(to=UserDefault,null=True, on_delete=models.CASCADE, related_name="unsecure_updated_by")
    objects = UnsecureLoanStepManager()
    link_url= models.CharField(max_length=200,null=True,blank=True)
    is_iframe= models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name
    
    def save_model(self,request,obj):
        if self.pk:
            obj.updated_by=request.user
        else:
            obj.created_by=request.user
        
        obj.save()



class UserUnsecureLoan(BaseModel):
    user= models.ForeignKey(to=user2, on_delete=models.CASCADE, related_name="unsecure_user")
    unsecure_step= models.ForeignKey(to=UnsecureLoanStep,related_name="unsecure_step",on_delete=models.CASCADE)
    status=models.IntegerField(default=1)
    def __str__(self) -> str:
        return self.user.full_name+" -> "+self.unsecure_step.name


class TemplateData(BaseModel):
    template_name=models.CharField(max_length=200)
    type=models.CharField(max_length=200,default="pre_sanction",choices=[("pre_sanction","Pre sanctioned Doc"),("post_sanction","Post Sanctioned Doc"),("disbursement","Disbursement Request")])
    body= CKEditor5Field(null=True, blank=True )

    def __str__(self) -> str:
        return self.template_name


class TemplateKey(BaseModel):
    template_data= models.ForeignKey(to=TemplateData,on_delete=models.CASCADE,related_name="template_template_key")
    key=models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.template_data.template_name+" / "+self.key
    

class OrganizationKeyValues(BaseModel):
    organization= models.OneToOneField(to=organizations,on_delete=models.CASCADE,related_name='organization_key_value')
    fpo_name=models.CharField(max_length=200,null=True,blank=True)
    document_execution_date=models.CharField(max_length=200,null=True,blank=True)
    first_guaranter_name=models.CharField(max_length=200,null=True,blank=True)
    second_guaranter_name=models.CharField(max_length=200,null=True,blank=True)
    gurantor_father_name=models.CharField(max_length=200,null=True,blank=True)
    gurantor_address=models.CharField(max_length=200,null=True,blank=True)
    gurantor_phone_no=models.CharField(max_length=200,null=True,blank=True)
    ifsc_code=models.CharField(max_length=200,null=True,blank=True)
    bank_name=models.CharField(max_length=200,null=True,blank=True)
    account_no=models.CharField(max_length=200,null=True,blank=True)
    disbursed_amount_dynamic=models.CharField(max_length=200,null=True,blank=True)
    ard_number=models.CharField(max_length=200,null=True,blank=True)
    date_of_disbursement=models.CharField(max_length=200,null=True,blank=True)    
    cheque_no=models.CharField(max_length=200,null=True,blank=True) 
    interest_rate=models.CharField(max_length=200,null=True,blank=True) 
    date_of_sanction_letter=models.CharField(max_length=200,null=True,blank=True) 
    place=models.CharField(max_length=200,null=True,blank=True)
    fpo_address=models.CharField(max_length=200,null=True,blank=True)
    sanction_amount=models.CharField(max_length=200,null=True,blank=True)
    sanction_amount_words=models.CharField(max_length=200,null=True,blank=True)
    arya_adress=models.CharField(max_length=200,null=True,blank=True)
    date_of_signing=models.CharField(max_length=200,null=True,blank=True)
    fpo_name_designation=models.CharField(max_length=200,null=True,blank=True)
    gurantor_name=models.CharField(max_length=200,null=True,blank=True)
    is_completed=models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.organization.org_name
    
class OrganizationTemplate(BaseModel):
    organization= models.ForeignKey(to=organizations,on_delete=models.CASCADE,related_name='organization_template')
    template=models.ForeignKey(to=TemplateData,on_delete=models.CASCADE,related_name='template_organization')
    file_url=models.FileField(max_length=300)

    def __str__(self) -> str:
        return self.organization.org_name+" / "+self.template.template_name
    

class BDProfin(BaseModel):
    name=models.CharField(max_length=200)
    email=models.CharField(max_length=200)