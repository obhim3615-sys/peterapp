from django.urls import path,include
from .services.farmer import route as farmer_api
from .services.news import route as news_api
from .services.auth import route as auth_api
from .services.organizations import route as org_api

urlpatterns = [
    path('farmer/', include(farmer_api)),
    path('news/', include(news_api)),
    path('auth/', include(auth_api)),
    path('org/', include(org_api)),
]