from django.urls import path,include
#from django.conf.urls import url

from . import views

#update_farm
urlpatterns = [
    path('get-all-survey', views.GetSurvey.as_view(),name='getallsurvey'),
    path('save-survey/<surveyid>/', views.SurveySubmitView.as_view(),name='savesurvey'),
    path('create-survey', views.CreateSurvey.as_view(),name='createsurvey'),
    path('create-survey-web', views.CreateSurveyWeb.as_view(),name='createsurvey'),
    path('get-user-survey-details', views.GetUserSurveyData.as_view(),name='getusersurveydetails'),
]