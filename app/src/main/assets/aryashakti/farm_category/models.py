from django.db import models
try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField

from app_farm.models import language_master,farm,crop_master,user
from verification.models import BaseModel

from django.contrib.gis.db import models as models2


# Create your models here.
class Category(BaseModel):
    status = models.CharField(max_length=100)
    trigger = models.CharField(max_length=100, editable=False)
    healthy = models.IntegerField()
    stress = models.IntegerField()
    damaged = models.IntegerField()
    color = models.CharField(max_length=7)
    
    def __unicode__(self):
        return self.id
    
    def __str__(self):
        return self.status
    
class FarmsCategory(BaseModel):
    farm = models.OneToOneField(farm,on_delete=models.CASCADE,related_name='category_farm')
    satelite_date = models.CharField(max_length=10,blank=True,null=True)
    biotic_map = JSONField(blank=True,null=True)
    biotic_category = models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,blank=True,related_name='category_biotic')
    abiotic_map = JSONField(blank=True,null=True)
    abiotic_category = models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,blank=True,related_name='category_abiotic')
    moisture_map = JSONField(blank=True,null=True)
    moisture_category = models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,blank=True,related_name='category_moisture')
    micro_nutrient_map = JSONField(blank=True,null=True)
    micro_nutrient_category = models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,blank=True,related_name='category_micro_nutrient')
    boundary = JSONField(blank=True,null=True)
    whole_map = JSONField(blank=True,null=True)
    yieldpotential=models.DecimalField(max_digits=12, decimal_places=2,null=True,blank=True)
    stressmin=models.DecimalField(max_digits=12, decimal_places=2,null=True,blank=True)
    stressmax=models.DecimalField(max_digits=12, decimal_places=2,null=True,blank=True)
    yieldlossmin=models.DecimalField(max_digits=12, decimal_places=2,null=True,blank=True)
    yieldlossmax=models.DecimalField(max_digits=12, decimal_places=2,null=True,blank=True)
    yieldmin=models.DecimalField(max_digits=12, decimal_places=2,null=True,blank=True)
    yieldmax=models.DecimalField(max_digits=12, decimal_places=2,null=True,blank=True)
    productionmin=models.DecimalField(max_digits=12, decimal_places=2,null=True,blank=True)
    productionmax=models.DecimalField(max_digits=12, decimal_places=2,null=True,blank=True)
    
    def __unicode__(self):
        return self.id
    
    def __str__(self):
        return str(self.id)


class CelreyTaskStatus(BaseModel):
    STATUS_PASSED = "passed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PASSED, "Passed"),
        (STATUS_FAILED, "Failed"),
    ]

    task_id = models.CharField(max_length=255, unique=True, db_index=True)
    description = models.CharField(max_length=500)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_FAILED)
    input_csv = models.CharField(max_length=500)
    batch_size = models.PositiveIntegerField(default=500)

    total_processed = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    inserted_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)

    result_files = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "farm_category_celery_task_status"
        ordering = ["-id"]

    def __str__(self):
        return f"{self.task_id} - {self.status}"
    
class HeadingAndAdvisory(BaseModel):
    heading = models.CharField(max_length=200)
    advisory = models.CharField(max_length=1000)
    language = models.ForeignKey(language_master, on_delete=models.CASCADE,default=1)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    
    def __unicode__(self):
        return self.id
    
    def __str__(self):
        return self.heading

class CropStage(BaseModel):
    name = models.CharField(max_length=200)
    crop = models.ForeignKey(crop_master, on_delete=models.CASCADE)

    def __str__(self):
        return self.name + '-' + self.crop.crop_name
    
class CropDisease(BaseModel):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name
    
class DiseaseScoring(BaseModel):
    stage = models.ForeignKey(CropStage, on_delete=models.CASCADE)
    disease = models.ForeignKey(CropDisease, on_delete=models.CASCADE)
    rank = models.IntegerField()
    min_value = models.IntegerField()
    max_value = models.IntegerField()
    whole_plant = models.BooleanField(default=False)
    leaf = models.BooleanField(default=False)
    fruit = models.BooleanField(default=False)
    flower_inflorescence = models.BooleanField(default=False)
    stem = models.BooleanField(default=False)
    branches = models.BooleanField(default=False)
    root = models.BooleanField(default=False)
    jan = models.BooleanField(default=False)
    feb = models.BooleanField(default=False)
    mar = models.BooleanField(default=False)
    apr = models.BooleanField(default=False)
    may = models.BooleanField(default=False)
    jun = models.BooleanField(default=False)
    jul = models.BooleanField(default=False)
    aug = models.BooleanField(default=False)
    sep = models.BooleanField(default=False)
    oct = models.BooleanField(default=False)
    nov = models.BooleanField(default=False)
    dec = models.BooleanField(default=False)

    def __str__(self):
        return str(self.rank)




class Warehouse(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    other_name = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    warehouse_code = models.CharField(max_length=255, null=True, blank=True)
    wcode = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    active = models.BooleanField(default=False)
    whtype = models.CharField(max_length=255, null=True, blank=True)
    longitude = models.DecimalField(decimal_places=8,max_digits=16,blank = True,null=True)
    latitude = models.DecimalField(decimal_places=8,max_digits=16,blank = True,null=True)
    is_blockchain_enabled = models.BooleanField(default=False)
    blockchain_synced_at = models.DateTimeField(null=True, blank=True)
    take_over_case = models.BooleanField(default=False)
    mill_compound = models.BooleanField(default=False)
    modified_by = models.CharField(max_length=255, null=True, blank=True)
    last_deactivated_at = models.DateTimeField(null=True, blank=True)
    pincode = models.IntegerField(null=True, blank=True)
    total_capacity = models.FloatField(default=0.0,null=True,blank=True)
    warehouse_start_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    min_pwh_rate_per_mt = models.FloatField(default=0.0)
    geometry = models2.GeometryField(srid=4326, null=True, blank=True)

    def __str__(self):
        return self.name
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__original_longitude = self.longitude
        self.__original_latitude = self.latitude
    
    def save(self, *args, **kwargs):
        if self.longitude!=self.__original_longitude or self.latitude !=self.__original_latitude :
            point = Point(float(self.longitude), float(self.latitude), srid=4326)
            self.geometry=point
        super(Warehouse, self).save(*args, **kwargs)

from django.contrib.gis.geos import Point
class BuyerSellerDetail(BaseModel):
    name= models.CharField(max_length=200,)
    contact_number= models.CharField(max_length=200,null=True,blank=True)
    longitude = models.DecimalField(decimal_places=8,max_digits=16,blank = True,null=True)
    latitude = models.DecimalField(decimal_places=8,max_digits=16,blank = True,null=True)
    type_user = models.CharField(max_length=50,choices=[('Buyer', 'Buyer'), ('Seller', 'Seller')],blank=True,null=True)
    extras= JSONField(null=True,blank=True)
    geometry = models2.GeometryField(srid=4326, null=True, blank=True)

    def save(self, *args, **kwargs):
        point = Point(float(self.longitude), float(self.latitude), srid=4326)
        self.geometry=point
        super(BuyerSellerDetail, self).save(*args, **kwargs)
        
class UserInterest(BaseModel):
    user = models.ForeignKey(user, on_delete=models.CASCADE,null=True,blank=True)
    remarks= JSONField()
    type_interest=models.CharField(max_length=50,choices=[('buy', 'buy'), ('sell', 'sel')],blank=True,null=True)
    longitude = models.DecimalField(decimal_places=8,max_digits=16,blank = True,null=True)
    latitude = models.DecimalField(decimal_places=8,max_digits=16,blank = True,null=True)


class WarehouseIndiaClusture(models.Model):
    ogc_fid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True)
    begin = models.DateTimeField(blank=True, null=True)
    end = models.DateTimeField(blank=True, null=True)
    altitudemode = models.CharField(max_length=255, blank=True, null=True)
    tessellate = models.IntegerField(blank=True, null=True)
    extrude = models.IntegerField(blank=True, null=True)
    visibility = models.IntegerField(blank=True, null=True)
    draworder = models.IntegerField(blank=True, null=True)
    icon = models.CharField(max_length=255, blank=True, null=True)
    cluster_number = models.CharField(max_length=255, blank=True, null=True)
    fill = models.CharField(max_length=255, blank=True, null=True)
    stroke_opacity = models.CharField(max_length=255, blank=True, null=True)
    stroke = models.CharField(max_length=255, blank=True, null=True)
    stroke_width = models.CharField(max_length=255, blank=True, null=True)
    wkb_geometry = models2.GeometryField(srid=4326, blank=True, null=True)
    pincode = models.IntegerField( blank=True, null=True)


class WarehousePincodeLocation(BaseModel):
    object_id = models.IntegerField(null=True, blank=True)
    pin_code = models.CharField(max_length=10, unique=True)
    office_name = models.CharField(max_length=255)
    office_type = models.CharField(max_length=50)
    circle_name = models.CharField(max_length=100)
    region_name = models.CharField(max_length=100)
    division_name = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    def __str__(self):
        return f"{self.office_name} ({self.pin_code})"




class SixtyKmCluster(models.Model):
    ogc_fid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    wkb_geometry = models2.GeometryField(srid=4326, blank=True, null=True)

    class Meta:
        db_table = "sixty_km"
        indexes = [
            models.Index(fields=["wkb_geometry"], name="sixty_km_geom_idx"),
        ]

    def __str__(self):
        return self.name or f"SixtyKm Cluster {self.ogc_fid}"


class TenKmCluster(models.Model):
    ogc_fid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    wkb_geometry = models2.GeometryField(srid=4326, blank=True, null=True)

    class Meta:
        db_table = "ten_km"
        indexes = [
            models.Index(fields=["wkb_geometry"], name="ten_km_geom_idx"),
        ]

    def __str__(self):
        return self.name or f"TenKm Cluster {self.ogc_fid}"
   




class Location(BaseModel):
    TYPE_CHOICES = [
        ("COUNTRY", "Country"),
        ("STATE", "State"),
        ("DISTRICT", "District"),
        ("PINCODE", "Pincode"),
        ("LOCATION", "Location"),
    ]

    # id = models.BigAutoField(primary_key=True)  # matches your CSV id
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    name = models.CharField(max_length=255)
    status = models.BooleanField(default=True)
    created_by = models.IntegerField(null=True, blank=True)
    # created_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    # updated_at = models.DateTimeField(null=True, blank=True)
    code = models.CharField(max_length=50, null=True, blank=True)
    alpha_code = models.CharField(max_length=50, null=True, blank=True)
    sap_code = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        db_table = "location"
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["name"]),
            models.Index(fields=["parent"]),
        ]

    def __str__(self):
        return f"{self.type}: {self.name}"
