from django.contrib import admin
from import_export.admin import ExportActionMixin, ImportMixin

from app_farm.utils.helper import image_upload
from . import models

# Register your models here.
class KutumbAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','kutumb_id','husband','wife','status','payment','added_by_org','created_at','updated_at')
    list_filter= ('status','added_by_org')
    search_fields = ('kutumb_id',)
    autocomplete_fields = ('added_by_org','husband','wife')

class MemberAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','first_name','last_name','dob','gender','phone','gender','aadhaar_num','masked_aadhaar','email','address1','address2','city','district','pincode','state','country','front_aadhaar','back_aadhaar','bank_acc','created_at','updated_at')
    list_filter= ('gender','city','district','pincode')
    search_fields = ('first_name','last_name','phone','aadhaar_num')
    autocomplete_fields = ('bank_acc',)

    def save_model(self, request, obj, form, change):
        imgs = ['front_aadhaar','back_aadhaar']

        for img in imgs:
            file=request.FILES.get(img)
            if file:
                path=image_upload(file)
                obj[img] =path

        super().save_model(request, obj, form, change)

class NomineeAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','name','relationship','phone','kutumb','created_at','updated_at')
    list_filter= ('relationship','kutumb')
    search_fields = ('name','phone')
    autocomplete_fields = ('kutumb',)

admin.site.register(models.Kutumb,KutumbAdmin)
admin.site.register(models.Member,MemberAdmin)
admin.site.register(models.Nominee,NomineeAdmin)

@admin.register(models.InsuranceEnrollment)
class InsuranceEnrollmentAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = (
        'id', 'first_name', 'last_name', 'aadhaar_number', 'mobile',
        'gender', 'dob', 'city', 'state', 'status', 'submitted_at'
    )
    list_filter = ('gender', 'state', 'status', 'submitted_at', 'social_scheme')
    search_fields = (
        'aadhaar_number', 'first_name', 'last_name', 'mobile',
        'nominee_first_name', 'nominee_last_name', 'account_number'
    )
    readonly_fields = ('submitted_at',)