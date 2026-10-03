from django.urls import path,include
#from django.conf.urls import url

from . import views

#update_farm
urlpatterns = [
    path('test-api/', views.TestFunction.as_view(),name='testapi'),
    path('get-subscription/', views.GetSubscription.as_view(),name='getsubscription'),
    path('get-service/', views.GetServices.as_view(),name='getservice'),
    path('get-service-user/', views.GetServicesUser.as_view(),name='getserviceuser'),
    path('verify-coupon/', views.VerifyCoupon.as_view(),name='verifycoupon'),
    path('test-api/', views.TestFunction.as_view(),name='testapi'),
]