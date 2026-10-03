from django.contrib import admin
from import_export.admin import ExportActionMixin, ImportMixin
from . import models

# Register your models here.
class OrderAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','paid_by','paid_by_name','paid_by_phone','paid_by_role','price','total_discount','taxes','final_price','status','coupon','coupon_discount','payment_id','payment_link_status','created_at','updated_at')
    list_filter= ('status',)
    search_fields = ('paid_by_name','paid_by_phone')

class UserOrderAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','order','user','created_at','updated_at')

class UserBankAccountAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','user','name','contact','email','account_num','ifsc','contact_id','fund_account','fav_id','created_at','updated_at')

class BankAccountAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','name','contact','email','account_num','ifsc','contact_id','fund_account','fav_id','status','verified_by','created_at','updated_at')
    list_filter= ('status',)
    search_fields = ('name','contact','account_num')
    autocomplete_fields = ('verified_by',)

class PaymentAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','payment_type','amount','status','response','payment_link_id','created_at','updated_at')
    list_filter= ('status','payment_type')
    search_fields = ('amount','payment_link_id')

class PayoutAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display= ('id','payout_id','amount','status','response','created_at','updated_at')
    list_filter= ('status',)
    search_fields = ('amount','payout_id')

class CastlerVirtualAccountAdmin(ImportMixin, ExportActionMixin, admin.ModelAdmin):
    list_display=['id','user','virtual_account_id','ifsc','status','created_at','updated_at']
    search_fields = ('user__full_name','user__organization__org_name')

admin.site.register(models.CastlerVirtualAccount,CastlerVirtualAccountAdmin)
admin.site.register(models.Order,OrderAdmin)
admin.site.register(models.UserOrder,UserOrderAdmin)
admin.site.register(models.UserBankAccount,UserBankAccountAdmin)
admin.site.register(models.Payment,PaymentAdmin)
admin.site.register(models.Payout,PayoutAdmin)
admin.site.register(models.BankAccount,BankAccountAdmin)
