from django.contrib import admin
from .models import *
#user_phonenumber_map
from django import forms
from django.urls import path
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.admin import DateFieldListFilter
from django.db.models import Sum
from import_export.admin import ExportActionMixin, ImportMixin
from django.template.response import TemplateResponse
from django.contrib.admin.views.decorators import staff_member_required
import csv
from django.http import HttpResponse
from app_farm.utils.queries_lib import org_counts,getAllBD,org_details_counts,org_details_counts_farm
from app_farm.utils.helper import image_upload
from import_export.admin import ExportActionMixin, ImportMixin
from admin_auto_filters.filters import AutocompleteFilter


class CsvImportForm(forms.Form):
    csv_upload = forms.FileField()

class user_rolesAdmin(admin.ModelAdmin):
    list_display= ('id','role_name','show_in_list','admin_rights','description')
    
    def save_model(self, request, obj, form, change):
        obj.name="sjhsfjdfsdkfl"
        file=request.FILES.get('image')
        if file:
            path=image_upload(file)
            obj.image =path

        super().save_model(request, obj, form, change)
        
admin.site.register(user_roles,user_rolesAdmin)

class OrgTypeAdmin(admin.ModelAdmin):
    list_display= ('id','name','image')

    def save_model(self, request, obj, form, change):
        file=request.FILES.get('image')
        if file:
            path=image_upload(file)
            obj.image =path

        super().save_model(request, obj, form, change)
admin.site.register(OrgType, OrgTypeAdmin)

class organizationsAdmin(ImportMixin,ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','room_100ms','org_name','logo','number_of_members','myplot_company_id','company_id','map_layer','latitude','longitude','cin','is_verified','pincode','country','state','district','taluka','village','share_capital','paid_capital','status','reviewed','manual_address','fpo_contact_no','geometry','zoom','carousel1','carousel2','carousel3','carousel4','members','acres','crops','stress','damaged','relationship_manager_name','relationship_manager_no','is_active')
    search_fields = ('org_name','company_id')
    list_filter = ('is_verified',)
    autocomplete_fields = ('group_org',)
    readonly_fields = ('created_at','updated_at')

admin.site.register(organizations,organizationsAdmin)

class SoilReportAdmin(admin.ModelAdmin):
    list_display= ('id','farmer','soil_report','created_at','updated_at')
    autocomplete_fields = ('farmer',)
    
    def save_model(self, request, obj, form, change):        
        file=request.FILES.get('soil_report')
        if file:
            path=image_upload(file)
            obj.soil_report =path

        super().save_model(request, obj, form, change)

admin.site.register(SoilReport,SoilReportAdmin)

class agendaAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','img_url','text')

    def save_model(self, request, obj, form, change):        
        file=request.FILES.get('img_url')
        if file:
            path=image_upload(file)
            obj.img_url =path

        super().save_model(request, obj, form, change)

admin.site.register(agenda,agendaAdmin)

class OrganizationUserFilter(AutocompleteFilter):
    title = 'Organization'
    field_name = 'organization'


class AddedbyUserFilter(AutocompleteFilter):
    title = 'Added by'
    field_name = 'added_by'

class userAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','email','organization','installed_app','user_role','admin','is_cvrp','mobile_number','otp_verfied','full_name','full_name_telugu','land_size','land_size_unit','land_size_unit_telugu','crop_interest','address_pincode','address_country','address_state','address_district','address_taluka','address_village','no_of_plots','latitude','longitude','designation','bio','timestamp','timestamp_first_login','timestamp_login','firebase_token','user_profile_img','added_by','verified_by','country')
    list_filter = ('user_role_id','is_cvrp',OrganizationUserFilter,('timestamp', DateFieldListFilter),'country',AddedbyUserFilter)
    search_fields = ('mobile_number','full_name')
    date_hierarchy = 'timestamp'
    autocomplete_fields = ('organization','added_by','verified_by')

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if type(response) == TemplateResponse and response.template_name == 'admin/change_list.html':
            queryset = response.context_data['cl'].queryset
            total_users = queryset.count()
            response.context_data['total_users'] = total_users
            response.context_data['user_page'] = True
        return response

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            a = csv_file.read()
            file_data = a.decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = user.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)

admin.site.register(user,userAdmin)
#admin.site.register(user)
class product_masterAdmin(admin.ModelAdmin):
    list_display= ('id','status','name','title_telegu','type','category_a','sub_category','prod_desc','prod_desc_telegu','prod_info','prod_info_telegu','display_price','display_mrp','agent_price','tag','popular')
    list_filter = ('id','name')
    search_fields = ('id','name')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(product_master,product_masterAdmin)

class carouselAdmin(admin.ModelAdmin):
    list_display= ('id','user','page','index','text','text_telugu','image_url','image_url_telugu','redirect_to')
    autocomplete_fields = ('user',)
    
    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = carousel.objects.update_or_create(
                    page = fields[0],
                    index = fields[1],
                    text = fields[2],
                    text_telugu= fields[3],
                    image_url= fields[4],
                    image_url_telugu= fields[5],
                    redirect_to =  fields[6],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(carousel,carouselAdmin)

class machinesAdmin(admin.ModelAdmin):
    list_display= ('id','machine_name','machine_name_telugu','machine_maker','machine_maker_telugu','machine_model','machine_model_telugu','owned','image_url','user_id')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(machine_master,machinesAdmin)

class crop_masterAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','crop_name','crop_unselected_icon_url','crop_selected_icon_url')
    search_fields = ('crop_name',)


    
admin.site.register(crop_master,crop_masterAdmin)

class crop_variety_masterAdmin(ImportMixin,ExportActionMixin,admin.ModelAdmin):
    list_display = ('id', 'crop_id', 'crop_variety', 'crop_variety_telugu')
    search_fields = ('crop_variety', 'crop_variety_telugu', 'crop_id__crop_name')  # adjust field name inside crop_master
    autocomplete_fields = ('crop_id',)  # ✅ correct FK field
   

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(crop_variety_master,crop_variety_masterAdmin)




class language_masterAdmin(admin.ModelAdmin):
    list_display= ('id','name','google_translate_code')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(language_master,language_masterAdmin)

class notificationAdmin(admin.ModelAdmin):
    list_display= ('id','user_id','title','title_telugu','desc','desc_telugu','timestamp','notification_icon','group')
    autocomplete_fields = ('user_id',)

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(notification,notificationAdmin)

class orderAdmin(admin.ModelAdmin):
    list_display= ('id','total_amount','status','user_name','notes','user_mobile')

    def user_name(self, obj):
        return obj.user_id.full_name
    def user_mobile(self,obj):
        return obj.user_id.mobile_number

    user_name.description = 'User Name'

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)

admin.site.register(order,orderAdmin)

class orderDetailsAdmin(admin.ModelAdmin):
    list_display= ('id','order_id','brand_name','product_name','quantity','amount')

    def  product_name(self,obj):
        return obj.product_id.name
    def brand_name(self,obj):
        return obj.product_id.brand_id.name
    def quantity(self,obj):
        return obj.quantity
    product_name.short_discription='Product Name'
    brand_name.short_discription="Brand Name"
    quantity.short_discription="quantity"

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)

admin.site.register(order_details,orderDetailsAdmin)
class OrganizationFilter(AutocompleteFilter):
    title = 'Organization'
    field_name = 'org_id'


class AddedbyFarmFilter(AutocompleteFilter):
    title = 'Added by'
    field_name = 'added_by'
class farmAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','user','updated_by_id','added_by','org_id','featured','name','name_telugu','stage','stage_telugu','total_area','area_unit','area_unit_telegu','crop_id','crop_variety_id','khasra_no','sowing_date','farm_images','timestamp','my_plot_id','season_id','farm_img','farmer_contact','graph_image_url','latitude','longitude','is_location','farm_country','farm_state','farm_district','farm_taluka','farm_village','farm_state_hindi','farm_district_hindi','farm_taluka_hindi','farm_village_hindi','stressed','biotic_stress','abiotic_stress','nutrient_stress','moisture','stress','damaged','user_survey')
    list_filter= ('is_location','crop_id_id', ('timestamp', DateFieldListFilter),OrganizationFilter,AddedbyFarmFilter,'farmer_type')
    search_fields = ('farmer_contact','name')
    date_hierarchy = 'timestamp'
    autocomplete_fields = ('updated_by_id','added_by','user','org_id','user_survey','crop_variety_id')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls
     
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        if type(response) == TemplateResponse and response.template_name == 'admin/change_list.html':
            queryset = response.context_data['cl'].queryset
            total_farms = queryset.count()
            total = queryset.aggregate(total=Sum('total_area'))['total']
            response.context_data['sum_of_area'] = total or 0.0
            response.context_data['total_farms'] = total_farms
            response.context_data['farm_page'] = True
        return response

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = farm.objects.update_or_create(
                    #user_id = fields[0],
                    name = fields[0],
                    name_telugu= fields[1],
                    stage= fields[2],
                    stage_telugu= fields[3],
                    total_area= fields[4],
                    area_unit= fields[5],
                    area_unit_telegu= fields[6],
                    #crop_id= fields[7],
                    #crop_variety_id= fields[8],
                    khasra_no= fields[7],
                    #sowing_date= fields[11],
                    #crop_variety_id= fields[12],
                    #farm_polygon= fields[12],
                    #farm_images= fields[11],

                    #timestamp= fields[13],
                    my_plot_id= fields[8],
                    farm_img= fields[9],
                    farmer_contact = fields[10],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(farm,farmAdmin)

class FarmChangeLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'farm', 'changed_by', 'field_name', 'old_value', 'new_value', 'changed_at')
    list_filter = ('field_name', 'changed_at')
    search_fields = ('farm__name', 'old_value', 'new_value')
    autocomplete_fields = ('farm', 'changed_by')


admin.site.register(FarmChangeLog, FarmChangeLogAdmin)

class stress_dataAdmin(admin.ModelAdmin):
    list_display= ('id','farm_id','date','biotic_stress','abiotic_stress','nutrient_stress','moisture')
    #list_filter = ('mobile_number','full_name')
    #search_fields = ('mobile_number','full_name')
    autocomplete_fields = ('farm_id',)


admin.site.register(stress_data,stress_dataAdmin)


class brand_masterAdmin(admin.ModelAdmin):
    list_display= ('id','name','name_telugu','notes')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(brand_master,brand_masterAdmin)

class offersAdmin(admin.ModelAdmin):
    list_display= ('id','status','brand_id','title','title_telugu','desc','desc_telugu','criteria','criteria_telugu','duration','duration_telugu','limit','limit_telugu','availability','availability_telugu','image_url')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = offers.objects.update_or_create(
                    name = fields[0],
                    org_id = fields[1],
                    status = fields[2],
                    brand_id = fields[3],
                    title = fields[4],
                    title_telugu = fields[5],
                    desc = fields[6],
                    desc_telugu = fields[7],
                    criteria = fields[8],
                    criteria_telugu = fields[9],
                    duration = fields[10],
                    duration_telugu = fields[11],
                    limit = fields[12],
                    limit_telugu = fields[13],
                    availability = fields[14],
                    availability_telugu = fields[15],
                    image_url = fields[16],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(offers,offersAdmin)



class sell_cropAdmin(admin.ModelAdmin):
    list_display= ('id','user_id','org_id','crop_id','crop_variety_id','quantity_expected','price_expected','availability_date','availability_days','notes','image_url','quantity_expected_unit','quantity_expected_unit_telegu')
    autocomplete_fields = ('org_id','user_id')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(sell_crop,sell_cropAdmin)

class newsAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','org_id','status','rank','title','source','source_telugu','timestamp','desc','notes','url_telugu','notes')
    autocomplete_fields = ('org_id',)

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = news.objects.update_or_create(
                    id = fields[0],
                    title = fields[1],

                    status = fields[2],
                    rank = fields[3],

                    title_telugu = fields[4],
                    source = fields[5],
                    source_telugu = fields[6],
                    #timestamp = fields[7],
                    desc = fields[7],
                    desc_telugu = fields[8],
                    url_telugu = fields[9],
                    image_url = fields[10],
                    thumbnail_url = fields[11],
                    notes = fields[12],
                    #org_id = fields[13],

                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(news,newsAdmin)

class trackingAdmin(admin.ModelAdmin):
    list_display= ('id','order_id','packaged_date','dispatched_date','dispatched','packaged','delivered','out_for_delivery','packed_details','dispatched_details','out_for_delivery_details','delivered_details')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(tracking,trackingAdmin)

class deliveryaddressAdmin(admin.ModelAdmin):
    list_display= ('id','user_id','delivery_pincode','location','location1','house','landmark','notes')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(delivery_address,deliveryaddressAdmin)

class productvariants_masterAdmin(admin.ModelAdmin):
    list_display= ('id','product_id','image_url','in_stock')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(product_variants,productvariants_masterAdmin)

class hashtag_masterAdmin(admin.ModelAdmin):
    list_display= ('id','tag','title')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(hashtag_master,hashtag_masterAdmin)

class location_masterAdmin(admin.ModelAdmin):
    list_display= ('id','location_name')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(location_master,location_masterAdmin)

class friends_masterAdmin(admin.ModelAdmin):
    list_display= ('id','user_id','friend_user_id')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(friends_master,friends_masterAdmin)

class trainingAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','org_id','status','brand_id','title','desc','media_url','media_type','hashtag')
    autocomplete_fields = ('org_id',)

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = training.objects.update_or_create(
                    name = fields[0],
                    org_id= fields[1],
                    status = fields[2],
                    brand_id = fields[3],
                    title = fields[4],
                    title_telugu = fields[5],
                    desc = fields[6],
                    desc_telugu = fields[7],
                    media_url = fields[8],
                    media_type = fields[9],
                    hashtag = fields[10],
                    timestamp = fields[11],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(training,trainingAdmin)

class social_postAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','org_id','user_name','status','timestamp','media_url','media_type','short_desc_telugu','desc','desc_telugu','location_id','friend_id','hashtag_id')
    autocomplete_fields = ('org_id','user_id')
    search_fields=('user_name','desc')

    def user_name(self,obj):
        return ('%s'%(obj.user_id.full_name))

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = social_post.objects.update_or_create(
                    user_id = fields[0],
                    org_id = fields[1],
                    media_file = fields[2],
                    media_url = fields[3],
                    media_type = fields[4],
                    desc = fields[5],
                    desc_telugu = fields[6],
                    location_id = fields[7],
                    short_desc_telugu = fields[8],
                    friend_id = fields[9],
                    hashtag_id = fields[10],
                    timestamp = fields[11],
                    approved = fields[12],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)

admin.site.register(social_post,social_postAdmin)

class SocialPostTagAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','name','status',)

admin.site.register(SocialPostTag,SocialPostTagAdmin)


class community_post_reportingAdmin(admin.ModelAdmin):
    list_display= ('id','user_id','post_id','timestamp','spam','inappropriate','comments')
    autocomplete_fields = ('user_id','post_id')

admin.site.register(community_post_reporting,community_post_reportingAdmin)

class otpAdmin(admin.ModelAdmin):
    list_display= ('otp_value','phone_number')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(OTPValidation,otpAdmin)

class implementsAdmin(admin.ModelAdmin):
    list_display= ('id','user_id','implement_name','implement_name_telugu','implement_maker','implement_maker_telugu','implement_model','implement_name_telugu')
    autocomplete_fields = ('user_id',)

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(implement_master,implementsAdmin)

class aryadhan_inquiryAdmin(admin.ModelAdmin):
    list_display= ('id','aryadhan_id','user_id','selected_info','comments')
    autocomplete_fields = ('user_id',)

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(aryadhan_inquiry,aryadhan_inquiryAdmin)


class agentsAdmin(admin.ModelAdmin):
    list_display= ('id','user_id','language','approved','mobile_no')
    def mobile_no(self,obj):
        return obj.user_id.mobile_number

    def language(self,obj):
        return obj.user_id.language_selected

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(agents,agentsAdmin)

admin.site.register(tb_application_access)
admin.site.register(partner_type_master)
admin.site.register(partner_list)

class activity_masterAdmin(admin.ModelAdmin):
    list_display= ('id','activity_name','activity_name_telugu')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(activity_master,activity_masterAdmin)


class activityAdmin(admin.ModelAdmin):
    list_display= ('id','org_id','user_id','activity_name','activity_name_telugu','activity_id','start_timestamp','end_timestamp','total_hours','total_area','area_unit','chemical_used','chemical_used_telugu','seed_used','seed_used_telugu','machine_used','machine_used_telugu','implement_used','implement_used_telugu','plot_id','plot_id_telugu')
    autocomplete_fields = ('user_id','org_id')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = activity.objects.update_or_create(
                    user_id = fields[0],
                    org_id = fields[1],
                    activity_name = fields[2],
                    activity_name_telugu = fields[3],
                    activity_id = fields[4],
                    start_timestamp = fields[5],
                    end_timestamp = fields[6],
                    total_hours = fields[7],
                    total_area = fields[8],
                    area_unit = fields[9],
                    chemical_used = fields[10],
                    chemical_used_telugu = fields[11],
                    seed_used = fields[12],
                    seed_used_telugu = fields[13],
                    machine_used = fields[14],
                    machine_used_telugu = fields[15],
                    implement_used = fields[16],
                    implement_used_telugu = fields[17],
                    image_urls = fields[18],
                    plot_id = fields[19],
                    plot_id_telugu = fields[20],
                    trajectory = fields[21],

                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(activity,activityAdmin)

class offerinquiryAdmin(admin.ModelAdmin):
    list_display= ('id','user_id','offer_id')

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)

            file_data = csv_file.read().decode("utf-8")
            csv_data = file_data.split("\n")

            for x in csv_data:
                fields = x.split(",")
                created = customer.objects.update_or_create(
                    name = fields[0],
                    balance = fields[1],
                    )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)

        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)
admin.site.register(offer_inquiry,offerinquiryAdmin)

class live_feedAdmin(admin.ModelAdmin):
    list_display= ('id','started_by_user_id','org_id','start_timestamp','end_timestamp','url','notes','status','agenda')
    autocomplete_fields = ('started_by_user_id','org_id')
    
admin.site.register(live_feed,live_feedAdmin)

class LiveFeedUserAdmin(admin.ModelAdmin):
    list_display= ('id','user','live_feed','status')
    autocomplete_fields = ('user',)
    
admin.site.register(LivefeedUser,LiveFeedUserAdmin)

class complianceAdmin(admin.ModelAdmin):
    list_display= ('id','user_id','status','document_type','document_name','file_type','file_url1','file_url2','file_url3','file_url4','file_url5')
    autocomplete_fields = ('user_id',)

admin.site.register(compliance,complianceAdmin)

class input_catalogueAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','status','added_by_user_id','timestamp','updated_at','name','name_hindi','brand','brand_hindi','sizes_available','product_images','size_unit','size_unit_hindi','short_description','long_description','short_description_hindi','long_description_hindi','mrp','price','discount_percentage')
    autocomplete_fields = ('added_by_user_id',)
admin.site.register(input_catalogue,input_catalogueAdmin)


class ChangeOrgRoleAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','user','created_at','updated_at')
    autocomplete_fields = ('user',)
admin.site.register(ChangeOrgRole,ChangeOrgRoleAdmin)

class farmer_requestAdmin(admin.ModelAdmin):
    list_display= ('id','status','org_id','user_id','product_id','affected_images','description')
    autocomplete_fields = ('user_id','org_id')

admin.site.register(farmer_request,farmer_requestAdmin)

class user_reportingAdmin(admin.ModelAdmin):
    list_display= ('id','user_id','blocked_by_user','timestamp','report','block','comments')
    autocomplete_fields = ('user_id',)

admin.site.register(user_reporting,user_reportingAdmin)

class app_configurationAdmin(admin.ModelAdmin):
    list_display= ('id','minimum_compatible_version','status')
admin.site.register(app_configuration,app_configurationAdmin)

class user_phonenumber_mapAdmin(admin.ModelAdmin):
   list_display= ('phone_no',)
admin.site.register(user_phonenumber_map,user_phonenumber_mapAdmin)


class device_dataReporting(admin.ModelAdmin):
    list_display=('id','device_name')
admin.site.register(DeviceData,device_dataReporting)

class device_user_dataReporting(admin.ModelAdmin):
    list_display=('id','device','user')
    autocomplete_fields = ('user',)

    search_fields=('device__device_name','user__full_name')

admin.site.register(UserDevice,device_user_dataReporting)

class UserDeviceManagementAdmin(admin.ModelAdmin):
    list_display=('id','user','device_id','device_name','device_type','device_os','device_model','is_active','last_used','created_at')
    list_filter = ('device_type','is_active','device_os','created_at','last_used')
    search_fields=('device_id','device_name','user__full_name','device_os')
    autocomplete_fields = ('user',)
    readonly_fields = ('last_used','created_at','updated_at')
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Device Information', {
            'fields': ('user', 'device_id', 'device_name', 'device_type')
        }),
        ('Device Details', {
            'fields': ('device_os', 'device_model', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('last_used', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

admin.site.register(UserDeviceManagement, UserDeviceManagementAdmin)

@staff_member_required
def bd_dash(request):
    org_dict= org_counts(request.GET.get('from_date'),request.GET.get('to_date'),request.GET.get('bd_name'))  
    all_bd=getAllBD()
    print(org_dict)  
    context = dict(
        all_bd=all_bd,
        org_dict=org_dict
    )    
    return render(request, "admin/bd_dash.html", context)



@staff_member_required
def exportBdManager(request):  
    response = HttpResponse(content_type='text/csv')  
    response['Content-Disposition'] = 'attachment; filename="file.csv"'  
    writer = csv.writer(response)  
    org_dict= org_counts(request.GET.get('from_date'),request.GET.get('to_date'),request.GET.get('bd_name'))
    writer.writerow(['Manager Name', 'Total User Created', 'Total Farm Created'])  
    for i,k in org_dict.items():        
        if('user_count' in k.keys()):
            writer.writerow([i, k['user_count'], k['farm_count']]) 
    return response

@staff_member_required
def bd_dash_details(request,name):
    org_dict_user= org_details_counts(name,request.GET.get('from_date'),request.GET.get('to_date')) 
    org_dict_farm=org_details_counts_farm(name,request.GET.get('from_date'),request.GET.get('to_date'))
      
    context = dict(
        org_dict_user=org_dict_user,
        org_dict_farm=org_dict_farm,
        name=name,
    )    
    return render(request, "admin/bd_dash_details.html", context)


class AuthenticationTokenAdmin(admin.ModelAdmin):
    list_display=('key','user')
    autocomplete_fields = ('user',)
    search_fields = ('user__full_name',)



admin.site.register(AuthenticationToken,AuthenticationTokenAdmin)

class OrganizationDocAdmin(admin.ModelAdmin):
    pass
admin.site.register(OrganizationDoc,OrganizationDocAdmin)

class TagTypeAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'is_active', 'created_at')
    search_fields = ('name', 'category')
    list_filter = ('category', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('category', 'name')
admin.site.register(TagType,TagTypeAdmin)

class TagAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'color', 'created_at')
    search_fields = ('name', 'type__name', 'type__category')
    list_filter = ('type__category', 'type')
    autocomplete_fields = ('type',)
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        file=request.FILES.get('image')
        if file:
            path=image_upload(file)
            obj.image =path

        super().save_model(request, obj, form, change)

admin.site.register(Tag,TagAdmin)

class TagOrganizationAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display = ('id', 'organization', 'tag', 'created_at', 'updated_at')
    search_fields = ('organization__org_name', 'organization__company_id', 'tag__name')
    list_filter = ('tag', 'created_at')
    autocomplete_fields = ('organization', 'tag')
    ordering = ('-created_at',)
admin.site.register(TagOrganization,TagOrganizationAdmin)

@admin.register(farmCropMaster)
class FarmCropMasterAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display = ("farm", "crop", "created_at", "updated_at")
    search_fields = ("farm__name", "crop__name")
    autocomplete_fields = ("farm", "crop")
