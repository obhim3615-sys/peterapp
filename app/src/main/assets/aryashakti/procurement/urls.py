from django.urls import path
from . import views

#update_farm
urlpatterns = [
    path('register-procurement', views.ProcurementRegisterData.as_view(),name='registerprocument'),
    path('register-procurement/<procurement_register_id>', views.UpdateProcurementData.as_view(),name='registerprocumentupdate'),
    path('procurement-data/<procure_register_id>', views.ProcurementData.as_view(),name='procurement-data'),
    path('payment/<procure_id>', views.PaymentProcure.as_view(),name='paymentprocure'),
    path('payment/', views.PaymentProcure.as_view(),name='paymentprocure'),
    path('download_sample_upload_csv/', views.DownloadProcurementUploadCSV.as_view(),name='downloadcsvsampleprocurement'),
    path('bulk_upload_csv/<procure_register_id>', views.UploadProcurementCSV.as_view(),name='bulkcsvupload'),
    path('get-balance/', views.AxisBankBalanceCheckView.as_view(),name='getbalance'),
    path('get-status/', views.CheckBulkPaymentStatusAPIView.as_view(),name='getstatus'),
    path('generate-qr-auth/', views.EnableGoogleAuthAPIView.as_view(),name='generateqrauth'),

]