from rest_framework import serializers
from app_farm.utils.constants import FARM_TYPES

class GetFarmDetails(serializers.Serializer):
    farm_id = serializers.IntegerField(required=True)
    language = serializers.IntegerField(required=True)
    type = serializers.ChoiceField(choices=FARM_TYPES,required=False,allow_null=True,allow_blank=True)