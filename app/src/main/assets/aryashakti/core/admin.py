from django.contrib import admin
from import_export.admin import ExportActionMixin, ImportMixin

from . import models
from app_farm.utils.helper import image_upload

# # Register your models here.
class PermissionAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','name','slug','api','description','created_at','updated_at')
    list_filter= ('api',)
    search_fields = ('name','api','slug',)

class CountryAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','name','code','mobile_code','phone_len','image','created_at','updated_at')
    search_fields = ('name','code','mobile_code',)

    def save_model(self, request, obj, form, change):
        file=request.FILES.get('image')
        if file:
            path=image_upload(file)
            obj.image =path

        super().save_model(request, obj, form, change)

class WhiteListedMobileAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','name','phone','country','otp','created_at','updated_at')
    search_fields = ('name','phone',)

class CustomFormAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','name','type','created_at','updated_at')
    list_filter= ('type',)
    search_fields = ('name',)
    def save_model(self, request, obj, form, change):        
        file=request.FILES.get('image_url')
        if file:
            path=image_upload(file)
            obj.image_url =path

        super().save_model(request, obj, form, change)

class CustomFormFieldAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','name','type','field_possible_value','is_required','status','custom_form','order','created_at','updated_at')
    list_filter= ('custom_form','type','is_required','status')
    search_fields = ('name',)


class CustomFormParentAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display=('id','custom_form_child','custom_form_parent')

    
    def save_model(self, request, obj, form, change):
        # Check if both fields have values
        if obj.custom_form_parent_id and obj.custom_form_child_id:
            # Check if the values are the same
            if obj.custom_form_parent_id == obj.custom_form_child_id:
                # Return an error message
                return self.message_user(request, "Parent and Child cannot have the same value.", level="ERROR")
        # Save the model
        super().save_model(request, obj, form, change)

admin.site.register(models.Country,CountryAdmin)
admin.site.register(models.Permission,PermissionAdmin)
admin.site.register(models.WhiteListedMobile,WhiteListedMobileAdmin)
admin.site.register(models.CustomForm,CustomFormAdmin)
admin.site.register(models.CustomFormField,CustomFormFieldAdmin)
admin.site.register(models.CustomFormParent,CustomFormParentAdmin)
