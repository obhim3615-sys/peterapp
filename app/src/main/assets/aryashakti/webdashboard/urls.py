from django.urls import path
from .views import *

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('dasboard-withcsv/', dashboard_view_csv, name='dashboardcsv'),
    path('dasboard-farms-for-activity/', dashboard_farm_for_activity, name='dashboardfarmforactivity'),
    path('dasboard-activity-for-farm/', dashboard_activity_for_farm, name='dashboardactivityforfarm'),
]
