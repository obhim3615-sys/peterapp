from django.contrib import admin

# Register your models here.
from .models import Requests

# Register your models here.
class RequestsAdmin(admin.ModelAdmin):
    list_display= ('id','type','user','organization','status','org_name','org_no','created_at','updated_at')
    list_filter= ('type',)
    search_fields = ('org_name',)


admin.site.register(Requests,RequestsAdmin)