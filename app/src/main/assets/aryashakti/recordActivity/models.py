from django.db import models
from verification.models import BaseModel
from app_farm.models import user,organizations,farm,crop_master,crop_variety_master
from django.contrib.gis.db import models as models2
try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField
# Create your models here.
from django.core import signing
from app_farm.utils.constants import DRONE_SPRAY_STATUS, LAND_SIZE_UNIT

class ActivityRecord(BaseModel):
    organization= models.ForeignKey(to=organizations,on_delete=models.CASCADE,related_name="activity_org",null=True,blank=True)
    name = models.CharField(max_length=200)
    image=models.ImageField(max_length=400,null=True,blank=True)
    order_value=models.IntegerField(default=99)
    
    def __str__(self) -> str:
        return self.name
    

class ActivityFields(BaseModel):
    organization= models.ForeignKey(to=organizations,on_delete=models.CASCADE,related_name="activity_form_org")
    activity=models.ForeignKey(to=ActivityRecord,on_delete=models.CASCADE,related_name='activity_data')
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=200,choices=[("string","String"),("int","Integer"),("optional","Optional"),("date","Date"),("multi-optional","Multi optional")])
    field_possible_value=models.TextField(null=True,blank=True)
    is_required=models.BooleanField(default=True)
    status= models.BooleanField(default=True)
    order_value=models.IntegerField(default=99)
    crop = models.ForeignKey(to=crop_master, on_delete=models.SET_NULL,related_name="crop_master_activity_fields",null=True,blank=True)
    variety = models.ForeignKey(to=crop_variety_master, on_delete=models.SET_NULL,related_name="crop_master_activity_fields",null=True,blank=True)
    def __str__(self) -> str:
        return self.activity.name+" / "+self.name

class DASActivityRecord(BaseModel):
    farmer = models.ForeignKey(to=user,on_delete=models.CASCADE,related_name='das_activity_farmer')
    farm = models.ForeignKey(to=farm,on_delete=models.CASCADE,related_name='das_activity_farm',null=True,blank=True)
    day_of_sowing = models.IntegerField()
    date_of_activity = models.DateField(null=True,blank=True)
    activity = models.ForeignKey(to=ActivityRecord, on_delete=models.CASCADE)
    activity_data=JSONField()
    session = models.ForeignKey(to='pop_manage.Session', on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_records')
    das_crop = models.ForeignKey(to=crop_master, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_crop_snapshot')
    das_variety = models.ForeignKey(to=crop_variety_master, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_variety_snapshot')
    image_url= models.CharField(max_length=200, null=True, blank=True)
    latitude = models.DecimalField(max_digits=16,decimal_places=8,default=0)
    longitude = models.DecimalField(max_digits=16,decimal_places=8,default=0)
    geometry = models2.GeometryField(srid=4326, null=True, blank=True)

    def __str__(self) -> str:
        return self.farmer.full_name+" / "+str(self.day_of_sowing)+" / "+self.activity.name

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and self.farm:
            try:
                if not self.das_crop and getattr(self.farm, 'crop_id', None):
                    self.das_crop = self.farm.crop_id
                if not self.das_variety and getattr(self.farm, 'crop_variety_id', None):
                    self.das_variety = self.farm.crop_variety_id
                if not self.session and getattr(self.farm, 'session', None):
                    self.session = self.farm.session
            except Exception:
                pass

        super().save(*args, **kwargs)

class DASActivityRecordImage(BaseModel):
    activity_record=models.ForeignKey(to=DASActivityRecord,on_delete=models.CASCADE,related_name="das_activity_record_img")
    image_url=models.ImageField(max_length=400)

    def __str__(self) -> str:
        return ""+str(self.activity_record.activity)

class OneTimeRecord(BaseModel):
    name=models.CharField(max_length=200)
    organization= models.ForeignKey(to=organizations,on_delete=models.CASCADE,related_name="otr_org",null=True,blank=True)

    def __str__(self) -> str:
        return self.name

class OneTimeRecordField(BaseModel):
    field=models.ForeignKey(to=OneTimeRecord,on_delete=models.CASCADE,related_name="ot_record")
    organization= models.ForeignKey(to=organizations,on_delete=models.CASCADE,related_name="otr_record_field_org",null=True,blank=True)
    name=models.CharField(max_length=200)
    type=models.CharField(max_length=200,choices=[("string","String"),("int","Integer"),("optional","Optional"),("date","Date")])
    field_possible_value=models.TextField(null=True,blank=True)
    is_required=models.BooleanField(default=True)
    status= models.BooleanField(default=True)


    def __str__(self) -> str:
        return self.field.name+" / "+self.name


class OTRFarmer(BaseModel):
    farmer=models.ForeignKey(to=user,on_delete=models.CASCADE)
    farm = models.ForeignKey(to=farm,on_delete=models.CASCADE,related_name='otr_farmer_farm',null=True,blank=True)
    record_type=models.ForeignKey(to=OneTimeRecord,on_delete=models.CASCADE)
    record_data=JSONField()

    def __str__(self) -> str:
        return self.farmer.full_name+" / "+self.record_type.name

class StatusHandle(BaseModel):
    name=models.CharField(max_length=300)

    def __str__(self) -> str:
        return self.name



class TaskBD(BaseModel):
    task_name=models.CharField(max_length=200)
    sub_task_size=models.IntegerField(default=1)
    assigned_by=models.ForeignKey(to=user,on_delete=models.CASCADE,related_name="assigned_by_task")
    assigned_to=models.ForeignKey(to=user,on_delete=models.CASCADE,related_name="assigned_to_task")
    status =models.CharField(max_length=200,choices=[("0","Pending"),("1","In Progress"),("2","Completed")])
    status_task=models.ForeignKey(to=StatusHandle,on_delete=models.SET_NULL,blank=True,null=True)
    custom_form_data=JSONField(null=True,blank=True)
    custom_form=models.ForeignKey(to='core.CustomForm',on_delete=models.SET_NULL,related_name="custom_form_task",null=True,blank=True)
    
    def __str__(self) -> str:
        return self.task_name

class SubTaskBD(BaseModel):
    taskbd=models.ForeignKey(to=TaskBD,on_delete=models.CASCADE,related_name="task_subtask")
    created_by=models.ForeignKey(to=user,on_delete=models.CASCADE,related_name="created_by_task",null=True,blank=True)
    date_time_of_activity=models.DateTimeField()
    title_of_activity=models.CharField(max_length=300)
    description=models.TextField(blank=True,null=True)
    latitude = models.DecimalField(max_digits=16,decimal_places=8,default=0)
    longitude = models.DecimalField(max_digits=16,decimal_places=8,default=0)
    status =models.CharField(max_length=200,choices=[("0","Pending"),("1","In Progress"),("2","Completed")])
    custom_form_data=JSONField(null=True,blank=True)
    custom_form=models.ForeignKey(to='core.CustomForm',on_delete=models.SET_NULL,related_name="custom_form_sub_task",null=True,blank=True)
    def __str__(self) -> str:
        return self.title_of_activity

class SubTaskImage(BaseModel):
    subtask=models.ForeignKey(to=SubTaskBD,on_delete=models.CASCADE,related_name="subtask_subtask_img")
    image_url=models.ImageField(max_length=400)

    def __str__(self) -> str:
        return ""+str(self.id)
    
class FollowUpCalendar(BaseModel):
    subtask=models.ForeignKey(to=SubTaskBD,on_delete=models.CASCADE,related_name="subtask_followup_calendar")
    date=models.DateTimeField()
   

class Thread(BaseModel):
    thread_id = models.CharField(max_length=255, unique=True,null=True,blank=True)
    assistant_id = models.CharField(max_length=255)
    farmer=models.ForeignKey(to=user,on_delete=models.CASCADE,related_name='farmer_thread')
    farm = models.ForeignKey(to=farm,on_delete=models.CASCADE,related_name='farm_thread',null=True,blank=True)



class ExternalClient(BaseModel):
    name= models.CharField(max_length=255,)
    token= models.CharField(max_length=555, unique=True)
    email= models.CharField(max_length=255, unique=True)
    available_count=models.IntegerField(default=0)
    assistant_id=models.CharField(max_length=255,unique=True,blank=True,null=True)
    openai_secret_key=models.CharField(max_length=1500,unique=True,blank=True,null=True)
    
    def __init__(self,*args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.previous_openai_secret_key=self.openai_secret_key
        

    def save(self, *args, **kwargs):
        if self.openai_secret_key and self.previous_openai_secret_key != self.openai_secret_key:
                self.openai_secret_key = self.encrypt_value(self.openai_secret_key)
        
        super().save(*args, **kwargs)
    
    def encrypt_value(self, value):
        return signing.dumps(value)

    def decrypt_value(self, encrypted_value):
        try:
            return signing.loads(encrypted_value)
        except signing.BadSignature:
            # If decryption fails, return the original value
            return encrypted_value

    def get_assistant_id(self):
        return self.decrypt_value(self.assistant_id)

    def get_openai_secret_key(self):
        return self.decrypt_value(self.openai_secret_key)

    def __str__(self):
        return self.name

class ExternalThread(BaseModel):
    thread_id = models.CharField(max_length=255, unique=True)
    assistant_id = models.CharField(max_length=255)
    external_client_id=models.ForeignKey(to=ExternalClient,on_delete=models.CASCADE,related_name='farmer_thread')
    image=models.CharField(max_length=500, null=True,blank=True)
    lat=models.DecimalField(max_digits=16,decimal_places=8,default=0)
    long=models.DecimalField(max_digits=16,decimal_places=8,default=0)
    language=models.CharField(max_length=100, default="English")
    crop_name=models.CharField(max_length=100, null=True, blank=True)
    structured_response = models.JSONField(null=True, blank=True)
    raw_openai_response = models.JSONField(null=True, blank=True)
    run_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self) -> str:
        return self.thread_id+" / "+self.assistant_id


class InternalThread(BaseModel):

    thread_id = models.CharField(max_length=255, unique=True)

    user = models.ForeignKey(to=user,
        on_delete=models.CASCADE,
        related_name="threads_user"
    )

    image = models.CharField(max_length=500, null=True, blank=True)

    lat = models.DecimalField(max_digits=16, decimal_places=8, default=0)
    long = models.DecimalField(max_digits=16, decimal_places=8, default=0)

    language = models.CharField(max_length=100, default="English")

    crop_name = models.CharField(max_length=100, null=True, blank=True)

    structured_response = models.JSONField(null=True, blank=True)
    raw_openai_response = models.JSONField(null=True, blank=True)

    run_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.thread_id} / internal"

class ExternalCropRemedy(BaseModel):
    thread_id=models.CharField(max_length=500, unique=True)
    run_id=models.CharField(max_length=500,null=True,blank=True)
    crop_name = models.CharField(max_length=500,)
    disease_name = models.CharField(max_length=500)
    thread_response=JSONField(null=True,blank=True)
    response = models.JSONField(null=True,blank=True)



class APICalledAnalytic(BaseModel):
    external_client=models.ForeignKey(to=ExternalClient,on_delete=models.CASCADE,related_name='analyticapi_external')
    external_thread=models.ForeignKey(to=ExternalThread,on_delete=models.CASCADE,related_name='analyticapi_external_thread')
    

class FarmReport(BaseModel):
    farm=models.ForeignKey(to=farm,on_delete=models.CASCADE,related_name="farm_farm_report")
    vegetation_score=models.IntegerField(default=0)
    yield_score=models.IntegerField(default=0)
    stress_score=models.IntegerField(default=0)
    irrigation_score=models.IntegerField(default=0)
    soil_score=models.IntegerField(default=0)
    cibil_score=models.IntegerField(default=0)
    overall_credit_score=models.IntegerField(default=0)
    seasonal_report=JSONField(null=True,blank=True)


class RequestForFarmCredit(BaseModel):
    farm=models.ForeignKey(to=farm,on_delete=models.CASCADE,related_name="farm_request_farm_report")
    status=models.BooleanField(default=False)




class Project(BaseModel):
    name= models.CharField(max_length=300)
    json_data = JSONField(null=True, blank=True)
    custom_form= models.ForeignKey(to='core.CustomForm',on_delete=models.CASCADE,null=True,blank=True)
    created_by= models.ForeignKey(to=user, on_delete=models.CASCADE,related_name="created_project")

    def __str__(self):
        return self.name

class ProjectUser(BaseModel):
    project = models.ForeignKey(to=Project, on_delete=models.CASCADE, related_name="project_user")
    user = models.ForeignKey(to=user, on_delete=models.CASCADE,related_name="user_project")

    def __str__(self):
        return f"{self.user} - {self.project}"

class ProjectTask(BaseModel):
    created_by= models.ForeignKey(to=user,on_delete=models.CASCADE,related_name="created_by_project_task",null=True,blank=True)
    task_name = models.CharField(max_length=300)
    project =  models.ForeignKey(to=Project, on_delete=models.CASCADE, related_name="project_task_user")
    task_type = models.CharField(max_length=200, choices=[("custom","Custom"),("activity","Activity")])
    custom_form= models.ForeignKey(to='core.CustomForm',on_delete=models.SET_NULL,related_name="custom_form_project_task",null=True,blank=True)
    activity_record = models.ForeignKey(to=ActivityRecord, on_delete=models.CASCADE, related_name="project_task_activity_record", null= True, blank=True)
   
    def __str__(self):
        return self.task_name

class ProjectTaskUser(BaseModel):
    assigned_to= models.ForeignKey(to=user,on_delete=models.CASCADE,related_name="assined_to_project_task")
    project_task = models.ForeignKey(to=ProjectTask, on_delete=models.CASCADE, related_name="project_task_user")
    farm = models.ForeignKey(to=farm, on_delete=models.CASCADE,related_name="user_project_task", null=True,blank=True)
    json_data = JSONField(null=True, blank=True)
    status = models.CharField(default="pending", max_length=200,choices=[("pending","Pending"),("reject","Reject"),("complete","Complete")])
    
    def __str__(self):
        return f"{self.assigned_to} - {self.project_task} ({self.status})"
       
import datetime
class SmartFarms(BaseModel):
    farm= models.ForeignKey(to=farm, on_delete=models.CASCADE,related_name="smart_farm_farm")
    next_run= models.DateField(null=True,blank=True)

class FylloFarmData(BaseModel):
    plot_id = models.CharField(max_length=100)

    def __str__(self):
        return self.plot_id

class FarmFylloFarmData(BaseModel):
    farm= models.ForeignKey(to=farm, on_delete=models.CASCADE,related_name="farm_farm_fyllo_farm_data")
    farm_fyllow=models.ForeignKey(to=FylloFarmData,on_delete=models.CASCADE,related_name="farm_fyllo_fyllo_farm_data")

    def __str__(self):
        return self.farm.name+" "+self.farm_fyllow.plot_id
    

from pgvector.django import VectorField
from recordActivity.vector_files.advisory_embeddings import embed_text
from django.utils import timezone


class CropDiseaseAdvisory(BaseModel):
    """
    Stores AI-searchable advisories for crop-disease-pest combinations.
    """
    crop_name = models.CharField(max_length=150)
    disease_or_pest_name = models.CharField(max_length=200)
    stage_of_crop = models.CharField(max_length=200)
    symptom_description = models.TextField()
    causal_organism_or_pest = models.CharField(max_length=200, blank=True, null=True)
    economic_threshold_level = models.CharField(max_length=100, blank=True, null=True)
    remedy_recommendation = models.TextField()

    client = models.ForeignKey(
        ExternalClient, on_delete=models.CASCADE, null=True, blank=True
    )

    embedding = VectorField(null=True, blank=True)  # pgvector field for semantic search



    def save(self, *args, **kwargs):
        """
        Auto-generate embeddings using key text fields.
        """
        combined_text = " ".join(
            filter(
                None,
                [
                    self.crop_name,
                    self.disease_or_pest_name,
                    self.symptom_description,
                    self.causal_organism_or_pest,
                    self.remedy_recommendation,
                ],
            )
        )

        if combined_text:
            embedding_vector = embed_text(combined_text)
            if isinstance(embedding_vector, list) and len(embedding_vector) > 0:
                self.embedding = embedding_vector[0]  # store 1D vector

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.crop_name} - {self.disease_or_pest_name}"



class Training(BaseModel):
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)

    created_by = models.ForeignKey(
        user,
        on_delete=models.CASCADE,
        related_name="created_trainings"
    )

    custom_form = models.ForeignKey(
        'core.CustomForm',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trainings"
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class TrainingExecution(BaseModel):
    training = models.ForeignKey(
        Training,
        on_delete=models.CASCADE,
        related_name="executions"
    )

    conducted_by = models.ForeignKey(
        user,
        on_delete=models.CASCADE,
        related_name="conducted_trainings"
    )
    organization= models.ForeignKey(to=organizations,on_delete=models.CASCADE,null=True,blank=True,related_name="training_execution_organization")

    form_response = models.JSONField(
        null=True,
        blank=True
    )

    conducted_at = models.DateTimeField(auto_now_add=True)

    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.training.title} - {self.conducted_at.date()}"


class TrainingExecutionFarm(BaseModel):
    training_execution = models.ForeignKey(
        TrainingExecution,
        on_delete=models.CASCADE,
        related_name="trained_farms"
    )

    farm = models.ForeignKey(
        farm,
        on_delete=models.CASCADE,
        related_name="training_records"
    )

    class Meta:
        unique_together = ("training_execution", "farm")

    def __str__(self):
        return f"{self.farm} - {self.training_execution}"






class CtQuestions(BaseModel):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    custom_form=models.JSONField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title



class CtQuestionsFarm(BaseModel):
    ct_question = models.ForeignKey(
        CtQuestions,
        on_delete=models.CASCADE,
        related_name="ct_questions_questions_farm"
    )
    added_by=models.ForeignKey(
            user,
            on_delete=models.CASCADE,
            related_name="ct_questions_added_by",
            null=True,blank=True
        )
    user=models.ForeignKey(
        user,
        on_delete=models.CASCADE,
        related_name="ct_questions_user"
    )
    farm = models.ForeignKey(
        farm,
        on_delete=models.CASCADE,
        related_name="ct_questions_farm"
    )
    

    response = models.JSONField(
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("submitted", "Submitted")],
        default="pending",
        db_index=True,
    )

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.full_name} - {self.ct_question.title}"



class DroneSprayActivity(BaseModel):
    
    farm = models.ForeignKey("app_farm.farm",on_delete=models.CASCADE,related_name="drone_spray_activities",db_index=True,help_text="Farm where spray is requested/performed")
    farmer = models.ForeignKey(user,on_delete=models.CASCADE,related_name="drone_spray_activities",null=True,blank=True,help_text="Auto-populated from farm.user")
    organization = models.ForeignKey("app_farm.organizations",on_delete=models.CASCADE,related_name="drone_spray_activities",db_index=True,help_text="Auto-populated from farm.org_id")
    
    # ========== LOCATION (Auto-populated) ==========
    state = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, db_index=True, blank=True, null=True)
    tehsil = models.CharField(max_length=100, blank=True, null=True)
    village = models.CharField(max_length=150, blank=True, null=True)
    
    # ========== CROP & AREA ==========
    crop = models.CharField(max_length=150, blank=True, null=True)
    area_total = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True,help_text="Total farm area in acres (auto-populated from farm.total_area if available)")
    area_unit = models.CharField(max_length=100,null=True,blank=True,choices=LAND_SIZE_UNIT,help_text="Unit of area measurement (auto-populated from farm.area_unit)")
    
    # ========== DYNAMIC FORM SUPPORT ==========
    custom_form = models.ForeignKey("core.CustomForm",on_delete=models.PROTECT,related_name="drone_spray_activities",null=True,blank=True,help_text="Dynamic form for spray-type specific fields")
    form_response = models.JSONField(default=dict,blank=True,help_text="""        
        IMPORTANT: Only spray_type is stored here (REQUIRED, managed via CustomForm).
        Example:
        {
            "spray_type": "Insecticide",  // REQUIRED
        }
        """
    )
    
    # ========== REQUEST DETAILS (Booking Phase) ==========
    preferred_week_start = models.DateField(null=True,blank=True,db_index=True,help_text="Start of preferred week for spraying (booking phase)")
    preferred_week_end = models.DateField(null=True,blank=True,db_index=True,help_text="End of preferred week for spraying (booking phase)")
    
    # ========== SPRAY EXECUTION DETAILS (Actual Execution Phase) ==========
    spray_cycle = models.CharField(max_length=50, null=True, blank=True)
    date_of_spraying = models.DateField(db_index=True,null=True,blank=True,help_text="ACTUAL date of spraying (filled by CVRP after execution)")
    crop_stage = models.CharField(max_length=100, null=True, blank=True)
    pest_or_activity = models.CharField(max_length=255, null=True, blank=True)
    products = models.JSONField(default=list,blank=True,help_text="Products used: [{'product_name': 'Marshal', 'dosage': 250, 'unit': 'ml'}]")
    area_sprayed = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True,help_text="Actual area sprayed in acres (filled by CVRP after execution)")
    area_sprayed_unit = models.CharField(max_length=100,null=True,blank=True,choices=LAND_SIZE_UNIT,help_text="Unit of area sprayed measurement (defaults to area_unit)")

    # ========== STATUS & WORKFLOW ==========
    status = models.CharField(max_length=20,choices=DRONE_SPRAY_STATUS,default="PENDING",db_index=True)
    
    # ========== UNIQUE REFERENCE ID ==========
    reference_id = models.CharField(max_length=150,unique=True,null=True,blank=True,db_index=True,editable=False,help_text="Unique reference ID for external systems")
    
    # ========== GEOJSON & SPATIAL DATA ==========
    geojson_file = models.FileField(upload_to="drone_spray/geojson/%Y/%m/",null=True,blank=True,help_text="GeoJSON file URL from drone vendor")
    spray_area_coordinates = models.JSONField(null=True,blank=True,help_text="GeoJSON features array with spray area coordinates for frontend map display")
    geojson_geometry = models2.GeometryField(srid=4326,null=True,blank=True,spatial_index=True,help_text="Parsed geometry from GeoJSON for spatial queries")
    geojson_area = models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True,help_text="Calculated area from GeoJSON in acres")
    
    # ========== WEBHOOK INTEGRATION ==========
    webhook_payload = models.JSONField(null=True, blank=True)
    webhook_reference_id = models.CharField(max_length=150,null=True,blank=True,db_index=True,unique=True)
    webhook_received_at = models.DateTimeField(null=True, blank=True)
    webhook_status = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    
    # ========== REQUEST & APPROVAL WORKFLOW ==========
    requested_by = models.ForeignKey(
        user,
        on_delete=models.PROTECT,
        related_name="requested_drone_sprays",
        null=True,
        blank=True,
        help_text="User who created the request"
    )
    rejection_reason = models.TextField(null=True, blank=True)
    rejected_by = models.ForeignKey(user,on_delete=models.SET_NULL,null=True,blank=True,related_name="rejected_drone_sprays")
    rejected_at = models.DateTimeField(null=True, blank=True)
    
    # ========== AUDIT TRAIL ==========
    created_by = models.ForeignKey(user,on_delete=models.CASCADE,related_name="created_drone_spray_activities")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "status", "created_at"]),
            models.Index(fields=["district", "status"]),
            models.Index(fields=["date_of_spraying"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["reference_id"]),
        ]
        verbose_name = "Drone Spray Activity"
        verbose_name_plural = "Drone Spray Activities"



    def populate_from_farm(self):
        """Auto-populate fields from farm"""
        if not self.farm_id:
            return
        
        try:
            farm = self.farm
        except Exception:
            return
        
        if not self.organization:
            self.organization = farm.org_id if hasattr(farm, 'org_id') else farm.organization
        
        if not self.farmer:
            self.farmer = farm.user
        
        if not self.state:
            self.state = farm.farm_state
        
        if not self.district:
            self.district = farm.farm_district
        
        if not self.tehsil:
            self.tehsil = farm.farm_taluka
        
        if not self.village:
            self.village = farm.farm_village
        
        if not self.crop and farm.crop_id:
            self.crop = farm.crop_id.crop_name
        
        if self.area_total is None:
            self.area_total = farm.total_area
        
        if not self.area_unit:
            self.area_unit = farm.area_unit
        
        if not self.area_sprayed_unit and self.area_unit:
            self.area_sprayed_unit = self.area_unit

    def save(self, *args, **kwargs):
        """Auto-populate and handle state transitions"""
        if self.farm_id:
            self.populate_from_farm()
        
        # Generate unique reference ID on creation
        if not self.pk and not self.reference_id:
            from django.utils.crypto import get_random_string
            org_id = self.organization.id if self.organization else '0'
            self.reference_id = f"DSA{org_id}{get_random_string(8).upper()}"
        
        # Set completed timestamp
        if self.status == "COMPLETED" and not self.completed_at:
            self.completed_at = timezone.now()
        
        # Auto-populate created_by from requested_by if not set
        if not self.pk and not self.created_by and self.requested_by:
            self.created_by = self.requested_by
        
        super().save(*args, **kwargs)

    def __str__(self):
        spray_date = self.date_of_spraying or 'No date'
        return f"{self.reference_id or f'DSA-{self.id}'} | {self.farmer} | {spray_date}"
    
    def get_spray_type(self):
        """Get spray type from form_response (CustomForm field)."""
        return self.form_response.get('spray_type', 'N/A')
