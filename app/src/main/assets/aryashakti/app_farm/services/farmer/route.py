from django.urls import path
from . import api

urlpatterns = [
    path('farm/stress', api.farm_stress.as_view()),
    path('farm/test', api.testroute),
    path('farm/social_list', api.social_list.as_view()),
    path('farm/activity_list', api.activity_list.as_view()),
    path('update_farmer', api.UpdateFarmer.as_view()),
    path('update-sowing-crop/', api.UpdateSowingDateCrop.as_view()),
    path('sms_farmer_list', api.SmsFarmerList.as_view()),
    path('soil-report', api.GetSoilReport.as_view()),
    path('create', api.CreateFarmerBySponsor.as_view()),

    path('get_address', api.GetAddress.as_view()),
    path('get_roles', api.GetRoles.as_view()),
    path('upload_users', api.UploadUserCSV.as_view()),
    path('download_csv_sample', api.DownloadUserUploadCSV.as_view()),
    path('get_all_farmers', api.GetAllFarmersList.as_view()),
    path('sessions_list/', api.GetSessions.as_view()),
    path('delete_profile', api.DeleteFarmer.as_view()),

    
]