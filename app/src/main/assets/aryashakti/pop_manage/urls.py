from django.urls import path
from . import views

#update_farm
urlpatterns = [
    path('get-suggestions/<farmid>', views.GetPopActivity.as_view(),name='getsuggestions'),
    path('get-soil-report-list/<farm_id>', views.GetSoilReportsOfFarm.as_view(),name='get-soil-report-list'),
    path('add-soil-test/', views.AddSoilTestPlotAPIView.as_view(), name='add-soil-test'),
    path('fetch-report-soil-test-webhook/', views.NeoPerkWebhookReceiver.as_view(), name='add-soil-test'),
    path('sessions/', views.SessionListView.as_view(), name='session-list'),
    path('farm/check-session/', views.FarmSessionCheckView.as_view(), name='farm-session-check'),
    path('get-pop/<farmid>/', views.ActivityFullPop.as_view(), name='getpop'),
    path('get-pop-group/<pop_group_id>/', views.ActivityPOPFromPOPGroup.as_view(), name='getpopgroupid'),
    path('get-pop/<farmid>/<varietyid>', views.ActivityFullPop.as_view(), name='getpopvarietyk'),
    path('get-activity-compliance/<org_id>/<listing_id>', views.GetActivityComplianceSummary.as_view(), name='getactivitycompliance'),
    path('prithvipro/create-popgroup/', views.CreatePOPGroupFromPrithviPro.as_view(), name='prithvi-create-popgroup'),
    path('prithvipro/upload-pop-activities/', views.UploadPOPActivitiesFromPrithviPro.as_view(), name='prithvi-upload-pop'),
    path('prithvipro/requirements/', views.POPGroupsFromPrithviPro.as_view(), name='prithvi-list-popgroups'),
    path('prithvipro/requirements/list', views.PrithviProRequirementAPIView.as_view(), name='prithvi-list-popgroups'),
    path('prithvipro/get-farm-acre-count/', views.OrgFarmStatsAPIView.as_view(), name='getfarmsumcountacre'),
    path('prithvipro/get-farm-listing-count/', views.ListingCountAPIView.as_view(), name='getfarmlistingcountacre'),
    path('prithvipro/accept-request/', views.AcceptRequirementData.as_view(), name='acceptrequest'),
    path('prithvipro/get-existing-pop-details/<int:buyer_id>/', views.OwnPOPGroupsFromPrithviPro.as_view(), name='getexistingpopgroup'),
    path('get-stages', views.StageListCreateAPI.as_view(), name='getstages'),
    path('get-sub-stages', views.SubStageListCreateAPI.as_view(), name='getsubstages'),
    path('send-pop-notifications', views.SendPopNotifications.as_view(), name='sendpopnotifications'),
    
    path('share-log-save/', views.AddPopShareLog.as_view(), name='sharelogsave'),

]
