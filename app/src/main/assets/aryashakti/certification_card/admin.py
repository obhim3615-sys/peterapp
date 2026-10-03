from django.contrib import admin
from .models import *
from app_farm.utils.helper import image_upload
from import_export.admin import ExportActionMixin, ImportMixin

# Register your models here.

class FarmerCertificationAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','farmer','certification','file_url','authority_name','created_at','updated_at')
    search_fields = ('farmer__full_name','farmer__mobile_number',)    
    autocomplete_fields = ('farmer',)

    def save_model(self, request, obj, form, change):
        file=request.FILES.get('file_url')
        if file:
            path=image_upload(file)
            obj.file_url =path

        super().save_model(request, obj, form, change)

admin.site.register(FarmerCertification,FarmerCertificationAdmin)

class CertificationAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display=['name','color','order_value','created_at','updated_at']
    def save_model(self, request, obj, form, change):
        file=request.FILES.get('background')
        if file:
            path=image_upload(file)
            obj.background =path

        super().save_model(request, obj, form, change)


admin.site.register(Certification,CertificationAdmin)

class ScoreAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display=['name','status','created_at','updated_at']
    
    def save_model(self, request, obj, form, change):
        file=request.FILES.get('icon')
        if file:
            path=image_upload(file)
            obj.icon =path

        super().save_model(request, obj, form, change)

admin.site.register(Score,ScoreAdmin)

class ScoreFarmerAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display=['farmer','farmer_certification','created_at','updated_at']
    search_fields = ('farmer__full_name','farmer__mobile_number',)    
    autocomplete_fields = ('farmer',)
    

admin.site.register(ScoreFarmer,ScoreFarmerAdmin)


class BadgeAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        file=request.FILES.get('icon')
        if file:
            path=image_upload(file)
            obj.icon =path

        super().save_model(request, obj, form, change)

admin.site.register(Badge,BadgeAdmin)

class BadgeFarmerAdmin(admin.ModelAdmin):
    list_display=['farmer','badge','created_at','updated_at']
    search_fields = ('farmer__full_name','farmer__mobile_number',)    
    autocomplete_fields = ('farmer',)

admin.site.register(FarmerBadge,BadgeFarmerAdmin)

class GraphHistoryAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display=['farm','type','created_at','value','date','updated_at']
    search_fields = ('farm__name','farm__farmer_contact')    
    autocomplete_fields = ('farm',)

admin.site.register(GraphHistory,GraphHistoryAdmin)

class ValueTypeAdmin(admin.ModelAdmin):
    pass

admin.site.register(ValueType,ValueTypeAdmin)

class ScoreGeneralFarmerAdmin(admin.ModelAdmin):
    list_display=['farmer','value','created_at','updated_at']
    search_fields = ('farmer__full_name','farmer__mobile_number',)    
    autocomplete_fields = ('farmer',)

admin.site.register(ScoreGeneralFarmer,ScoreGeneralFarmerAdmin)
