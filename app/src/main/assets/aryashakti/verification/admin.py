from django.contrib import admin
from .models import *
from import_export.admin import ExportActionMixin, ImportMixin

# Register your models here.

class VerificationAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    readonly_fields=('created_by','updated_by')
    autocomplete_fields = ('created_by','updated_by')

    def save_model(self, request, obj, form, change):
        if obj.pk:
            obj.updated_by=request.user
        else:
            obj.created_by=request.user
        
        obj.save()

admin.site.register(Document,VerificationAdmin)


class UnsecureLoanStepAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    readonly_fields=('created_by','updated_by')
    autocomplete_fields = ('created_by','updated_by')
    def save_model(self, request, obj, form, change):
        if obj.pk:
            obj.updated_by=request.user
        else:
            obj.created_by=request.user
        
        obj.save()

admin.site.register(UnsecureLoanStep,UnsecureLoanStepAdmin)



class UserUnsecureLoanAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','user','unsecure_step','status')
    list_filter= ('unsecure_step__name',)
    search_fields = ('user__full_name','unsecure_step__name')
    autocomplete_fields = ('user',) 


admin.site.register(UserUnsecureLoan,UserUnsecureLoanAdmin)

# class AdharVerificationAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
#     list_display= ('id','user')
#     search_fields = ('user__full_name',)
#     autocomplete_fields = ('user',) 


# admin.site.register(AdharVerifcation,AdharVerificationAdmin)

# class PanVerificationAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
#     list_display= ('id','user','pan_number','pan_dob','pan_name','father_name')
#     search_fields = ('user__full_name','pan_number')
#     autocomplete_fields = ('user','organization') 


# admin.site.register(PanVerifcation,PanVerificationAdmin)

# class GSTVerificationAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
#     list_display= ('id','user','gstin','registrationDate','principalAddress')
#     search_fields = ('user__full_name','gstin')
#     autocomplete_fields = ('user',) 


# admin.site.register(GSTData,GSTVerificationAdmin)



class UserVerificationDocumentAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','user','document_type','document_id','status','verified_by')
    list_filter= ('document_type__name',)
    search_fields = ('user__full_name','document_type__name')
    autocomplete_fields = ('user','verified_by') 


admin.site.register(UserVerificationDocument,UserVerificationDocumentAdmin)

class OrganizationConsolidationDirectorAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','user','pan','director','director_pan','director_state','pincode','address','email','dob','mobile_number','is_adhar_verified')
    list_filter= ('director_state',)
    search_fields = ('user__full_name','pan__pan_number')
    autocomplete_fields = ('user',) 
    

admin.site.register(OrganizationConsolidationDirector,OrganizationConsolidationDirectorAdmin)




class TemplateDataAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','template_name','type',)
    search_fields = ('template_name','type',)

    
admin.site.register(TemplateData,TemplateDataAdmin)

class TemplateKeyAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','template_data','key',)
    search_fields = ('template_data__template_name','key')

admin.site.register(TemplateKey,TemplateKeyAdmin)


class BDProfinAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','name','email',)
    search_fields = ('name','email')

admin.site.register(BDProfin,BDProfinAdmin)



class OrganizationKeyValuesAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','organization','fpo_name','is_completed')
    #list_filter= ('organization',)
    search_fields = ('organization__org_name','fpo_name')
    autocomplete_fields = ('organization',) 


admin.site.register(OrganizationKeyValues,OrganizationKeyValuesAdmin)


class OrganizationTemplateAdmin(admin.ModelAdmin):
    list_display= ('id','organization','template','file_url')
    #list_filter= ('organization',)
    search_fields = ('organization__org_name','fpo_name')
    autocomplete_fields = ('organization','template',) 


admin.site.register(OrganizationTemplate,OrganizationTemplateAdmin)


