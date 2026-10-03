from django.urls import path
from . import views

#update_farm
urlpatterns = [
    path('get-all-activity/', views.GetAllActivity.as_view(),name='getallactivity'),
    path('get-all-activity-pp/', views.GetAllActivityPP.as_view(),name='getallactivitypp'),
    path('get-activity-fields/<farm_id>/<activity_record_id>/', views.GetActivityFields.as_view(),name='getallactivityfields'),
    path('create-das-activity/', views.CreateActivityDas.as_view(),name='createdasactivity'),
    path("edit-das-activity/<int:activity_id>/", views.EditActivityDas.as_view()),
    path('get-farmer-activity/<farmerid>/', views.GetFarmerActivity.as_view(),name='getfarmeractivity'),
    
    path('pp-get-farmer-activity/<farm_id>/', views.PPGetFarmerActivity.as_view(),name='ppgetfarmactivity'),

    path('get-all-record/', views.GetAllOtherActivity.as_view(),name='getallrecord'),
    path('create-record/', views.CreateOTRDas.as_view(),name='createrecord'),
    path('get-farmer-record/<farmerid>/', views.GetFarmerOTRActivity.as_view(),name='getfarmerrecord'),

    path('get-activity-count/', views.GetActivityCount.as_view(),name='getfarmerrecord'),
    path('get-activity-list/<activity_id>/', views.GetActivityFPO.as_view(),name='getfarmerlist'),
    path('task/', views.CreateTaskBD.as_view(),name='createtask'),
    path('task-update/', views.UpdateTaskBD.as_view(),name='updatetask'),
    path('subtask/', views.CreateSubTaskBD.as_view(),name='createsubtask'),
    path('get-followup-calendar/', views.GetFollowupCalendar.as_view(),name='get-followup'),
    
    path('subtask/<taskid>/', views.CreateSubTaskBD.as_view(),name='getsubtask'),

    path('get-bd-user/', views.GetBDListForManager.as_view(),name='getbduser'),
    path('get-bd-manager/', views.GetBDManagerList.as_view(),name='getbdmanager'),
    path('get-status-handle/', views.GetStatusHandle.as_view(),name='getstatushandle'),
    # path('get-crop-analytic/', views.CropDiseaseIdentification.as_view(),name='getcropanalytic'),

    path('create_assistant/', views.CreateAssistantView.as_view(), name='create_assistant'),
    path('update_assistant/', views.UpdateAssistantView.as_view(), name='update_assistant'),
    path('get_assistant_id/', views.GetAssistantIDViewForCropIdentification.as_view(), name='get_assistant_id'),
    path('create_thread/', views.CreateThreadViewForCropIdentification.as_view(), name='create_thread'),
    path('send_conversation/', views.SendConversationView.as_view(), name='send_image'),
    path('run_conversation/', views.RunTheConversationView.as_view(), name='run_conversation'),
    path('list_runs/', views.ListTheRunView.as_view(), name='list_runs'),
    path('get_runs/', views.GetTheRunView.as_view(), name='list_runs'),
    path('get_message_of_thread/', views.GetTheMessagesFromThreadView.as_view(), name='list_runs'),
    path('get-farm-report/<farm_id>', views.GetFarmReportList.as_view(), name='get_farm_report'),
    path('send-request-report/<farm_id>', views.SendRequestForFarmReport.as_view(), name='send_request_report'),
    path('update-farm/<farm_id>', views.UpdateFarm.as_view(), name='update_farm'),
    path('check-if-request-sent/<farm_id>', views.GetCurrentRequest.as_view(), name='check_if_request_sent'),
    path('show-farm-cibil-report/<farm_id>/<report_id>', views.ShowFarmReport.as_view(), name='show_farm_cibil_report'),
    path('send-mail-report/', views.SendMailForRequest.as_view(), name='send_mail_report'),


    path('send-conversation-ms/', views.SendConversationMS.as_view(), name='send_conversation_ms'),
    path('remedy-send-conversation-ms/', views.RemedySendConversationMS.as_view(), name='send_conversation_ms'),
    path('get-message-conversation-ms/', views.GetTheMessagesFromThreadViewMS.as_view(), name='get_message_conversation_ms'),
    path('project/<int:project_id>/tasks/', views.CreateProjectTask.as_view(), name='project-tasks'),
    
    path('send-conversation-internal/', views.SendConversationInternal.as_view(), name='send_conversation_internal'),
    path('get-message-conversation-internal/', views.GetTheMessagesFromThreadViewInternal.as_view(), name='get_message_conversation_internal'),


    path('project-task-farm/', views.CreateProjectTaskFarm.as_view(), name='project-tasks-farm'),
    path('project-task-farm/<int:project_task_id>/', views.CreateProjectTaskFarm.as_view(), name='project-tasks-farm-with-id'),


    path('assign-today-task', views.AssignTask.as_view(), name='assign-today-task'),

    path('get-weather-based-details/<farm>/', views.GetWeatherBasedDetails.as_view(), name='get-weather-based-details'),
    
    path('training/', views.TrainingExecutionAPI.as_view(), name='training'),
    path('training-execution/', views.TrainingExecutionListAPI.as_view(), name='training'),
    path('training/form/<int:training_id>/', views.TrainingFormAPIView.as_view(), name='trainingform'),
    path('ct-questions/', views.CtQuestionsAPIView.as_view(), name='ct-questions'),
    path('ct-questions/response/', views.CtQuestionsFarmAPIView.as_view(), name='ct-questions-response-post'),
    path('ct-questions/response/<int:question_id>/<int:user_id>/<int:farm_id>/', views.CtQuestionsFarmAPIView.as_view(), name='ct-questions-response'),

    # Drone Spray Bookings
    path('drone-sprays/', views.DroneSprayListCreate.as_view(), name='drone_spray_list_create'),
    path('drone-sprays/<int:booking_id>/', views.DroneSprayDetail.as_view(), name='drone_spray_detail'),
    path('drone-sprays/<int:booking_id>/execute/', views.ExecuteDroneSprayBooking.as_view(), name='execute_drone_spray_booking'),
    path('drone-sprays/<int:booking_id>/status/', views.DroneSprayStatusUpdate.as_view(), name='update_drone_spray_status'),
    path('drone-sprays/webhook/', views.DroneSprayWebhook.as_view(), name='drone_spray_webhook'),

    
]