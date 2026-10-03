from django.db import models
# Create your models here.
from verification.models import BasicModel,BaseModel
from app_farm.models import user,crop_master,organizations,farm,crop_variety_master
from recordActivity.models import ActivityRecord
try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField

class CropManager(models.Manager):
    def get_crop(self):
        return self.filter(status=True).all()

class Crop(models.Model,BasicModel):
    name=models.CharField(max_length=200)
    status=models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

class Variety(models.Model,BasicModel):
    name=models.CharField(max_length=200)
    status=models.BooleanField(default=True)
    def __str__(self) -> str:
        return self.name
    
     

class Stage(models.Model,BasicModel):
    name=models.CharField(max_length=200)
    status=models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

class SubStage(models.Model,BasicModel):
    name=models.CharField(max_length=200)
    notes=models.TextField(null=True,blank=True)
    status=models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name
    
     

class Activity(models.Model,BasicModel):
    name=models.CharField(max_length=200)
    notes=models.TextField(null=True,blank=True)
    status=models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

class Product(models.Model,BasicModel):
    name=models.CharField(max_length=200)
    status=models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

class DASManage(models.Model,BasicModel):
    crop=models.ForeignKey(to=Crop,on_delete=models.CASCADE, related_name='das_crop')
    variety=models.ForeignKey(to=Variety,on_delete=models.CASCADE,null=True,blank=True, related_name='das_variety')
    stage=models.ForeignKey(to=Stage,on_delete=models.CASCADE , related_name='das_stage')
    sub_stage=models.ForeignKey(to=SubStage,on_delete=models.CASCADE ,null=True,blank=True, related_name='das_sub_stage')
    day_number=models.IntegerField()
    notes=models.TextField(blank=True,null=True)
    water_required=models.CharField(max_length=200,blank=True,null=True)
    nutrient_required=models.CharField(max_length=200,blank=True,null=True)

    def __str__(self) -> str:
            stage_name=day_number=crop_name=variety=sub_stage=""
            if self.crop:
                 crop_name=self.crop.name
            
            if self.stage:
                 stage_name=self.stage.name

            if self.variety:
                 variety=self.variety.name

            if self.sub_stage:
                 sub_stage=self.sub_stage.name
            
            if self.day_number:
                 day_number=self.day_number

            return crop_name+"("+variety+") / "+stage_name+"("+sub_stage+") / "+str(day_number)

class DASProduct(models.Model,BasicModel):
    das=models.ForeignKey(to=DASManage,on_delete=models.CASCADE, related_name='das_relation')
    product=models.ForeignKey(to=Product,on_delete=models.CASCADE, related_name='das_product')

    def __str__(self) -> str:
            return self.das.crop.name+" / "+self.product.name+" / "+str(self.das.day_number)

class DASActivity(models.Model,BasicModel):
    das=models.ForeignKey(to=DASManage,on_delete=models.CASCADE, related_name='das_activity_relation')
    activity=models.ForeignKey(to=Activity,on_delete=models.CASCADE,related_name='das_activity')

    def __str__(self) -> str:
            return self.das.crop.name+" / "+self.activity.name+" / "+str(self.das.day_number)
    
#multiple record of single das against a farmer
class DASFarmerCalendar(BaseModel):
     farmer=models.ForeignKey(to=user,on_delete=models.CASCADE,related_name="data_data_farmer")
     das=models.ForeignKey(to=DASManage,on_delete=models.CASCADE,related_name="das_data")
     is_sent=models.IntegerField(default=0)
     is_follow=models.IntegerField(default=0)

#single data of a famer 
class DASFarmer(BaseModel):
     farmer= models.ForeignKey(to=user,on_delete=models.CASCADE,related_name='das_farmer')
     delay=models.IntegerField(default=0)
     sowing_date=models.DateTimeField()
     next_das=models.IntegerField(default=0)



# This table is the "capsule" of PoPs (independent of org/farmer variations)
class POPGroup(BaseModel):
    name = models.CharField(max_length=1500)
    created_by_user = models.ForeignKey(
        user, null=True, blank=True, on_delete=models.SET_NULL
    )  # Aryashakti user (internal agronomist, etc.)
    created_by_buyer_id = models.IntegerField(null=True, blank=True)  # PrithviPro user id
    created_from_prithvipro = models.BooleanField(default=False)  # flag to identify source
    csv_upload_status = models.CharField(
        max_length=30,
        default="created",  # created, processing, completed, failed
    )
    crop=models.ForeignKey(to=crop_master,null=True,blank=True,on_delete=models.CASCADE,related_name='pop_group_crop')
    variety=models.ForeignKey(to=crop_variety_master,null=True,blank=True,on_delete=models.CASCADE,related_name='pop_group_crop_variety_master')
    def __str__(self):
        return self.name




class ActivityPOP(BaseModel): 
    from_das =models.IntegerField(default=0)
    to_das =models.IntegerField(default=0)
    crop=models.ForeignKey(to=crop_master,null=True,blank=True,on_delete=models.CASCADE,related_name='activity_pop_crop')
    variety=models.ForeignKey(to=crop_variety_master,null=True,blank=True,on_delete=models.CASCADE,related_name='activity_pop_crop_variety_master')
    stage= models.ForeignKey(to=Stage,null=True,blank=True,on_delete=models.CASCADE,related_name='activity_pop_stages')
    sub_stage= models.ForeignKey(to=SubStage,null=True,blank=True,on_delete=models.CASCADE,related_name='activity_pop_sub_stages')
    jsondata =JSONField()
    activity_records_id=models.ForeignKey(to=ActivityRecord,on_delete=models.CASCADE,related_name='activity_pop_activity_record')
    pop_group = models.ForeignKey(POPGroup, related_name="definitions", on_delete=models.CASCADE,null=True,blank=True)

    def __str__(self):
        return self.activity_records_id.name
class OrganizationSoilTestingToken(BaseModel):
    org= models.OneToOneField(to=organizations,on_delete=models.CASCADE,related_name="organization_soil_testing")
    soil_testing_token=models.CharField(max_length=300)


class FarmSoilTested(BaseModel):
    farm_value=models.ForeignKey(to=farm,null=True,blank=True,on_delete=models.CASCADE,related_name="farm_soil_testing")
    sample_id=models.CharField(max_length=100,unique=True)
    project_id=models.CharField(max_length=100)
    file_response= models.CharField(max_length=1000,null=True,blank=True)
    json_response= JSONField(null=True,blank=True)
    
class Session(BaseModel):
    name = models.CharField(max_length=50, null=False, blank=False)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class CropSession(BaseModel):
    crop = models.ForeignKey(crop_master, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    from_month = models.IntegerField()
    to_month = models.IntegerField()

    def __str__(self):
        return f"{self.crop} - {self.session} ({self.from_month} to {self.to_month})"




# Bridge between Aryashakti farms and PrithviPro listings
class FarmListing(BaseModel):
    farm = models.ForeignKey(farm, related_name="farm_listings", on_delete=models.CASCADE)
    listing_id = models.IntegerField()  # ID from PrithviPro Listing
    pop_group = models.ForeignKey(POPGroup,related_name="listingpop", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ("farm", "listing_id")

    def __str__(self):
        return f"Farm {self.farm.id} ↔ Listing {self.listing_id}"
    


# pop_manage/models.py  (or a suitable app)

class PopNotificationLog(BaseModel):
    STATUS_CHOICES = (
        ("success", "Success"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
    )

    farm = models.ForeignKey("app_farm.farm", on_delete=models.CASCADE)
    farmer = models.ForeignKey("app_farm.user", on_delete=models.CASCADE)
    activity = models.ForeignKey("pop_manage.ActivityPOP", on_delete=models.SET_NULL, null=True, blank=True)
    organization = models.ForeignKey("app_farm.organizations", on_delete=models.CASCADE)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    message = models.TextField(null=True, blank=True)  # push message body
    response = models.JSONField(null=True, blank=True)  # firebase raw response
    error = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["farm", "created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.farm_id} - {self.status} - {self.created_at.date()}"



class PopShareLog(BaseModel):
    farm= models.ForeignKey(to="app_farm.farm",on_delete=models.CASCADE,related_name="farm_pop_share")
    user_shared= models.ForeignKey(to=user,on_delete=models.CASCADE,related_name="user_pop_share")
    pop= models.ForeignKey(to=ActivityPOP,on_delete=models.CASCADE,related_name="pop_pop_share")
    crop= models.ForeignKey(to=crop_master,on_delete=models.CASCADE,related_name="crop_pop_share")
    variety= models.ForeignKey(to=crop_variety_master,on_delete=models.CASCADE,related_name="crop_variety_pop_share",null=True,blank=True)
    activity= models.ForeignKey(to=ActivityRecord,on_delete=models.CASCADE,related_name="activity_record_pop_share",null=True,blank=True)
    sowing= models.DateTimeField(null=True,blank=True)