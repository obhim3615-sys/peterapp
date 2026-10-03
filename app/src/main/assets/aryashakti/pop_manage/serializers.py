from rest_framework import serializers
from .models import *
from app_farm.utils.helper import remove_media
from recordActivity.serializers import ActivityFieldsSerializer
from recordActivity.models import DASActivityRecord

class ActivityPOPSerializer(serializers.ModelSerializer):
    activity_field = serializers.SerializerMethodField()
    activity_name = serializers.CharField(source="activity_records_id.name", read_only=True)
    activity_status = serializers.SerializerMethodField()  # renamed from is_activity_added

    def get_activity_field(self, obj):
        # If you want related fields with status=True
        if hasattr(obj.activity_records_id, "activity_data"):
            return ActivityFieldsSerializer(
                obj.activity_records_id.activity_data.filter(status=True), many=True
            ).data
        return []

    def get_activity_status(self, obj):
        """
        Returns both:
        - count of times activity was recorded
        - whether activity has been completed (>=1)
        - whether it was completed within POP's from_das - to_das window
        """

        farm_id = self.context.get("farm_id")
        sowing_date = self.context.get("sowing_date")

        if not (farm_id and sowing_date):
            return {"count": 0, "is_completed": False, "within_time": False}

        # Instead of hitting DB each time, use context cache
        das_activities = self.context.get("das_activities", {}).get(obj.activity_records_id_id, [])

        count = len(das_activities)

        # check if any was completed in window
        within_time = any(
            obj.from_das <= (act.date_of_activity - sowing_date).days <= obj.to_das
            for act in das_activities
        )

        return {
            "count": count,
            "is_completed": count > 0,
            "within_time": within_time,
        }

    class Meta:
        model = ActivityPOP
        fields = [
            "id", "activity_field", "activity_status",
            "from_das", "to_das", "crop", "jsondata",
            "activity_records_id", "activity_name"
        ]



class ActivityPOPSecondSerializer(serializers.ModelSerializer):
    class Meta:
        model=ActivityPOP
        fields = "__all__"
        depth=1

class StageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stage
        fields = "__all__"

class SubStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubStage
        fields = "__all__"

class FarmSoilTestedSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = FarmSoilTested
        fields=["id","farm_value",'sample_id','file_response','json_response']
    

