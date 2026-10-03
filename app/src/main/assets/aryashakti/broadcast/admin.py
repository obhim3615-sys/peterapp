from django.contrib import admin

from . import models
from app_farm.utils.helper import image_upload
from import_export.admin import ExportActionMixin, ImportMixin
from admin_auto_filters.filters import AutocompleteFilter

from app_farm.models import user,organizations
# Register your models here.
class SmsTemplateAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','name','order','template_id','msg','description','image','created_at','updated_at')
    search_fields = ('name','msg','template_id','description',)

    def save_model(self, request, obj, form, change):        
        file=request.FILES.get('image')
        if file:
            path=image_upload(file)
            obj.image =path

        super().save_model(request, obj, form, change)

class SmsTemplateFieldAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','name','type','field_possible_value','is_required','status','sms_template','created_at','updated_at')
    list_filter= ('sms_template','type','is_required','status')
    search_fields = ('name',)


admin.site.register(models.SmsTemplate,SmsTemplateAdmin)
admin.site.register(models.SmsTemplateField,SmsTemplateFieldAdmin)


class CommunitiesShareAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','image','organization')
    list_filter= ('organization',)
    search_fields = ('organization__name',)

    def save_model(self, request, obj, form, change):
        file=request.FILES.get('image')
        if file:
            path=image_upload(file)
            obj.image =path

        super().save_model(request, obj, form, change)


admin.site.register(models.CommunitiesShare,CommunitiesShareAdmin)


# Define filters for each relation field
class ReceiverFilter(AutocompleteFilter):
    title = 'Receiver'  # Display name in the admin
    field_name = 'receiver'  # Model field name


class SenderFilter(AutocompleteFilter):
    title = 'Sender'
    field_name = 'sender'


class OrganizationFilter(AutocompleteFilter):
    title = 'Organization'
    field_name = 'org_name'

@admin.register(models.NotificationLog)
class NotificationLogAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = (
        "id",
        "sender",
        "receiver",
        "receiver_phone",
        "sms_template",
        "org_name",
        "status",
        "created_at",
    )
    # ✅ enable autocomplete for ForeignKey fields
    autocomplete_fields = ("sender", "receiver", "org_name")
    # Use autocomplete filters
    list_filter = (ReceiverFilter, SenderFilter, OrganizationFilter)

    search_fields = ("receiver_phone",)
    
    # ✅ make only timestamps read-only
    readonly_fields = ("created_at", "updated_at")

    
