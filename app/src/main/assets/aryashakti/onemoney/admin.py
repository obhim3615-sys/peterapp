from django.contrib import admin
from .models import OnemoneyConsent, BankStatementVerifcation

# Register your models here.
class OnemoneyConsentAdmin(admin.ModelAdmin):
    list_display= ('id','user','status','consent_handle','consent_id','vua','timestamp','created_at','updated_at')
    list_filter= ('user_id',)
    search_fields = ('consent_handle','consent_id')

class BankStatementVerifcationAdmin(admin.ModelAdmin):
    list_display= ('consent','linkReferenceNumber','maskedAccountNumber','fiType','bank','startDate','endDate','bank_statement','created_at','updated_at')
    list_filter= ('consent_id__user',)


admin.site.register(OnemoneyConsent,OnemoneyConsentAdmin)
admin.site.register(BankStatementVerifcation,BankStatementVerifcationAdmin)