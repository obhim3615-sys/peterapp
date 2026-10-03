from django.urls import path
from . import views

#update_farm
urlpatterns = [
    path('member', views.AddMember.as_view()),
    path('member-bank-validation', views.MemberBankValidation.as_view(),name='memberbankvalidation'),
    path('kutumbs-summary', views.KutumbsSummary.as_view()),
    path('incomplete-kutumbs', views.GetIncompleteKutumbs.as_view()),
    path('claimable-kutumbs', views.GetClaimableKutumbs.as_view()),
    path('add-nominee', views.AddNominee.as_view()),
    path('verify-consent', views.VerifyConsent.as_view()),
    path('cash-payment', views.CashPayment.as_view()),
    path('online-payment', views.OnlinePayment.as_view()),
    path('same-bank-account', views.SameBankAccount.as_view()),


    path('insurance-estimate/', views.AadhaarEstimateAPIView.as_view()),
    path('insurance-enroll/', views.AadhaarEnrollmentAPIView.as_view()),
    path('insurance-bank-verification/', views.InsuranceBankValidation.as_view()),
    path('insurance-payment/', views.EnrollmentPaymentUrl.as_view()),
    path('check-status-insurance/<insurance_id>/', views.CheckStatus.as_view()),
    path('insurance-enroll-esign-success/<ref_id>/', views.UpdateInsuranceEsignSuccess.as_view(),name="esignSuccess"),
    path('insurance-enroll-esign-failed/<ref_id>/', views.UpdateInsuranceEsignFailure.as_view(),name="esignFailed"),
    path('verify-consent-insurance', views.VerifyConsentInsurance.as_view()),

]