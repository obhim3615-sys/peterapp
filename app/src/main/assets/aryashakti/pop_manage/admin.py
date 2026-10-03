from django.contrib import admin
from .models import *
# Register your models here.
from import_export.admin import ExportActionMixin, ImportMixin

class DASProductAdmin(admin.ModelAdmin):
    pass

admin.site.register(DASProduct,DASProductAdmin)

class DASManageAdmin(admin.ModelAdmin):
    pass

admin.site.register(DASManage,DASManageAdmin)


class DASActivityAdmin(admin.ModelAdmin):
    pass

admin.site.register(DASActivity,DASActivityAdmin)


class CropAdmin(admin.ModelAdmin):
    pass

admin.site.register(Crop,CropAdmin)


class ProductAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    pass

admin.site.register(Product,ProductAdmin)


class ActivityAdmin(admin.ModelAdmin):
    pass

admin.site.register(Activity,ActivityAdmin)


@admin.register(Stage)
class StageAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)   # required for autocomplete_fields
    list_per_page = 50


@admin.register(SubStage)
class SubStageAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name', )


class VarietyAdmin(admin.ModelAdmin):
    pass

admin.site.register(Variety,VarietyAdmin)



@admin.register(ActivityPOP)
class ActivityPOPAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ('id','crop', 'activity_records_id', 'variety', 'stage', 'sub_stage')  # ✅ use real fields
    search_fields = ('activity_records_id__name', 'crop__crop_name','variety__crop_variety', 'stage__name', 'sub_stage__name')
    autocomplete_fields = ('variety', 'stage', 'sub_stage')


class OrganizationSoilTestingTokensAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','org','soil_testing_token','created_at','updated_at')
    autocomplete_fields = ('org',)
    
    search_fields = ('org__org_name',)


admin.site.register(OrganizationSoilTestingToken,OrganizationSoilTestingTokensAdmin)

@admin.register(FarmSoilTested)
class FarmSoilTestedAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ('id', 'farm_value', 'sample_id', 'project_id', 'file_response')
    search_fields = ('sample_id', 'project_id', 'farm_value__name')
    list_filter = ('project_id',)
    autocomplete_fields = ('farm_value',)



class ActivityPOPInline(admin.TabularInline):
    model = ActivityPOP
    extra = 1
    autocomplete_fields = ('variety', 'stage', 'sub_stage')


@admin.register(POPGroup)
class POPGroupAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    """
    Admin for POPGroup (capsule)
    Fields on model:
      - name
      - created_by_user (FK to user)
      - created_by_buyer_id (int)
      - created_from_prithvipro (bool)
    """
    list_display = (
        'id',
        'name',
        'created_by_user',
        'created_by_buyer_id',
        'created_from_prithvipro',
    )
    search_fields = (
        'name',
        'created_by_user__full_name',
        'created_by_user__mobile_number',
    )
    list_filter = ('created_from_prithvipro',)
    autocomplete_fields = ('created_by_user',)
    inlines = (ActivityPOPInline,)
    list_per_page = 50


@admin.register(FarmListing)
class FarmListingAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ('id', 'listing_id', 'farm', 'created_at')  # ✅ removed synced_at
    search_fields = ('listing_id', 'farm__name')
    autocomplete_fields = ('farm',)


@admin.register(Session)
class SessionAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ['name']

@admin.register(CropSession)
class CropSessionAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ('crop', 'session', 'from_month', 'to_month')
    list_filter = ('crop', 'session')
    search_fields = ('crop__name', 'session__name')
    autocomplete_fields = ('crop', 'session')

from admin_auto_filters.filters import AutocompleteFilter

class FarmerFilter(AutocompleteFilter):
    title = 'Farmer'
    field_name = 'farmer'

class FarmFilter(AutocompleteFilter):
    title = 'Farm'
    field_name = 'farm'


class UserFilter(AutocompleteFilter):
    title = 'User'
    field_name = 'user_shared'


class CropMasterFilter(AutocompleteFilter):
    title = 'Crop'
    field_name = 'crop'


class CropVarietyMasterFilter(AutocompleteFilter):
    title = 'Crop Variety'
    field_name = 'variety'


class ActivityPOPFilter(AutocompleteFilter):
    title = 'Activity pop'
    field_name = 'pop'

class OrganizationUserFilter(AutocompleteFilter):
    title = 'Organization'
    field_name = 'organization'


# admin.py
@admin.register(PopNotificationLog)
class PopNotificationLogAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ("farm", "farmer", "organization", "status", "created_at")
    list_filter = ("status", "created_at",FarmerFilter,OrganizationUserFilter)
    search_fields = ("farm__name", "farmer__full_name",)
    autocomplete_fields = ("farm", "farmer", "organization",)




# admin.py
@admin.register(PopShareLog)
class PopShareLogAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = (
        "id",
        "farm",
        "user_shared",
        "pop",
        "crop",
        "variety",
        "sowing",
        "created_at",
    )

    list_filter = (
        FarmFilter,
        UserFilter,
        CropMasterFilter,
        CropVarietyMasterFilter,
        ActivityPOPFilter,
        "created_at",
    )

    search_fields = (
        "farm__org_id__org_name",
        "user_shared__full_name",
        "user_shared__mobile_number",
        "crop__crop_name",
        "variety__crop_variety",
        "pop__activity_records_id__name",
    )

    autocomplete_fields = (
        "farm",
        "user_shared",
        "pop",
        "crop",
        "variety",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    date_hierarchy = "created_at"

    ordering = ("-created_at",)
