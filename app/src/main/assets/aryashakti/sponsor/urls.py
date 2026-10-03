from django.urls import path,include
#from django.conf.urls import url

from . import views

#update_farm
urlpatterns = [
    path('get-sponsored-farmer',views.GetSponsoredFarmer.as_view(),name="getsponsoredfarmer"),
    path('get-sponsored-organization',views.GetOrganizationFarmer.as_view(),name="getorganizationfarmer")
]