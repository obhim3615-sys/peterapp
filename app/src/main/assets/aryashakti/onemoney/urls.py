from django.urls import path
from . import views

#update_farm
urlpatterns = [
    path('verify/', views.BankVerify.as_view(),name='bankverify'),
    path('redirect/', views.OnemoneyRedirect.as_view(),name='onemoneyredirect'),

    path('consent_webhook', views.ConsentWebhook.as_view(),name='consentwebhook'),
    path('data_webhook', views.DataWebhook.as_view(),name='datawebhook')
]