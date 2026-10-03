from django.contrib import admin
from subscription_service.models import *
# Register your models here.

class SubscriptionAdmin(admin.ModelAdmin):
    list_display= ('id','name','slug','type','status','price','validity','package_type','color')
    list_filter= ('validity','package_type','type')
    search_fields = ('name','slug')

admin.site.register(Subscription,SubscriptionAdmin)


class ServiceAdmin(admin.ModelAdmin):
    list_display= ('id','name','slug','type','status','price','unit')
    list_filter= ('unit','type')
    search_fields = ('name','slug')

admin.site.register(Service,ServiceAdmin)

class SubscriptionServiceAdmin(admin.ModelAdmin):
    list_display= ('id','subscription','service','validity')
    list_filter= ('subscription','service')
    search_fields = ('subscription__name','service__full_name')


admin.site.register(SubscriptionService,SubscriptionServiceAdmin)

class UserServiceAdmin(admin.ModelAdmin):
    list_display= ('id','user','service','user_subscription','validity','remaining')
    list_filter= ('service__name',)
    search_fields = ('user__full_name','service__name','user_subscription__subscription__name')
    autocomplete_fields = ('user','user_subscription','service') 


admin.site.register(UserService,UserServiceAdmin)

class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display= ('id','user','subscription','validity','sponsored_by')
    list_filter= ('subscription__name',)
    search_fields = ('user__full_name','subscription__name','sponsored_by__full_name')
    autocomplete_fields = ('user','sponsored_by') 

admin.site.register(UserSubscription,UserSubscriptionAdmin)


class CouponAdmin(admin.ModelAdmin):
    list_display= ('id','name','value','type')
    list_filter= ('name','value','type')
    search_fields = ('name','value','type')
    


admin.site.register(Coupon,CouponAdmin)

class CouponUserAdmin(admin.ModelAdmin):
    list_display= ('id','coupon','user')
    list_filter= ('coupon',)
    search_fields = ('coupon','user__full_name')
    autocomplete_fields = ('user',) 

admin.site.register(CouponUser,CouponUserAdmin)
