from django.urls import path
from . import views

urlpatterns = [
    path('sms-templates', views.GetSmsTemplateList.as_view()),
    path('sms-template-detail', views.GetSmsTemplateDetail.as_view()),
    path('send-group-sms', views.SendGroupSms.as_view()),
    path('get-community-share', views.GetCommunitiesShare.as_view()),
]