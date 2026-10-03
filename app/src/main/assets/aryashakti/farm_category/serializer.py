from rest_framework import serializers
from .models import *
from app_farm.models import farm

class HeadingAndAdvisorySerializer(serializers.ModelSerializer):
    class Meta:
        model = HeadingAndAdvisory
        fields = ('heading','advisory')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id','color','healthy','stress','damaged')

class FarmCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmsCategory
        fields = ('satelite_date',)

class FarmsSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField('get_date')

    def get_date(self,obj):
        if hasattr(obj,'category_farm'):
            return FarmCategorySerializer(obj.category_farm,many=False).data['satelite_date']
        else:
            return None
    class Meta:
        model = farm
        fields = ('id','date')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('color',)

class BioticFarmCategoryDetailSerializer(serializers.ModelSerializer):
    color = serializers.SerializerMethodField('get_color')

    def get_color(self,obj):
        if hasattr(obj,'biotic_category'):
            return CategorySerializer(obj.biotic_category,many=False).data['color']
        else:
            return None
    class Meta:
        model = FarmsCategory
        fields = ('biotic_map','biotic_category','color','whole_map')

class AbioticFarmCategoryDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmsCategory
        fields = ('abiotic_map','abiotic_category','boundary')

class MoistureFarmCategoryDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmsCategory
        fields = ('moisture_map','moisture_category','boundary')

class MicroNutrientFarmCategoryDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = FarmsCategory
        fields = ('micro_nutrient_map','micro_nutrient_category','boundary')

class FarmsDetailSerializer(serializers.ModelSerializer):
    stress_data = serializers.SerializerMethodField('get_stress_data')
    local_boundary = serializers.SerializerMethodField('get_local_boundary')

    def get_local_boundary(self,obj):
        if hasattr(obj,'category_farm'):
            return obj.category_farm.boundary
        return None

    def get_stress_data(self,obj):
        if hasattr(obj,'category_farm'):
            stress_type = self.context.get('stress_type')
            if stress_type == 'biotic':
                return BioticFarmCategoryDetailSerializer(obj.category_farm,many=False).data
            elif stress_type == 'abiotic':
                return AbioticFarmCategoryDetailSerializer(obj.category_farm,many=False).data
            elif stress_type == 'micro_nutrient':
                return MicroNutrientFarmCategoryDetailSerializer(obj.category_farm,many=False).data
            elif stress_type == 'moisture':
                return MoistureFarmCategoryDetailSerializer(obj.category_farm,many=False).data
        else:
            return None
    class Meta:
        model = farm
        fields = ('id','farm_taluka','farm_district','latitude','longitude','stress_data','local_boundary')


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields=['id','latitude','longitude','name','address','state','total_capacity']

class WarehouseSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields=['id','name']



class BuyerSellerDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerSellerDetail
        fields="__all__"


class UserInterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInterest
        fields="__all__"

    
class WarehouseIndiaClustureSerializer(serializers.ModelSerializer):
    class Meta:
        model = WarehouseIndiaClusture
        fields = '__all__'
    

class SixtyKmClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SixtyKmCluster
        fields = ("ogc_fid", "name", "description", "wkb_geometry")

class TenKmClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TenKmCluster
        fields = ("ogc_fid", "name", "description", "wkb_geometry")


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = (
            "id",
            "parent_id",
            "type",
            "name",
            "status",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
            "code",
            "alpha_code",
            "sap_code",
        )