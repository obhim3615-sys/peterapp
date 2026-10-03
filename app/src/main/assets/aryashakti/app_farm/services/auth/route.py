from django.urls import path
from . import api

urlpatterns = [
    path('otp/verify', api.OtpVerify.as_view()),
    path('otp/verify-by-admin', api.OtpVerifyByAdmin.as_view()),
    path('signup', api.signup.as_view()),
    path('create_farmer', api.CreateFarmer.as_view()),
    path('send-otp', api.SendOtp.as_view()),
]