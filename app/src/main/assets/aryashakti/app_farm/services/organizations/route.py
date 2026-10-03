from django.urls import path
from . import api

urlpatterns = [
    path('list', api.GetOrgList.as_view()),
    path('list-details', api.GetOrganisationList.as_view()),
    path('type_list', api.GetOrgTypesList.as_view()),
    path('detail', api.GetOrgDetail.as_view()),
    path('create', api.OrgCreate.as_view()),
    path('upload-doc-org', api.UploadOrganizationDoc.as_view()),
    path('send-notification', api.SendNotification.as_view()),
    path('get-tags', api.GetTags.as_view()),
    path('get-tags-organization', api.GetOrganizationWithTag.as_view()),
    path('get-agenda', api.GetAgendas.as_view()),    
    path('update-organization', api.UpdateOrganizationValues.as_view()),

]
