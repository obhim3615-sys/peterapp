from django.urls import path
from . import views

urlpatterns = [
    path('page_details', views.GetPageDetails.as_view()),
    path('get-config', views.GetConfig.as_view()),
    path('get-lang-content', views.GetLanguageContent.as_view()),
]