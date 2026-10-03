from django.contrib import admin

# Register your models here.
from . import models
from import_export.admin import ExportActionMixin, ImportMixin


# Register your models here.
class CategoryAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','status','trigger','healthy','stress','damaged','color','created_at','updated_at')

class HeadingAndAdvisoryAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','heading','advisory','category','language','created_at','updated_at')
    list_filter= ('language','category')

class FarmsCategoryAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','farm','satelite_date','biotic_category','abiotic_category','moisture_category','micro_nutrient_category','created_at','updated_at')
    search_fields = ('farm__name','farm__farmer_contact')
    #list_filter= ('farm__org_id__org_name',)
    autocomplete_fields = ('farm',)


class CeleryTaskStatusAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        'id',
        'task_id',
        'description',
        'status',
        'input_csv',
        'batch_size',
        'total_processed',
        'updated_count',
        'inserted_count',
        'skipped_count',
        'failed_count',
        'created_at',
        'updated_at',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('task_id', 'description', 'input_csv')

class CropStageAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','name','crop','created_at','updated_at')
    list_filter= ('crop',)
    search_fields = ('name',)

class CropDiseaseAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','name','created_at','updated_at')
    search_fields = ('name',)

class DiseaseScoringAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','stage','disease','rank','min_value','max_value','whole_plant','leaf','fruit','flower_inflorescence','stem','branches','root','jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec','created_at','updated_at')
    list_filter= ('stage','disease')


class WarehouseAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = (
         'id','name', 'other_name', 'state', 'warehouse_code', 'wcode', 'address',
        'created_by', 'created_at', 'updated_at', 'type', 'whtype',
        'longitude', 'latitude',
    )
    search_fields = ('name', 'other_name')


class WarehouseIndiaClustureAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        'ogc_fid', 'name', 'timestamp', 'begin', 'end',
        'altitudemode', 'tessellate', 'extrude', 'visibility', 'draworder',
        'icon', 'cluster_number', 'fill', 'stroke_opacity', 'stroke',
        'stroke_width', 
    )
    search_fields = ('name', 'description', 'cluster_number',)
    list_filter = ('timestamp', 'begin', 'end', 'altitudemode',)
    ordering = ('ogc_fid',)
    date_hierarchy = 'timestamp'

admin.site.register(models.WarehouseIndiaClusture, WarehouseIndiaClustureAdmin)


class BuyerSellerDetailAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = (
         'id','name', 'contact_number', 'created_at', 'updated_at', 'type_user', 
        'longitude', 'latitude',
    )



class WarehousePincodeLocationAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ("office_name", "pin_code", "state", "district", "country")
    search_fields = ("pin_code", "office_name", "state")


class SixtyKmClusterAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("ogc_fid", "name", "description")
    search_fields = ("name", "description")


class TenKmClusterAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("ogc_fid", "name", "description")
    search_fields = ("name", "description")




class LocationAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("id", "parent", "type", "name", "status", "created_at", "updated_at")
    search_fields = ("name", "type", "code", "alpha_code", "sap_code")
    list_filter = ("type", "status")
    ordering = ("id",)
    raw_id_fields = ("parent",)  # makes parent FK easier to handle for large data
    exclude = ("created_at", "updated_at")
  

admin.site.register(models.Location, LocationAdmin)


admin.site.register(models.SixtyKmCluster, SixtyKmClusterAdmin)
admin.site.register(models.TenKmCluster, TenKmClusterAdmin)

    


admin.site.register(models.WarehousePincodeLocation,WarehousePincodeLocationAdmin)
admin.site.register(models.BuyerSellerDetail,BuyerSellerDetailAdmin)
admin.site.register(models.Warehouse,WarehouseAdmin)
admin.site.register(models.Category,CategoryAdmin)
admin.site.register(models.HeadingAndAdvisory,HeadingAndAdvisoryAdmin)
admin.site.register(models.FarmsCategory,FarmsCategoryAdmin)
admin.site.register(models.CelreyTaskStatus, CeleryTaskStatusAdmin)
admin.site.register(models.CropStage,CropStageAdmin)
admin.site.register(models.CropDisease,CropDiseaseAdmin)
admin.site.register(models.DiseaseScoring,DiseaseScoringAdmin)