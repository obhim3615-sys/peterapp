from rest_framework import serializers


class DASActivitiyValidator(serializers.Serializer):
    user_id=serializers.IntegerField(required=True)
    activity_id=serializers.IntegerField(required=True)
    #day_of_sowing=serializers.IntegerField(required=True)
    data=serializers.JSONField(required=True)
    date_of_activity=serializers.DateField(required=True)

class UpdateDASActivityValidator(serializers.Serializer):
    activity_id = serializers.IntegerField(required=False)
    farm_id = serializers.IntegerField(required=False)
    date_of_activity = serializers.DateField(required=False)
    data = serializers.JSONField(required=False)
    latitude = serializers.DecimalField(max_digits=16, decimal_places=8, required=False)
    longitude = serializers.DecimalField(max_digits=16, decimal_places=8, required=False)
    delete_existing_images = serializers.BooleanField(required=False)

class OTRecordValidator(serializers.Serializer):
    user_id=serializers.IntegerField(required=True)
    record_type=serializers.IntegerField(required=True)
    data=serializers.JSONField(required=True)


class TaskBDValidator(serializers.Serializer):
    task_name=serializers.CharField(required=True)
    sub_task_size=serializers.IntegerField(required=True)

class UpdateTaskBDValidator(serializers.Serializer):
    task_id=serializers.IntegerField(required=True)
    status=serializers.IntegerField(required=True)
    
class SubTaskBDValidator(serializers.Serializer):    
    taskid=serializers.IntegerField(required=True)
    date_time_of_activity=serializers.DateTimeField(required=True)
    title_of_activity=serializers.CharField(required=True)
    latitude=serializers.DecimalField(max_digits=16,decimal_places=8,required=True)
    longitude=serializers.DecimalField(max_digits=16,decimal_places=8,required=True)


class CropIdentificationValidator(serializers.Serializer):
    file = serializers.FileField(required=True)

    def validate_file(self, value):
        """
        Custom validation for the uploaded file.
        For example, you can validate the file size, type, etc.
        """
        # Example: Validate file size (limit to 5MB)
        max_file_size = 5 * 1024 * 1024  # 5 MB
        if value.size > max_file_size:
            raise serializers.ValidationError("File size should not exceed 5MB.")
        
        # Example: Validate file type (allow only specific types)
        allowed_file_types = ['application/pdf', 'image/jpeg', 'image/png']
        if value.content_type not in allowed_file_types:
            raise serializers.ValidationError("Unsupported file type. Allowed types are: PDF, JPEG, PNG.")
        
        return value



class ProjectTaskValidator(serializers.Serializer):
    task_name = serializers.CharField(max_length=300)
    task_type = serializers.ChoiceField(choices=[("custom", "Custom"), ("activity", "Activity")])
    custom_form_id = serializers.IntegerField(required=False, allow_null=True)
    date_of_task = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", input_formats=["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ"], required=False, allow_null=True)


class CtQuestionResponseValidator(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    question_id = serializers.IntegerField(required=True)
    farm_id = serializers.IntegerField(required=True)
    response = serializers.JSONField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=[("pending", "Pending"), ("submitted", "Submitted")], required=False, allow_null=True)
    user_id = serializers.IntegerField(required=False, allow_null=True)
