from django.urls import path
from . import views

urlpatterns = [
    path('details', views.GetFarmDetails.as_view()),
    path('run-script', views.FarmCategoryScript.as_view()),
    path('get-projected-farms/<crop_id>', views.GetProjectedFarms.as_view()),
    path('get-whole-farm/<crop_id>', views.GetWholeFarm.as_view()),
    path('get-all-organization-crop/', views.GetOrganizationCrop.as_view()),
    path('get-all-stressed-farm/', views.GetTotalStressedFarm.as_view()),
    path('farm-details', views.FarmDetails.as_view()),
    path('run-cron-job', views.RunCronJob.as_view()),
    path('get-nearest-warehouse', views.GetNearestWarehouse.as_view()),
    path('get-buyer-seller', views.GetBuyersSellers.as_view()),
    path('create-interest', views.AddInterestUser.as_view()),
    path('get-nearest-warehouse-clusture', views.GetWarehouseClusterList.as_view()),
    path('getclusture-by-id/<warehouse_id>/', views.GetWarehouseClusterByID.as_view()),
    path('create-farm-boundary/<farm_id>/', views.CreateManualFarmBoundary.as_view()),
    path('get-all-warehouse', views.GetWarehouseList.as_view()),

     #Prithvi pro
     path('get-wholefarm-pp/', views.GetWholeFarmPrithviPro.as_view()),
     path('get-farm-list', views.GetFarmListWithOrganization.as_view()),
     path('get-single-farm-data/<farm_id>/', views.GetSingleFarmData.as_view()),
     path('locations/', views.GetLocations.as_view()),

    path("cluster-market/", views.ClusterSearchView.as_view(), name="cluster-search"),
]