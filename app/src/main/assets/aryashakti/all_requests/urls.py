from django.urls import path
from . import views

urlpatterns = [
    path('new_fpo', views.CreateFpoRequest.as_view()),
    path('farmer_to_fpo', views.CreateFarmerToFpoRequest.as_view()),

    path('list', views.RequestsList.as_view()),
    path('update', views.RequestsUpdate.as_view()),
]