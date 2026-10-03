from django.urls import path
from . import views

#update_farm
urlpatterns = [
    path('create-link', views.CreateOrder.as_view(),name='createlink'),
    path('payment-redirect', views.PaymentRedirect.as_view(),name='paymentredirect'),
    path('payment-redirect-common', views.PaymentRedirectCommon.as_view(),name='paymentredirectcommon'),
    path('bank-validation', views.UserBankValidation.as_view(),name='bankvalidation'),
    path('bank-validation-by-admin', views.UserBankValidationByAdmin.as_view(),name='bankvalidationbyadmin'),
    path('bank-validation-redirect', views.BankValidationRedirect.as_view(),name='bankvalidationredirect'),
    path('razorpay-webhooks', views.RazorpayWebhooks.as_view(),name='razorpaywebhooks'),


    path('bank-validation-pams', views.UserBankValidationPams.as_view(),name='bankvalidation'),
    path('bank-validation-by-admin-pams', views.UserBankValidationByAdminPams.as_view(),name='bankvalidationbyadmin'),
        
    
]