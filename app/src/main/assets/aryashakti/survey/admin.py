from django.contrib import admin
from import_export.admin import ExportActionMixin, ImportMixin
from .models import *
from django.db import models
# Register your models here.
from django.forms import Textarea
from django.urls import reverse
from django_json_widget.widgets import JSONEditorWidget
from django import forms
try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField

class SurveyAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','name','created_by','price','started_at','valid_till')
    list_filter= ('created_at','updated_at','created_by','started_at','valid_till')
    search_fields = ('name','created_by__full_name')

    def save_model(self, request, obj, form, change):
        # Save the model instance
        super().save_model(request, obj, form, change)
        if not obj.link_form:
            # Generate the complete URL for the saved survey
            survey_url = reverse('savesurvey', args=[str(obj.id)])
            complete_url = request.build_absolute_uri(survey_url)

            # Update the link_form field with the complete URL
            obj.link_form = complete_url
        obj.save()

    # readonly_fields=['created_by']

    # def save_model(self, request, obj, form, change):
    #     obj.created_by_id=request.user.id        
    #     obj.save()



admin.site.register(Survey,SurveyAdmin)



class UserSurveyModelForm(forms.ModelForm):
    class Meta:
        model = UserSurvey
        fields = '__all__'
        widgets = {
            'response': JSONEditorWidget(options={
                'mode': 'tree',  # Use 'tree' mode to show JSON in a tree view
                'indentation': 2,  # Number of spaces for indentation
                'theme': 'light',
                  # Use 'light' theme (optional)
                # Add more options here as needed
            }),
        }

class UserSurveyAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    readonly_fields = ('user','survey',)
    list_display= ('id','user','survey','status','created_at','updated_at')
    list_filter= ('created_at','updated_at','status','user','survey')
    search_fields = ('name','survey__name','user__full_name')
    formfield_overrides = {
        JSONField: {'widget': JSONEditorWidget(options={'mode': 'tree', 'indentation': 2, 'theme': 'light', 'readOnly': True})},
    }
    


admin.site.register(UserSurvey,UserSurveyAdmin)

class SurveyTypeAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','name','created_at','updated_at')
    list_filter= ('created_at','updated_at','name')
    search_fields = ('name',)
    

admin.site.register(SurveyType,SurveyTypeAdmin)

class SurveyFieldsAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','survey','name','type','is_required','status','created_at','updated_at')
    list_filter= ('created_at','updated_at','survey__name')
    search_fields = ('survey__name','name')
    

admin.site.register(SurveyFields,SurveyFieldsAdmin)


