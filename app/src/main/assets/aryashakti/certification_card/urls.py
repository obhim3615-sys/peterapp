from django.urls import path,include,re_path
#from django.conf.urls import url
from django.views.generic import RedirectView

from . import views

#update_farm
urlpatterns = [
    path('get-certifications/', views.GetAllCertification.as_view(),name='getcertification'),
    path('create-certification/', views.AddCeritfication.as_view(),name='createcertification'),
    path('get-certification-farmer/<farmerid>/', views.GetCertificationOfFarmer.as_view(),name='getcertificationfarmer'),
    path('get-badge/<farmerid>/', views.GetUserBadge.as_view(),name='getbadge'),       
    # path('get-graph/<farmid>/<certificateid>/', views.GetGraph.as_view(),name='getgraph'),  
    path('upload-graph/', views.UploadCSVGraph.as_view(),name='uploadgraph'),          
       
]