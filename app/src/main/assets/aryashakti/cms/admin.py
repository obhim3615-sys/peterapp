from django.contrib import admin

# Register your models here.
from . import models
from app_farm.utils.helper import image_upload
from import_export.admin import ExportActionMixin, ImportMixin
from flat_json_widget.widgets import FlatJsonWidget
from django import forms

class JsonDocumentForm(forms.ModelForm):
    class Meta:
        widgets = {
            'content': FlatJsonWidget,
            'crop_content': FlatJsonWidget,
        }

# Register your models here.
class PageAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','name','language','order','created_at','updated_at')
    list_filter= ('language',)
    search_fields = ('name',)

class SectionAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','name','order','type','page','created_at','updated_at')
    list_filter= ('page','type')
    search_fields = ('name',)

class SubSectionAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','name','section','image_text','image_url','url','order','is_iframe','created_at','updated_at')
    list_filter= ('section',)
    search_fields = ('name',)

    def save_model(self, request, obj, form, change):        
        file=request.FILES.get('image_url')
        if file:
            path=image_upload(file)
            obj.image_url =path

        super().save_model(request, obj, form, change)

class LanguageContentAdmin(ImportMixin, ExportActionMixin,admin.ModelAdmin):
    list_display= ('id','language','created_at','updated_at')
    form= JsonDocumentForm

class SettingAdmin(admin.ModelAdmin):
    list_display= ('id','key','value','type','created_at','updated_at')
    list_filter= ('country',)

admin.site.register(models.Page,PageAdmin)
admin.site.register(models.Section,SectionAdmin)
admin.site.register(models.SubSection,SubSectionAdmin)
admin.site.register(models.LanguageContent,LanguageContentAdmin)
admin.site.register(models.Setting,SettingAdmin)