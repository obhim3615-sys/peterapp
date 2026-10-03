from django.contrib import admin
from .models import *
# Register your models here.
from import_export.admin import ExportActionMixin, ImportMixin
from app_farm.utils.helper import image_upload
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from core.models import CustomForm,CustomFormField
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from import_export import resources
from django.utils.safestring import mark_safe

from import_export.formats.base_formats import DEFAULT_FORMATS
import json
from django.contrib.admin import DateFieldListFilter
import uuid
from admin_auto_filters.filters import AutocompleteFilter

class FarmerFilter(AutocompleteFilter):
    title = 'Added by'
    field_name = 'farmer'

class DASActivityRecordAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','farmer','farm','created_at','day_of_sowing','date_of_activity','activity','image_url',"created_at","updated_at")
    autocomplete_fields = ('farmer','farm',)
    list_filter=(FarmerFilter,)
    search_fields = ('farmer__full_name','farm__name','date_of_activity','activity__name','farmer__organization__org_name')

admin.site.register(DASActivityRecord,DASActivityRecordAdmin)

class DASActivityRecordImageAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','image_url','activity_record',"created_at","updated_at")
    search_fields = ('activity_record__farmer__full_name','activity_record__activity__name')

    def save_model(self, request, obj, form, change):
        file=request.FILES.get('image_url')
        if file:
            path=image_upload(file)
            obj.image_url =path

        super().save_model(request, obj, form, change)

admin.site.register(DASActivityRecordImage,DASActivityRecordImageAdmin)

class ActivityFieldsAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','organization','activity','name','type','is_required','status',"created_at","updated_at")
    autocomplete_fields = ('organization',)

    search_fields = ('name','organization__org_name','activity__name','name','type',)

admin.site.register(ActivityFields,ActivityFieldsAdmin)

class ActivityRecordAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','organization','name','image','order_value',"created_at","updated_at")
    autocomplete_fields = ('organization',)

    search_fields = ('name','organization__org_name',)

    def save_model(self, request, obj, form, change):
        file=request.FILES.get('image')
        if file:
            path=image_upload(file)
            obj.image =path

        super().save_model(request, obj, form, change)

admin.site.register(ActivityRecord,ActivityRecordAdmin)

class OneTimeRecordAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','name','organization',"created_at","updated_at")
    autocomplete_fields = ('organization',)

    search_fields = ('name','organization__org_name')

admin.site.register(OneTimeRecord,OneTimeRecordAdmin)

class OneTimeRecordFieldAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','field','organization','name','type','is_required','status',"created_at","updated_at")
    autocomplete_fields = ('organization',)

    search_fields = ('field','name','type')

admin.site.register(OneTimeRecordField,OneTimeRecordFieldAdmin)


class OTRFarmerAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','farmer','record_type',"created_at","updated_at")
    autocomplete_fields = ('farmer','farm')
    
    search_fields = ('farmer__full_name','record_type')


admin.site.register(OTRFarmer,OTRFarmerAdmin)


class ThreadAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','farmer','farm','thread_id','assistant_id',"created_at","updated_at")
    autocomplete_fields = ('farmer','farm')
    
    search_fields = ('farmer__full_name','farmer__mobile_number','assistant','thread_id')


admin.site.register(Thread,ThreadAdmin)


class StatusHandleAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','name',"created_at","updated_at")
    
    search_fields = ('name',)


admin.site.register(StatusHandle,StatusHandleAdmin)

class FarmReportAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','farm',"created_at","updated_at")
    autocomplete_fields = ('farm',)
    search_fields = ('farm__user__full_name','farm__name','farm__farmer_contact')


admin.site.register(FarmReport,FarmReportAdmin)

class RequestForFarmCreditAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','farm',"created_at","updated_at")
    autocomplete_fields = ('farm',)
    search_fields = ('farm__user__full_name','farm__name','farm__farmer_contact')


admin.site.register(RequestForFarmCredit,RequestForFarmCreditAdmin)



class TaskBDAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','task_name','assigned_by','status_task','assigned_to','display_assigned_to_mobile_number','display_assigned_by_mobile_number',"created_at","updated_at")
    search_fields = ('task_name','assigned_by__full_name','assigned_by__mobile_number','assigned_to__full_name','assigned_to__mobile_number')
    autocomplete_fields = ('assigned_by','assigned_to')

    def display_assigned_to_mobile_number(self,obj):
        return obj.assigned_to.mobile_number 
    
    def display_assigned_by_mobile_number(self,obj):
        return obj.assigned_by.mobile_number 


admin.site.register(TaskBD,TaskBDAdmin)

class SubTaskBDAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','created_by','display_created_by_mobile_number','display_image_data','taskbd','display_custom_form_data','date_time_of_activity','title_of_activity','status',"created_at","updated_at")
    search_fields = ('taskbd__task_name','created_by__full_name','title_of_activity','date_time_of_activity','status')
    autocomplete_fields = ('created_by','taskbd') 
    list_filter = (
        ('created_at', DateFieldListFilter),
        ('updated_at', DateFieldListFilter),
    )

    def display_created_by_mobile_number(self,obj):
        return obj.created_by.mobile_number
    
    def display_image_data(self, obj):
        data=obj.subtask_subtask_img.all()
        image_data=""
        for i in data:
            image_data += f'<a target="__blank" href="{i.image_url}">Check Image</a>,'

        return mark_safe(image_data)
    def display_custom_form_data(self, obj):
        # Retrieve the JSON data from the custom_form_data column
        custom_form_data = obj.custom_form_data
        # Parse the JSON data
        try:
            data =custom_form_data
        except json.JSONDecodeError:
            # Handle invalid JSON data
            return 'Invalid JSON'

        # Build a string representation of the JSON data
        formatted_data = ''
        if data:
            if isinstance(data, dict):
                for key, value in data.items():
                    formatted_data += f'{key}: {value},'
            elif isinstance(data, list):
                for k in data:
                    if 'name' in k.keys() and 'value' in k.keys():
                        formatted_data += f'{k["name"]}: {k["value"]},'


            return formatted_data

    display_custom_form_data.short_description = 'Custom Form Data'  # Optional: Custom column header


admin.site.register(SubTaskBD,SubTaskBDAdmin)

class SubTaskImageAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','image_url','subtask',"created_at","updated_at")
    search_fields = ('subtask__created_by__full_name','subtask__title_of_activity')

    def save_model(self, request, obj, form, change):
        file=request.FILES.get('image_url')
        if file:
            path=image_upload(file)
            obj.image_url =path

        super().save_model(request, obj, form, change)

admin.site.register(SubTaskImage,SubTaskImageAdmin)


class ExternalClientAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ("id",'name', 'email', 'token', 'available_count',"created_at","updated_at")
    readonly_fields = ('token',)
    search_fields=("name",)

    def save_model(self, request, obj, form, change):
        if not obj.token:
            obj.token = uuid.uuid4()
        super().save_model(request, obj, form, change)

admin.site.register(ExternalClient, ExternalClientAdmin)

class ExternalThreadAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ("id",'thread_id', 'assistant_id', 'external_client_id',"created_at","updated_at")
    readonly_fields = ('thread_id','assistant_id','external_client_id')
    search_fields=("external_client_id__name",)


admin.site.register(ExternalThread, ExternalThreadAdmin)

class APICalledAnalyticAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ("id",'external_client', 'external_thread',"created_at","updated_at")
    readonly_fields = ('external_client','external_thread')
    search_fields=("external_clients__name",)
    autocomplete_fields=("external_client",'external_thread')


admin.site.register(APICalledAnalytic, APICalledAnalyticAdmin)

class FollowUpCalendarAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ("id",'subtask', 'date',"display_created_by_full_name","created_at","updated_at")
    search_fields=("subtask__created_by__full_name",)
    autocomplete_fields = ('subtask',)


    def display_created_by_full_name(self,obj):
        return obj.subtask.created_by.full_name


admin.site.register(FollowUpCalendar, FollowUpCalendarAdmin)

@staff_member_required
def bd_activity_subtask_template(request):
    templates= CustomForm.objects.filter(type="bd_activity_sub_task").all() 
    context = dict(
        templates=templates
    )    
    return render(request, "admin/bd_activity_subtask_template.html", context)




@staff_member_required
def bd_activity_subtask(request,id):
    data = SubTaskBD.objects.filter(custom_form_id=id)
    form_column= CustomFormField.objects.filter(custom_form_id=id).order_by('id').all()
    # Pagination
    id_sort=request.GET.get('id_sort')
    name_sort=request.GET.get('name_sort')
    task_sort=request.GET.get('task_sort')
    bd_name=request.GET.get('bd_name')
    greater_than=request.GET.get('greater_than')
    less_than=request.GET.get('less_than')

    if id_sort and id_sort=='1':
        data=data.order_by('id')
    
    if task_sort and task_sort=='1':
        data=data.order_by('taskbd__task_name')
    
    if name_sort and name_sort=='1':
        data=data.order_by('created_by__full_name')
    
    if bd_name :
        data=data.filter(created_by__full_name__icontains=bd_name)

    if greater_than  :
        data=data.filter(created_at__gte=greater_than)

    if less_than  :
        data=data.filter(created_at__lte=less_than) 

    data= data.all()
    paginator = Paginator(data, 40)  # Show 40 items per page
    page_number = request.GET.get('page')
    try:
        page_data = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        page_data = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results.
        page_data = paginator.page(paginator.num_pages)
    
    user_data=user.objects.order_by('full_name').all()[:50]
    context = dict(
        id=id,
        data=page_data,    
        page_obj=page_data,
        form_column=form_column,
        task_sort=task_sort,
        id_sort=id_sort,
        name_sort=name_sort,
        user_data=user_data,
        less_than=less_than,
        greater_than=greater_than
    )    
    return render(request, "admin/bd_activity_subtask.html", context)


@admin.register(Project)
class ProjectAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ("id","name", "created_by","created_at","updated_at")
    search_fields = ("name", "created_by__username")
    autocomplete_fields = ("created_by",)

@admin.register(ProjectUser)
class ProjectUserAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ("id","user", "project","created_at","updated_at")
    search_fields = ("user__username", "project__name")
    autocomplete_fields = ("user", "project")

@admin.register(ProjectTask)
class ProjectTaskAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ("task_name", "project", "task_type", "created_by","created_at","updated_at")
    search_fields = ("task_name", "project__name", "created_by__username")
    list_filter = ("task_type",)
    autocomplete_fields = ("project", "created_by")

@admin.register(ProjectTaskUser)
class ProjectTaskUserAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ("id","assigned_to", "project_task", "status", "farm","created_at","updated_at")
    search_fields = ("assigned_to__username", "project_task__task_name", "status")
    list_filter = ("status",)
    autocomplete_fields = ("assigned_to", "project_task", "farm")


@admin.register(SmartFarms)
class SmartFarmsAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ("id","farm", "created_at", "updated_at")
    search_fields = ("farm__name", "farm__farmer_contact")
    autocomplete_fields = ("farm",)



@admin.register(ExternalCropRemedy)
class ExternalCropRemedyAdmin(admin.ModelAdmin):
    list_display = ('thread_id', 'run_id', 'crop_name', 'disease_name', 'short_response')
    search_fields = ('thread_id', 'run_id', 'crop_name', 'disease_name')
    readonly_fields = ('thread_id', 'run_id', 'crop_name', 'disease_name', 'response')

    def short_response(self, obj):
        return (obj.response[:75] + '...') if obj.response and len(obj.response) > 75 else obj.response
    short_response.short_description = 'Response (Preview)'


@admin.register(FylloFarmData)
class FylloFarmDataAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ('id', 'plot_id')
    search_fields = ('plot_id',)

@admin.register(FarmFylloFarmData)
class FarmFylloFarmDataAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ('id', 'farm', 'get_plot_id')
    search_fields = ('farm_fyllow__plot_id',)
    autocomplete_fields = ('farm', 'farm_fyllow')

    @admin.display(description='plot_id')
    def get_plot_id(self, obj):
        return obj.farm_fyllow.plot_id
    


# ------------------------------
# Training (Master)
# ------------------------------
@admin.register(Training)
class TrainingAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "created_by",
        "custom_form",
        "created_at"
    )
    # list_filter = ( "custom_form",)
    search_fields = ("title",)
    ordering = ("-id",)
    autocomplete_fields=["created_by","custom_form"]


# ------------------------------
# Inline Farms for Execution
# ------------------------------
class TrainingExecutionFarmInline(admin.TabularInline):
    model = TrainingExecutionFarm
    extra = 0
    autocomplete_fields = ("farm",)


# ------------------------------
# Training Execution
# ------------------------------
@admin.register(TrainingExecution)
class TrainingExecutionAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = (
        "id",
        "training",
        "conducted_by",
        "conducted_at"
    )
    list_filter = ("training",)
    search_fields = ("training__title",)
    ordering = ("-id",)
    inlines = [TrainingExecutionFarmInline]
    autocomplete_fields=["conducted_by","organization"]

    readonly_fields = ("conducted_at",)


# ------------------------------
# TrainingExecutionFarm (optional direct admin)
# ------------------------------
@admin.register(TrainingExecutionFarm)
class TrainingExecutionFarmAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = (
        "id",
        "training_execution",
        "farm",
        "created_at"
    )
    autocomplete_fields = ("training_execution", "farm")
    ordering = ("-id",)


@admin.register(CtQuestions)
class CtQuestionsAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("id", "title", "is_active", "created_at", "updated_at")
    search_fields = ("title", "description")
    list_filter = ("is_active",)
    ordering = ("-id",)


@admin.register(CtQuestionsFarm)
class CtQuestionsFarmAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ("id", "ct_question", "user", "added_by", "farm", "status", "created_at", "updated_at")
    search_fields = ("ct_question__title", "user__full_name", "farm__name")
    list_filter = ("status",)
    autocomplete_fields = ("ct_question", "user", "farm", "added_by")
    ordering = ("-id",)


@admin.register(DroneSprayActivity)
class DroneSprayActivityAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):

    list_display = (
        "id",
        "reference_id",
        "farm",
        "farmer",
        "get_spray_type_display",
        "crop",
        "get_preferred_week_display",
        "get_spray_date_display",
        "status",
        "get_area_display",
        "requested_by",
        "created_at",
    )

    search_fields = (
        "reference_id",
        "farm__name",
        "farmer__full_name",
        "village",
        "crop",
        "webhook_reference_id",
        "district",
    )

    list_filter = (
        "status",
        ("preferred_week_start", DateFieldListFilter),
        ("date_of_spraying", DateFieldListFilter),
        "district",
        "organization",
        ("created_at", DateFieldListFilter),
    )

    autocomplete_fields = (
        "farm",
        "farmer",
        "organization",
        "created_by",
        "requested_by",
        "rejected_by",
        "custom_form",
    )

    readonly_fields = (
        "reference_id",
        "created_at",
        "updated_at",
        "completed_at",
        "rejected_at",
        "webhook_payload",
        "webhook_received_at",
        "webhook_status",
        "display_form_response",
        "display_products",
    )

    fieldsets = (
        ('Basic Info', {
            'fields': (
                'reference_id',
                'farm',
                'farmer',
                'organization',
                'status',
            ),
            'description': 'Spray type is stored in form_response'
        }),
        ('Location', {
            'fields': ('state', 'district', 'tehsil', 'village'),
            'classes': ('collapse',)
        }),
        ('Crop & Area', {
            'fields': ('crop', 'area_total', 'area_unit', 'area_sprayed', 'area_sprayed_unit')
        }),
        ('Request Details (Booking)', {
            'fields': ('preferred_week_start', 'preferred_week_end'),
            'description': 'Preferred week for spraying - filled during request'
        }),
        ('Dynamic Form', {
            'fields': ('custom_form', 'form_response', 'display_form_response'),
            'classes': ('collapse',)
        }),
        ('Spray Details (Actual Execution)', {
            'fields': (
                'spray_cycle',
                'date_of_spraying',
                'crop_stage',
                'pest_or_activity',
                'products',
                'display_products',
            ),
            'description': 'Actual spray details '
        }),
        ('GeoJSON Data', {
            'fields': (
                'geojson_file',
                'spray_area_coordinates',
                'geojson_geometry',
                'geojson_area',
            ),
            'classes': ('collapse',),
            'description': 'GeoJSON spray area file and coordinates'
        }),
        ('Webhook', {
            'fields': (
                'webhook_reference_id',
                'webhook_status',
                'webhook_payload',
                'webhook_received_at',
            ),
            'classes': ('collapse',)
        }),
        ('Workflow', {
            'fields': (
                'requested_by',
                'rejected_by',
                'rejected_at',
                'rejection_reason',
            ),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': (
                'created_by',
                'created_at',
                'updated_at',
                'completed_at',
            ),
            'classes': ('collapse',)
        }),
    )

    ordering = ("-created_at",)
    
    actions = ['mark_as_in_progress', 'mark_as_completed', 'mark_as_cancelled']

    def get_preferred_week_display(self, obj):
        if obj.preferred_week_start and obj.preferred_week_end:
            return f"{obj.preferred_week_start} to {obj.preferred_week_end}"
        return '-'
    get_preferred_week_display.short_description = 'Preferred Week'

    def get_spray_date_display(self, obj):
        return obj.date_of_spraying if obj.date_of_spraying else '-'
    get_spray_date_display.short_description = 'Spray Date'
    
    def get_area_display(self, obj):
        if obj.area_sprayed:
            unit = obj.area_sprayed_unit or obj.area_unit or 'acres'
            return f"{obj.area_sprayed} {unit}"
        return '-'
    get_area_display.short_description = 'Area Sprayed'
    
    def get_spray_type_display(self, obj):
        spray_type = obj.get_spray_type()
        return spray_type if spray_type != 'N/A' else '-'
    get_spray_type_display.short_description = 'Spray Type'
    
    def display_form_response(self, obj):
        if obj.form_response:
            import json
            formatted = json.dumps(obj.form_response, indent=2)
            return mark_safe(f"<pre>{formatted}</pre>")
        return "-"
    display_form_response.short_description = 'Form Response (Formatted)'
    
    def display_products(self, obj):
        if obj.products:
            html = "<ul>"
            for product in obj.products:
                html += f"<li><b>{product.get('product_name', 'N/A')}</b>: {product.get('dosage', 'N/A')} {product.get('unit', 'N/A')}</li>"
            html += "</ul>"
            return mark_safe(html)
        return "-"
    display_products.short_description = 'Products Used'
    
    def mark_as_in_progress(self, request, queryset):
        count = queryset.filter(status__in=['PENDING', 'REQUESTED']).update(status='IN_PROGRESS')
        self.message_user(request, f"{count} spray activities marked as IN PROGRESS")
    mark_as_in_progress.short_description = "Mark selected as IN PROGRESS"
    
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for obj in queryset.filter(status__in=['IN_PROGRESS', 'REQUESTED', 'PENDING']):
            obj.status = 'COMPLETED'
            if not obj.completed_at:
                obj.completed_at = timezone.now()
            obj.save()
            updated += 1
        self.message_user(request, f"{updated} spray activities marked as COMPLETED")
    mark_as_completed.short_description = "Mark selected as COMPLETED"
    
    def mark_as_cancelled(self, request, queryset):
        count = queryset.exclude(status='COMPLETED').update(status='CANCELLED')
        self.message_user(request, f"{count} spray activities marked as CANCELLED")
    mark_as_cancelled.short_description = "Mark selected as CANCELLED"
