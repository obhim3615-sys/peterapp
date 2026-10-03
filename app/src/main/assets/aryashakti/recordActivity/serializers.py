from rest_framework import serializers
from .models import *
from app_farm.utils.helper import remove_media
from core.serializer import GetCustomeFormSerializer
class ActivityFieldsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActivityFields
        fields="__all__"

from django.db.models import Q
class ActivitySerializer(serializers.ModelSerializer):
    activity_field= serializers.SerializerMethodField('get_activity_field')

    def get_activity_field(self,obj):
        crop_id = self.context.get('crop_id', None)  # Get crop_id from context if provided
        
        activity_data= obj.activity_data.filter(status=True).all()
    
        if crop_id is not None:
            activity_data = activity_data.filter(Q(crop__isnull=True) | Q(crop_id=crop_id))
        
        return ActivityFieldsSerializer(activity_data, many=True).data
        # return ActivityFieldsSerializer(obj.activity_data.filter(status=True,organization_id=organization).all(),many=True).data
    
    def to_representation(self, instance):
        return remove_media(self,instance,ActivitySerializer,'image')

    class Meta:
        model = ActivityRecord
        fields=['id','name','image','order_value','activity_field','created_at','updated_at']

class DASActivityRecordImageSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return remove_media(self,instance,DASActivityRecordImageSerializer,'image_url')
    
    class Meta:
        model = DASActivityRecordImage
        fields="__all__"

class DASActivityRecordSerializer(serializers.ModelSerializer):
    activity_image = serializers.SerializerMethodField('get_activity_image')
    farm_name = serializers.SerializerMethodField('get_farm_name')
    activity_name = serializers.SerializerMethodField('get_activity_name')  

    def get_activity_image(self,obj):
        data=obj.das_activity_record_img.all()

        if data:
            data=DASActivityRecordImageSerializer(data,many=True).data
        return data
    
    def get_activity_name(self, obj):
        return obj.activity.name if obj.activity else ""   
    
    def get_farm_name(self,obj):
        if obj.farm:
            return obj.farm.name
        return ""
    
    class Meta:
        model = DASActivityRecord
        fields=["id","created_at","updated_at","day_of_sowing","date_of_activity","activity_data","image_url","latitude","longitude","geometry","farmer","activity","activity_image","farm_name","activity_name"]


class DASActivityRecordCountSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField('get_total')
    activity_name = serializers.SerializerMethodField('get_activity_name')

    def get_activity_name(self,obj):        
        return obj['activity_name']

    def get_total(self,obj):
        return obj['total']
    
    class Meta:
        model = DASActivityRecord
        fields=['total','activity_name','activity_id']

class OneTimeRecordFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = OneTimeRecordField
        fields="__all__"


class OneTimeRecordSerializer(serializers.ModelSerializer):
    ot_record= serializers.SerializerMethodField('get_ot_record')

    def get_ot_record(self,obj):
        return OneTimeRecordFieldSerializer(obj.ot_record.filter(status=True).all(),many=True).data
   
    class Meta:
        model=OneTimeRecord
        fields=['id','name','ot_record','created_at']


class OTRFarmerSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTRFarmer
        fields="__all__"




class StatusHandleSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusHandle
        fields="__all__"



class TaskBDSerializer(serializers.ModelSerializer):
    total_subtasks = serializers.SerializerMethodField('get_total_subtasks')
    last_subtask_title = serializers.SerializerMethodField('get_last_subtask_title')
    custom_form_icon = serializers.SerializerMethodField('get_custom_form_icon')
    status_task_obj = serializers.SerializerMethodField('get_status_task_obj')

    def get_total_subtasks(self,obj):
        return obj.total_subtasks
    
    def get_last_subtask_title(self,obj):
        return obj.last_subtask_title
    
    def get_custom_form_icon(self,obj):
        form_data= obj.custom_form
        if form_data:
            form_data= GetCustomeFormSerializer(form_data).data
            return form_data['image_url']
        return None
    
    def get_status_task_obj(self,obj):
        data={}
        if obj:
            data= StatusHandleSerializer(obj.status_task)
            if data:
                data=data.data
        return data
    
    class Meta:
        model = TaskBD
        fields=['id','task_name','sub_task_size','custom_form_data','custom_form','custom_form_icon','total_subtasks','last_subtask_title','status_task_obj','status','created_at','updated_at']


class SubTaskImageSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        return remove_media(self,instance,SubTaskImageSerializer,'image_url')
    
    class Meta:
        model = SubTaskImage
        fields="__all__"


class SubTaskBDSerializer(serializers.ModelSerializer):
    subtask_image = serializers.SerializerMethodField('get_subtask_image')
    created_by_name = serializers.SerializerMethodField('get_created_by_name')

    
    def get_created_by_name(self,obj):
        return obj.created_by.full_name


    def get_subtask_image(self,obj):
        data=obj.subtask_subtask_img.all()

        if data:
            data=SubTaskImageSerializer(data,many=True).data
        return data
    
    class Meta:
        model = SubTaskBD
        fields=['id','taskbd','custom_form_data','custom_form_id','created_by','created_by_name','subtask_image','date_time_of_activity','title_of_activity','description','latitude','longitude','status']


class FollowUpCalendarSerializer(serializers.ModelSerializer):
    task = serializers.SerializerMethodField('get_task')
    
    def get_task(self,obj):
        return {
                "task_name":obj.subtask.taskbd.task_name,
                "task_id":obj.subtask.taskbd.id,
                "custom_form_id":obj.subtask.taskbd.custom_form_id
                }
    
   
    
    class Meta:
        model =FollowUpCalendar
        fields =['id','task','date']

class FarmReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmReport
        fields = '__all__'



class ProjectTaskSerializer(serializers.ModelSerializer):
    activity_details = serializers.SerializerMethodField('get_activity_details')
    static_fields = serializers.SerializerMethodField('get_static_fields')
    
    def get_activity_details(self,obj):
        if obj.activity_record:
            activity=ActivitySerializer(obj.activity_record, many=False)
            if activity:
                return activity.data

        return None
    def get_static_fields(self,obj):
        return [
            #{"name":"day_after_sowing","type":"int", "is_required":True },
            {"name":"date_of_activity","type":"date","is_required":True},
            {"name":"image","type":"string","is_required":False}
        ]
    class Meta:
        model = ProjectTask
        fields = ['id','created_at','updated_at','task_name','task_type','project','custom_form','activity_record','activity_details','static_fields']
        depth = 1


class ProjectTaskUserSerializer(serializers.ModelSerializer):
    farm_name= serializers.SerializerMethodField('get_farm_name')
    project_task_data= serializers.SerializerMethodField('get_project_task_data')
    
 
    def get_farm_name(self,obj):
        return obj.farm.name
    
    def get_project_task_data(self,obj):
        if obj:
            return ProjectTaskSerializer(obj.project_task).data
    class Meta:
        model = ProjectTaskUser
        fields = ['id','created_at','updated_at','json_data','status','project_task_data','farm_name','farm']
        depth = 1



class TrainingExecutionSerializer(serializers.ModelSerializer):
    training_title = serializers.CharField(source="training.title", read_only=True)
    # farms = serializers.SerializerMethodField()

    class Meta:
        model = TrainingExecution
        fields = [
            "id",
            "training",
            "training_title",
            "form_response",
            "conducted_at",
            "remarks",
            # "farms"
        ]

    # def get_farms(self, obj):
    #     return list(
    #         obj.farms.values_list("farm_id", flat=True)
    #     )



class TrainingFormSerializer(serializers.ModelSerializer):
    custom_form = GetCustomeFormSerializer()

    class Meta:
        model = Training
        fields = [
            "id",
            "title",
            "custom_form"
        ]


class TrainingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Training
        fields = "__all__"
        # depth=1


class CtQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CtQuestions
        fields = ["id", "title", "description", "custom_form", "is_active"]


class CtQuestionsFarmSerializer(serializers.ModelSerializer):
    ct_question_title = serializers.CharField(source="ct_question.title", read_only=True)

    class Meta:
        model = CtQuestionsFarm
        fields = ["id", "ct_question", "ct_question_title", "added_by", "user", "farm", "response", "status", "created_at", "updated_at"]


class DroneSprayActivitySerializer(serializers.ModelSerializer):
    custom_form_details = serializers.SerializerMethodField('get_custom_form_details')
    
    def get_custom_form_details(self, obj):
        if obj.custom_form:
            return GetCustomeFormSerializer(obj.custom_form).data
        return None
    
    class Meta:
        model = DroneSprayActivity
        fields = "__all__"
        read_only_fields = ('reference_id', 'created_at', 'updated_at', 'completed_at', 'area_unit', 'area_sprayed_unit')

    def validate(self, attrs):
        """Validate DroneSprayActivity data"""
        # Validate farm is required
        farm = attrs.get("farm", getattr(self.instance, "farm", None))
        if not farm:
            raise serializers.ValidationError({
                "farm": "Farm is required."
            })
        
        status = attrs.get("status", getattr(self.instance, "status", None))
        form_response = attrs.get("form_response", getattr(self.instance, "form_response", {}))
        
        # CRITICAL: Validate spray_type is in form_response (REQUIRED - managed via CustomForm)
        if not form_response.get('spray_type'):
            raise serializers.ValidationError({
                "form_response": "spray_type is required in form_response."
            })
        
        # Validate preferred week dates
        preferred_week_start = attrs.get("preferred_week_start", getattr(self.instance, "preferred_week_start", None))
        preferred_week_end = attrs.get("preferred_week_end", getattr(self.instance, "preferred_week_end", None))
        
        if preferred_week_start and preferred_week_end:
            if preferred_week_end < preferred_week_start:
                raise serializers.ValidationError({
                    "preferred_week_end": "Week end date must be after start date"
                })
            
            # Validate reasonable window
            delta = (preferred_week_end - preferred_week_start).days
            if delta > 14:
                raise serializers.ValidationError({
                    "preferred_week_end": "Preferred window cannot exceed 2 weeks"
                })

        # Validate custom form required fields and field values
        custom_form = attrs.get("custom_form", getattr(self.instance, "custom_form", None))
        if custom_form and form_response:
            from core.models import CustomFormField
            form_fields = CustomFormField.objects.filter(
                custom_form=custom_form,
                status=True
            )
            
            missing_fields = []
            invalid_values = []
            
            for field in form_fields:
                field_name = field.name
                field_value = form_response.get(field_name)
                
                # Check required fields
                if field.is_required and not field_value:
                    missing_fields.append(field_name)
                    continue
                
                # Validate field values against possible values (for 'optional' type fields)
                if field_value and field.field_possible_value and field.type == 'optional':
                    allowed_values = [v.strip() for v in field.field_possible_value.split(',')]
                    if field_value not in allowed_values:
                        invalid_values.append({
                            'field': field_name,
                            'value': field_value,
                            'allowed': allowed_values
                        })
            
            if missing_fields:
                raise serializers.ValidationError({
                    "form_response": f"Required fields missing: {', '.join(missing_fields)}"
                })
            
            if invalid_values:
                error_messages = []
                for item in invalid_values:
                    error_messages.append(
                        f"{item['field']}: '{item['value']}' is not valid. "
                        f"Allowed values: {', '.join(item['allowed'])}"
                    )
                raise serializers.ValidationError({
                    "form_response": " | ".join(error_messages)
                })
        
        # Validate products format (static field)
        products = attrs.get('products', getattr(self.instance, 'products', None))
        
        if products and not isinstance(products, list):
            raise serializers.ValidationError({
                "products": "Products must be a list."
            })
        
        for product in (products or []):
            if not isinstance(product, dict):
                raise serializers.ValidationError({
                    "products": "Each product must be an object."
                })
            required = {"product_name", "dosage", "unit"}
            if not required.issubset(product.keys()):
                raise serializers.ValidationError({
                    "products": "Each product must contain product_name, dosage and unit."
                })

        # Completion validation (static fields)
        if status == "COMPLETED":
            area_sprayed = attrs.get('area_sprayed', getattr(self.instance, 'area_sprayed', None))
            date_of_spraying = attrs.get('date_of_spraying', getattr(self.instance, 'date_of_spraying', None))
            
            if not products:
                raise serializers.ValidationError({
                    "products": "Products required for completed spray."
                })

            if not area_sprayed:
                raise serializers.ValidationError({
                    "area_sprayed": "Area sprayed required for completed spray."
                })
            
            if not date_of_spraying:
                raise serializers.ValidationError({
                    "date_of_spraying": "Spray date required for completed spray."
                })
        
        # Validate area doesn't exceed farm area
        area_sprayed = attrs.get('area_sprayed', getattr(self.instance, 'area_sprayed', None))
        area_total = attrs.get('area_total', getattr(self.instance, 'area_total', None))
        
        if area_sprayed and area_total:
            if float(area_sprayed) > float(area_total):
                raise serializers.ValidationError({
                    "area_sprayed": f"Area sprayed ({area_sprayed}) cannot exceed farm area ({area_total})"
                })
        
        # Status transition validation - cannot change status of completed activity
        if self.instance and self.instance.pk:
            if self.instance.status == "COMPLETED" and status != "COMPLETED":
                raise serializers.ValidationError({
                    "status": "Cannot change status of completed activity"
                })

        return attrs