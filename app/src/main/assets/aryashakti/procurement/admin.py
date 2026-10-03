from django.contrib import admin
from .models import *
from app_farm.utils.helper import image_upload

# Register your models here.
from import_export.admin import ExportActionMixin, ImportMixin


class ProcurementRegisterAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','name','organization','user','status')
    search_fields = ('name','organization__org_name')
    autocomplete_fields = ('organization','user') 


admin.site.register(ProcurementRegister,ProcurementRegisterAdmin)


class ProcurementAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','crop','user_from','user_to','variety','qty','rate','amount','description','payment','payout','status')
    search_fields = ('name','organization__org_name','crop__crop_name')
    autocomplete_fields = ('user_from','user_to') 


admin.site.register(Procurement,ProcurementAdmin)

class ProcurementImageAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','procurement','image_url')
    autocomplete_fields = ('procurement',) 

    def save_model(self, request, obj, form, change):
        file=request.FILES.get('image_url')
        if file:
            path=image_upload(file)
            obj.image_url =path

        super().save_model(request, obj, form, change)

admin.site.register(ProcurementImage,ProcurementImageAdmin)


# @admin.register(AxisBankOrganization)
# class AxisBankOrganizationAdmin(admin.ModelAdmin):
#     list_display = (
#         'id', 
#         'organization', 
#         'user', 
#         'corp_code', 
#         'corp_account_number',
#         'created_at',  # assuming BaseModel has created_at
#         'updated_at',  # assuming BaseModel has updated_at
#     )
#     search_fields = (
#         'organization__name',  # if organization has name field
#         'user__email',         # if user has email field
#         'corp_code',
#         'corp_account_number',
#     )
#     autocomplete_fields = ('organization','user') 

#     # list_filter = ('organization', 'user')
#     ordering = ('-created_at',)