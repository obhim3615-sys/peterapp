from django.urls import path,include
#from django.conf.urls import url

from . import views

#update_farm
urlpatterns = [
    path('pan-verify/', views.Pan.as_view(),name='panverify'),  
    path('verify-token/', views.Verify.as_view(),name='verifytoken'),  
    path('pan-create/', views.PanCreate.as_view(),name='pancreate'),
    path('pan-form-view/', views.PanSubmitView.as_view(),name='panview'),
    path('pan-url/', views.PanUrl.as_view(),name='panviewurl'),
    path('digilocker-url/', views.DigiLockerUrlCreation.as_view(),name='digilockerurl'),
    path('digilocker-url-user/<int:user_id>/', views.DigiLockerUrlCreation.as_view(),name='digilockerurluser'),
    path('digilocker-eadhar/', views.DigiLockerGetEAdhar.as_view(),name='digilockeradhar'),
    path('gstin-pan/', views.GetGSTByPAN.as_view(),name='gstinpan'),
    path('get-verification-status/', views.GetVerificationStatus.as_view(),name='getverification'),
    path('get-verification-status-user-id/<int:user_id>/', views.GetVerificationStatus.as_view(), name='getverification_with_user_id'),
    path('get-user-journey/', views.GetUserJourney.as_view(),name='getuserjourney'),
    path('verify-adhar/<type>/<userid>/<director>/<verified_by_id>/', views.UploadAdharData.as_view(),name='verifyadhar'),
    path('get-cibil/', views.CreateLoanLead.as_view(),name='createlead'),
    path('director-verify/', views.ViewForDirectorVerification.as_view(),name='directorverify'),
    path('director-verify-cibil/', views.ViewForDirectorCibil.as_view(),name='directorverifycibil'),
    path('verify-adhar-completed/', views.VerifyAdharCompleted.as_view(),name='verifyadharcompleted'),
    path('delete-director/', views.DeleteDirector.as_view(),name='deletedirector'),
    path('get-digio-template/', views.GetTemplate.as_view(),name='getdigiotemplate'),
    path('get-digio-files/<docid>', views.DownloadDoc.as_view(),name='getdigiofiles'),
    path('get-digio-files', views.DownloadAllDoc.as_view(),name='getdigiofilesall'),
    path('generate-doc', views.GenerateDoc.as_view(),name='generatedoc'),
    path('check-generation-doc', views.CheckIfDataCreated.as_view(),name='checkgenerationdoc'),
    path('upload-digio-files/<docid>', views.UploadDocForTemplate.as_view(),name='uploaddigiofiles'),
    path('verify-consolidation/', views.GetConsolidateData.as_view(),name='verifyconsolidation'),  
    path('check-if-lead/', views.GetPanVerificationDetails.as_view(),name='check-if-lead'),  
    path('verify-logic', views.VerifyLogic.as_view(),name='verify-logic'),  
    path('upload-bank-statement', views.UploadBankStatement.as_view(),name='upload-bank-statement'),  
    path('adhar-send-otp', views.AdharSendOTP.as_view(),name='adhartsendotp'),  
    path('adhar-otp-verify', views.AdharOTPVerify.as_view(),name='adharotpverify'),  
    path('adhar-otp-verify/<user_id>', views.AdharOTPVerify.as_view(),name='adharotpverifyuser'), 
    path('adhar-image-verify', views.AdharVerificationByImage.as_view(),name='adharimageverify'),  
    path('adhar-image-verify-single/', views.AdharVerificationByImageSingle.as_view(),name='adharimageverifysingle'),  
    path('adhar-image-verify/<user_id>', views.AdharVerificationByImage.as_view(),name='adharimageverifyuser'),  
    path('boundary-update/', views.Test.as_view(),name='boundaryupdate'),  

    path('esign-verify-callback', views.EsignCompleted.as_view(),name='esignverifycallback'),
    path('esign-contract-initiate', views.SignzyInitiateContractAPIView.as_view(),name='esigncontractinitiate'),
    
]