from django.urls import path
from . import views

urlpatterns = [
    path('get-countries-list', views.GetCountryList.as_view()),
    path('get-custom-form-details', views.GetCustomFormDetails.as_view()),
    path('get-custom-forms', views.GetCustomForms.as_view()),
    path('get-user-ajax', views.GetUserAjax.as_view()),
    path('live/', views.liveness, name='liveness'),
    path('ready/', views.readiness, name='readiness'),
    path('search-user-name-phone', views.SearchUserByNamePhone.as_view()),
    path('send-farm-csv', views.SendDailyFarmAddedDetails.as_view()),
]