from django.shortcuts import render
from rest_framework import status
from app_farm.utils import helper, constants,response as res
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from app_farm.authentication import CustomTokenAuthentication
from .models import *
from rest_framework.pagination import PageNumberPagination
from .serializers import *
from .validator import *
from payment.views import cash_upload
import csv 
from io import TextIOWrapper 
from app_farm.models import user, crop_master,farm
from django.db import transaction
from payment.views import create_payment_link_common
from django.db.models import Sum,Q
from libraries.castler import Castler
from cms.models import Setting
from django.shortcuts import get_object_or_404

# Create your views here.


class ProcurementRegisterData(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

     # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=ProcurementRegister    

    def get_queryset(self):   
        queryset=ProcurementRegister.objects.filter(organization=self.request.user.organization).order_by('-id').all()

        return queryset
    
    def post(self,request):
        try:
            data= request.data
            if 'name' not in data.keys():
                return res.req_response("Bad Request",False,"PR-VPRD-POST-01",status.HTTP_400_BAD_REQUEST)
            procure=ProcurementRegister.objects.create(name=data['name'],organization=request.user.organization,user=request.user)

            if procure:
                procure=ProcurementRegisterSerializer(procure)
                return res.req_response("Procurement register created",True,"",status.HTTP_200_OK,procure.data)
            return res.req_response("Bad Request",False,"PR-VPRD-POST-02",status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return res.req_response("Error "+str(e),False,"PR-VPRD-POST-03",status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    

    def get(self,request):
        queryset = self.get_queryset()      
        page =  self.paginate_queryset(queryset,request)

        procure=None
        if page:          
            procure=ProcurementRegisterSerializer(page,many=True).data
            procure=self.get_paginated_response(procure).data
        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,procure)


class UpdateProcurementData(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request,procurement_register_id):
        try:
            procure=ProcurementRegister.objects.filter(id=procurement_register_id).update(status=False)

            if procure:
                procure=ProcurementRegister.objects.filter(id=procurement_register_id).get()
                procure=ProcurementRegisterSerializer(procure,many=False)
                return res.req_response("Procurement register updated",True,"",status.HTTP_200_OK,procure.data)
            return res.req_response("Bad Request",False,"PR-VPRD-POSTUP-02",status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return res.req_response("Error "+str(e),False,"PR-VPRD-POSTUP-03",status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProcurementData(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

     # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=Procurement   

    def get_queryset(self,procure_register_id):   
        queryset=Procurement.objects.filter(~Q(payment=None),~Q(payment__status=None),procure_register_id=procure_register_id).order_by('-id')

        return queryset
    
    def post(self,request,procure_register_id):
        try:
            data= request.data
            validation = ProcurementValidator(data=data)
            if not validation.is_valid():
                return res.req_response("Bad Request",False,"PR-VPRD-POST-04",status.HTTP_400_BAD_REQUEST,validation.errors)
            if 'type' in data.keys() and data['type'] != "bulk":
                data['type']="single"
            procure=Procurement.objects.create(user_to_id=data.get('user_to_id'),
                                               user_from=request.user,
                                               variety=data.get('variety'),
                                               qty=data.get('qty'),
                                            #    farm_id=data.get('farm_id'),
                                               rate=data.get('rate'),
                                               amount=data.get('amount'),
                                               crop_id=data.get('crop_id'),
                                               description=data.get('description'),
                                               procure_register_id=procure_register_id,
                                               type=data.get('type'))
            
            images = request.FILES.getlist('image_url')  # Assuming 'image_url' is the name of the file input field

            image_urls = []

            for image in images:
                if image is not None:
                    image_url = helper.image_upload(image)
                    image_urls.append(image_url)
                else:
                    image_urls.append("")

            if procure:
                for i in image_urls:      
                    if i:
                        ProcurementImage.objects.create(
                            image_url=i,
                            procurement=procure
                        )
                procure=ProcurementSerializer(procure)

                return res.req_response("Procurement record created",True,"",status.HTTP_200_OK,procure.data)
            return res.req_response("Bad Request",False,"PR-VPRD-POST-02",status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return res.req_response("Error "+str(e),False,"PR-VPRD-POST-03",status.HTTP_500_INTERNAL_SERVER_ERROR)


    def get(self,request,procure_register_id):
        queryset = self.get_queryset(procure_register_id)      
        page =  self.paginate_queryset(queryset,request)

        procure=None
        if page:          
            procure=ProcurementSerializer(page,many=True).data
            procure=self.get_paginated_response(procure).data
        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,procure)





from decimal import Decimal
from datetime import datetime
from libraries.axis_fund_client import AxisFundTransferClient  # Adjust as needed
from libraries.encryption_utils import aes_decrypt_base64  # Adjust as needed
from django.conf import settings
import json
def send_fund_if_sufficient_balance(
    org: AxisBankOrganization,
    beneficiary_name: str,
    beneficiary_account: str,
    beneficiary_ifsc: str,
    beneficiary_bank: str,
    amount: str,
    value_date: str,
    unique_ref: str,
    invoice_number: str,
    txnPaymode="NE"
) -> dict:
    """
    Checks balance via AxisBank, and only initiates fund transfer if sufficient.
    """
    try:
        client = AxisFundTransferClient()

        # Inject override values for balance check
        client.set_dynamic_context(org.corp_code, org.corp_account_number)

        # 🔍 Step 1: Check balance
        balance_response = client.check_account_balance()
        encrypted_data = balance_response.get("GetAccountBalanceResponse", {}).get("GetAccountBalanceResponseBodyEncrypted")

        if not encrypted_data:
            return {
                    "success": False, 
                    "data":{
                        "message": "Missing encrypted balance data from Axis response."
                    }
                    }

        decrypted = aes_decrypt_base64(encrypted_data)
        if isinstance(decrypted, str) :
            return {
                    "success": False, 
                    "data":{
                        "message": decrypted}
                    }
        
        if isinstance(decrypted.get("data", {}), str) :
            return {
                    "success": False, 
                    "data":{
                        "message": decrypted.get("data", {})}
                    }
        
        balance_str = decrypted.get("data", {}).get("Balance")
        
        if not balance_str:
            return {
                    "success": False, 
                    "data":{
                        "message": "Missing 'Balance' field in Axis decrypted response."}
                    }

        balance = Decimal(balance_str)
        amount_decimal = Decimal(amount)

        # 🧮 Step 2: Compare balance
        if balance < amount_decimal:
            return {
                "success": False,
                "data":{
                    "message": f"Insufficient balance: ₹{balance}. Required: ₹{amount}."
                }
            }

        # 💸 Step 3: Proceed to fund transfer
        overrides = {
            "channelId": settings.AXIS_CORP_CHANNEL_ID,
            "corpCode": org.corp_code,
            "paymentDetails": {
                "custUniqRef": unique_ref,
                "corpAccNum": org.corp_account_number,
                "valueDate": value_date,
                "txnAmount": str(amount),
                "beneName": beneficiary_name,
                "beneAccNum": beneficiary_account,
                "beneIfscCode": beneficiary_ifsc,
                "beneBankName": beneficiary_bank,
                "invoiceDetails": [
                    {
                        "invoiceAmount": str(amount),
                        "invoiceNumber": invoice_number,
                        "invoiceDate": value_date
                    }
                ],
                "senderToReceiverInfo": f"{txnPaymode} PROCUREMENT"
            }
        }

        transfer_response = client.initiate_fund_transfer(txnPaymode, overrides)

        encrypted_data = transfer_response.get("TransferPaymentResponse", {}).get("TransferPaymentResponseBodyEncrypted")

        if not encrypted_data:
            return {"success": False,
                    "data":{ 
                        "data":transfer_response,
                        "message": "Missing encrypted transfer data from Axis response."
                        }
                    }
        
        decrypted = aes_decrypt_base64(encrypted_data)
        transfer_response["decrypted"] = decrypted
        
        if decrypted.get('status')=="F":
            return {
                "success": False,
                "data":{
                    "message": "Transfer initiation failed.",
                    "data": transfer_response
                }
            }

        return {
            "success": True,
            "data":{
                "message": "Transfer initiated successfully.",
                "data": transfer_response
            }
        }

    except Exception as e:
        return {
            "success": False,
            "data":{
                "message": f"Exception during transfer: {str(e)}",
            }
        }

import qrcode, pyotp
from io import BytesIO
import base64


def verify_google_auth_code(user, code):
    if not user.is_2fa_enabled or not user.google_auth_secret:
        return False, "2FA not enabled."

    totp = pyotp.TOTP(user.google_auth_secret)
    if totp.verify(code):
        return True, "Code verified."
    else:
        return False, "Invalid code."


class EnableGoogleAuthAPIView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 

    def post(self, request):
        user = request.user

        # Generate secret if not exists
        if not user.google_auth_secret:
            user.google_auth_secret = pyotp.random_base32()
            user.is_2fa_enabled = True
            user.save()

        # Create provisioning URI
        totp = pyotp.TOTP(user.google_auth_secret)
        uri = totp.provisioning_uri(name=str(user.mobile_number), issuer_name="aryashakti")

        # Generate QR code
        qr = qrcode.make(uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return res.req_response(
            constants.SUCCESS,
            True,
            '',
            status.HTTP_200_OK,
            {
                "secret": user.google_auth_secret,
                "qr_code_base64": qr_base64,
                "provisioning_uri": uri
            }
        )

          
from threading import Thread
import time

class PaymentProcure(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_procurement_details(self,procure_ids,payment_id):
        procurements = Procurement.objects.filter(id__in=procure_ids)
        
        procurement_details_list = []
        count=0
        for procurement in procurements:
            count=count+1
            user_to = procurement.user_to
            user_bank_account = get_object_or_404(UserBankAccount, user=user_to)
            
            details = {
                "amount": procurement.amount,
                "purpose": "Buying Property",  # Hardcoded purpose
                "beneficiaryAccNumber": user_bank_account.account_num,
                "beneficiaryIFSC": user_bank_account.ifsc,
                "beneficiaryName": user_bank_account.name,  # Assuming full_name is in the User model
                "beneficiaryBankName": user_bank_account.bank_name,
                "transferType": "NEFT",  # Hardcoded transfer type
                "customerRefId": "ARYA_PROC-0"+str(payment_id)+"-"+str(user_to.id)+"-"+str(count) # Placeholder, handle this as needed
            }
            
            procurement_details_list.append(details)
        return procurement_details_list

    def post(self,request,procure_id=False):
        data= request.data
        
        image=request.FILES.get('image_url')
        payment=None
        mobile_number = request.user.mobile_number if '+91' in str(request.user.mobile_number) else '+91'+str(request.user.mobile_number)
        code = request.data.get("otp_code")
        is_valid, msg = verify_google_auth_code(request.user, code)
        if not is_valid:
            return res.req_response(msg, False, "OTP-01", status.HTTP_400_BAD_REQUEST)
        if 'latitude' not in data.keys() and 'longitude'  not in data.keys():
                return res.req_response("Location is missing.", False, "PRV-PPPOST-ORG", status.HTTP_400_BAD_REQUEST)

        if 'payment_type' in data.keys():
            payment_mode=data.get('payment_mode')
            latitude=data.get('latitude')
            longitude=data.get('longitude')
            device_details=data.get('device_details')
            if not payment_mode:
                payment_mode="NE"
            try:
                org = AxisBankOrganization.objects.get(user=request.user)
            except AxisBankOrganization.DoesNotExist:
                return res.req_response("Sender bank not configured.", False, "PRV-PPPOST-ORG", status.HTTP_400_BAD_REQUEST)


            if data['payment_type']=="online":   
                try:
                    procure=Procurement.objects.filter(id=procure_id).get()
                except Procurement.DoesNotExist as e:
                    return res.req_response(str(e),False,"PRV-PPPOST-02",status.HTTP_400_BAD_REQUEST,payment)
                
                
                with transaction.atomic():
                    payment = Payment.objects.create(
                        amount = procure.amount,
                        payment_type = 'online',
                        status = 'pending',
                        org=request.user.organization,
                        device_details=device_details
                    )

                    procure_updated =  Procurement.objects.filter(id=procure_id).update(status=1,payment=payment)
                    if not procure_updated:
                        transaction.set_rollback(True)
                        return res.req_response(constants.ERROR, False, "PRV-PPPOST-03", status.HTTP_400_BAD_REQUEST, None, 'Please send correct kutumbs.')
            
                    req_data={'procurement_ids':[procure_id]}
                    req_data['description'] = 'Payment for Procurement.'
                    req_data['amount'] = procure.amount
                    req_data['notes'] = {
                        'procurement_ids': req_data['procurement_ids']
                    }

                    unique_ref = f"AR{payment.id}"
                    invoice_number = f"IN{procure_id}"
                    user_bank = get_object_or_404(UserBankAccount, user=procure.user_to)

                    # transfer_response= json.loads('''{
                    #                               "success":"True",
                    #                               "message":"failed",
                    #                               "data":{
                    #                               "message":"transfer success",
                    #                               "data":{
                    #                                 "raw": {
                    #                                     "TransferPaymentResponse": {
                    #                                         "SubHeader": {
                    #                                             "requestUUID": "'''+unique_ref+'''",
                    #                                             "serviceRequestId": "OpenAPI",
                    #                                             "serviceRequestVersion": "1.0",
                    #                                             "channelId": "ARYATECHP"
                    #                                         },
                    #                                         "TransferPaymentResponseBodyEncrypted": "/xIGDo6cqbpBNEldmCTmik/XHymzkuTkk5GnST3lspU394ndcuU8JZYKsddnSkBqBAf6eagMu4QwDAq8UfT3xqw4bJKPeNQcIqP/9YMdWng39CKE9BVV/2/q9G5Zcz4lRjJgTeuQmuJo7R3poM2mKWqkwNSm1FsiqicTezl+qFJWCDNlmYZr0zOq8Xwh19DD+f2p+CNTa5VJVnxOwiAV8gTqOdCa9aIyyF2kiCJMBw0="
                    #                                     }
                    #                                 },
                    #                                 "decrypted": {
                    #                                     "data": "",
                    #                                     "message": "txnPaymode should be RT for RTGS,NE for NEFT,FT for Fund Transfer,CC for Corporate Cheques,DD for Demand Draft,PA for IMPS",
                    #                                     "status": "F"
                    #                                 }
                    #                             }
                    #                             }
                    #                             }
                    #                             ''')
                    transfer_response = send_fund_if_sufficient_balance(
                        org=org,
                        beneficiary_name=user_bank.name,
                        beneficiary_account=user_bank.account_num,
                        beneficiary_ifsc=user_bank.ifsc,
                        beneficiary_bank=user_bank.bank_name,
                        amount=str(procure.amount),
                        value_date=datetime.today().strftime('%Y-%m-%d'),
                        unique_ref=unique_ref,
                        invoice_number=invoice_number,
                        txnPaymode=payment_mode
                    )

                    if not transfer_response["success"]:
                        transaction.set_rollback(True)
                        return res.req_response(transfer_response["data"], False, "PRV-PPPOST-TRANSFER", status.HTTP_400_BAD_REQUEST)

                    
                  
                    payment.payment_link_id = unique_ref
                    payment.response=transfer_response['data']
                    payment.latitude=latitude
                    payment.longitude=longitude
                    payment.save()                
                return res.req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, transfer_response['data'])
            
            elif data['payment_type']=="bulk" and not procure_id and data['procure_ids']:
                procure_ids=data['procure_ids']
                # Assuming procure_ids is a list of procurement IDs
                procurement_sum = Procurement.objects.filter(id__in=procure_ids).aggregate(total_amount=Sum('amount'))['total_amount']

                procurements = Procurement.objects.select_related('user_to').filter(id__in=procure_ids)


                try:
                    # ✅ Check sender balance before creating payment
                    org = AxisBankOrganization.objects.get(user=request.user)
                    client = AxisFundTransferClient()
                    client.set_dynamic_context(org.corp_code, org.corp_account_number)

                    balance_response = client.check_account_balance()
                    encrypted_data = balance_response.get("GetAccountBalanceResponse", {}).get("GetAccountBalanceResponseBodyEncrypted")

                    if not encrypted_data:
                        return res.req_response("Missing encrypted balance data from Axis response.", False, "BAL-01", status.HTTP_400_BAD_REQUEST)

                    decrypted = aes_decrypt_base64(encrypted_data)
                    balance_str = decrypted.get("data", {}).get("Balance")

                    if not balance_str:
                        return res.req_response("Missing 'Balance' in Axis balance response.", False, "BAL-02", status.HTTP_400_BAD_REQUEST)

                    current_balance = Decimal(balance_str)
                    if current_balance < Decimal(procurement_sum):
                        return res.req_response(
                            f"Insufficient balance: ₹{current_balance}. Required: ₹{procurement_sum}.",
                            False, "BAL-03", status.HTTP_400_BAD_REQUEST
                        )

                except AxisBankOrganization.DoesNotExist:
                    return res.req_response("AxisBankOrganization not found.", False, "BAL-04", status.HTTP_404_NOT_FOUND)

                except Exception as e:
                    return res.req_response(f"Balance check error: {str(e)}", False, "BAL-05", status.HTTP_500_INTERNAL_SERVER_ERROR)


                # If procurement_sum is None, you may want to handle the case where there are no matching objects
                if procurement_sum is None:
                    procurement_sum = 0

                
                with transaction.atomic():
                    # payment = Payment.objects.create(
                    #     amount = procurement_sum,
                    #     payment_type = 'bulk',
                    #     status = 'pending'
                    # )

                    # procure_updated = Procurement.objects.filter(id__in=procure_ids).update(status=0,payment=payment)
                    
                    # if procure_updated != len(data['procure_ids']):
                    #     transaction.set_rollback(True)
                    #     return res.req_response(constants.ERROR, False, "PRV-PPPOST-06", status.HTTP_400_BAD_REQUEST, None, 'Please send procurements kutumbs.')
                    
                    # req_data={'procurement_ids':procure_ids}
                    # req_data['description'] = 'Payment for Procurement.'
                    # req_data['amount'] =procurement_sum
                    # req_data['notes'] = {
                    #     'procurement_ids': req_data['procurement_ids']
                    # }
                    
                    
                    
                    # # link_data = create_payment_link_common(payment.id, req_data, request, mobile_number)

                    # # if not link_data['status'] and link_data['status'] != 'created':
                    # #     transaction.set_rollback(True)
                    # #     return res.req_response(constants.ERROR, False, "PRV-PPPOST-05", status.HTTP_400_BAD_REQUEST)
                    
                    # payment.payment_link_id = link_data['id']
                    # payment.save()

                    updated = 0
                    for procure in procurements:
                        payment = Payment.objects.create(
                            amount=procure.amount,
                            payment_type='bulk',
                            status='pending',
                            latitude=latitude,
                            longitude=longitude,
                            org=request.user.organization,
                            device_details=device_details

                        )
                        procure.payment = payment
                        procure.type = "bulk"
                        procure.status = 0
                        procure.save()
                        updated += 1

                    if updated != len(procurements):
                        transaction.set_rollback(True)
                        return res.req_response(constants.ERROR, False, "PRV-PPPOST-06", status.HTTP_400_BAD_REQUEST, None, 'Please send procurements kutumbs.')

                # ✅ Background worker to handle transfers
                

                def delayed_bulk_transfer_worker(procs, user_id,payment_mode):
                    from datetime import datetime
                    from django.utils.timezone import now

                    org = AxisBankOrganization.objects.get(user_id=user_id)

                    for procure in procs:
                        try:
                            unique_ref = f"AR{procure.payment.id}"
                            invoice_number = f"IN{procure.id}"
                            user_bank = get_object_or_404(UserBankAccount, user=procure.user_to)
                            if procure.amount>200000:
                                payment_mode="RT"
                            result = send_fund_if_sufficient_balance(
                                org=org,
                                beneficiary_name=user_bank.name,
                                beneficiary_account=user_bank.account_num,
                                beneficiary_ifsc=user_bank.ifsc,
                                beneficiary_bank=user_bank.bank_name,
                                amount=str(procure.amount),
                                value_date=datetime.today().strftime('%Y-%m-%d'),
                                unique_ref=unique_ref,
                                invoice_number=invoice_number,
                                txnPaymode=payment_mode
                            )

                            # result= json.loads('''{
                            #                       "success":"True",
                            #                       "message":"failed",
                            #                       "data":{
                            #                       "message":"transfer success",
                            #                       "data":{
                            #                         "raw": {
                            #                             "TransferPaymentResponse": {
                            #                                 "SubHeader": {
                            #                                     "requestUUID": "'''+unique_ref+'''",
                            #                                     "serviceRequestId": "OpenAPI",
                            #                                     "serviceRequestVersion": "1.0",
                            #                                     "channelId": "ARYATECHP"
                            #                                 },
                            #                                 "TransferPaymentResponseBodyEncrypted": "/xIGDo6cqbpBNEldmCTmik/XHymzkuTkk5GnST3lspU394ndcuU8JZYKsddnSkBqBAf6eagMu4QwDAq8UfT3xqw4bJKPeNQcIqP/9YMdWng39CKE9BVV/2/q9G5Zcz4lRjJgTeuQmuJo7R3poM2mKWqkwNSm1FsiqicTezl+qFJWCDNlmYZr0zOq8Xwh19DD+f2p+CNTa5VJVnxOwiAV8gTqOdCa9aIyyF2kiCJMBw0="
                            #                             }
                            #                         },
                            #                         "decrypted": {
                            #                             "data": "",
                            #                             "message": "txnPaymode should be RT for RTGS,NE for NEFT,FT for Fund Transfer,CC for Corporate Cheques,DD for Demand Draft,PA for IMPS",
                            #                             "status": "F"
                            #                         }
                            #                     }
                            #                     }
                            #                     }
                            #                     ''')
                            payment = procure.payment
                            # payment.status = "success" if result.get("success") else "failed"
                            payment.response = result['data']
                            payment.payment_link_id = unique_ref
                            payment.save()

                            procure.status = 1 if result.get("success") else 2
                            procure.save()

                            time.sleep(4)

                        except Exception as e:
                            if procure.payment:
                                procure.payment.status = "failed"
                                procure.payment.response = {"success": False, "message": str(e)}
                                procure.payment.save()
                            procure.status = 2
                            procure.save()

                Thread(target=delayed_bulk_transfer_worker, args=(list(procurements), request.user.id,payment_mode)).start()

                return res.req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, f"Bulk payment initiated for {len(procurements)} procurements.")
            
            elif data['payment_type'] == "cash":
                try:
                    procure = Procurement.objects.get(id=procure_id)
                except Procurement.DoesNotExist as e:
                    return res.req_response(str(e), False, "PRV-PPPOST-02", status.HTTP_400_BAD_REQUEST, payment)
                
                payment_data = cash_upload(
                    procure.amount, 
                    image, 
                    user_id=request.user.id
                )
                
                if not payment_data.get('success'):
                    return res.req_response(payment_data.get('message', "Cash upload failed"), False, "PRV-PPPOST-CASH", status.HTTP_400_BAD_REQUEST)
                Procurement.objects.filter(id=procure_id).update(status=1, payment_id=payment_data['data'].id)
                procure.refresh_from_db()
                procure_data = ProcurementSerializer(procure).data
                
                # Include signed URL for immediate frontend display 
                if 'signed_url' in payment_data:
                    procure_data['signed_url'] = payment_data['signed_url']
                    
                return res.req_response(payment_data['message'], True, "", status.HTTP_200_OK, procure_data)
            

                        
                    
        return res.req_response("Something is wrong",False,"PRV-PPPOST-04",status.HTTP_400_BAD_REQUEST)






class AxisBankBalanceCheckView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 


    def get(self, request):
        try:
            try:
                org = AxisBankOrganization.objects.get(user=request.user)
            except AxisBankOrganization.DoesNotExist:
                return res.req_response(
                    "Axis bank account not configured for this user.",
                    False,
                    "BAL-CHECK-01",
                    status.HTTP_400_BAD_REQUEST
                )

            client = AxisFundTransferClient()
            client.set_dynamic_context(org.corp_code, org.corp_account_number)

            response = client.check_account_balance()
            encrypted = response.get("GetAccountBalanceResponse", {}).get("GetAccountBalanceResponseBodyEncrypted")

            if not encrypted:
                print(response)
                return res.req_response(
                    "No encrypted balance found in response.",
                    False,
                    "BAL-CHECK-02",
                    status.HTTP_502_BAD_GATEWAY
                )

            decrypted = aes_decrypt_base64(encrypted)
            balance_info = decrypted.get("data", {})
            balance = balance_info.get("Balance")

            if not balance:
                return res.req_response(
                    "Balance not present in decrypted response.",
                    False,
                    "BAL-CHECK-03",
                    status.HTTP_502_BAD_GATEWAY
                )

            return res.req_response(
                "Balance fetched successfully.",
                True,
                "BAL-CHECK-00",
                status.HTTP_200_OK,
                {
                    "balance": balance,
                    # "corp_code": balance_info.get("corpCode"),
                    # "corp_account": balance_info.get("corpAccNum")
                }
            )

        except Exception as e:
            return res.req_response(
                f"Error occurred while checking balance: {str(e)}",
                False,
                "BAL-CHECK-99",
                status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CheckBulkPaymentStatusAPIView(APIView):
    """
    API to check pending payments' transfer status.
    This will be run by cron.
    """

    def post(self, request):
        # Fetch pending payments starting with ARYAONL
        pending_payments = Payment.objects.filter(
            status="pending",
            payment_link_id__startswith="AR"
        )

        if not pending_payments.exists():
            return res.req_response("No pending payments found.", True, "", status.HTTP_200_OK)

        # Worker function to check status and update records
        def status_worker(payments):
            client = AxisFundTransferClient()
            for payment in payments:
                try:
                    unique_ref = payment.payment_link_id  # Already contains ARYAONL...
                    org = AxisBankOrganization.objects.get(organization=payment.org)

                    client.set_dynamic_context(org.corp_code, org.corp_account_number)
                    response = client.check_fund_transfer_status(unique_ref)

                    encrypted = response.get("GetStatusResponse", {}).get("GetStatusResponseBodyEncrypted")

                    if not encrypted:
                        payment.response_json_status ={"error":"No encrypted status found in response.","data":response}
                        return res.req_response(
                            "No encrypted status found in response.",
                            False,
                            "BAL-CHECK-02",
                            status.HTTP_502_BAD_GATEWAY
                        )

                    decrypted = aes_decrypt_base64(encrypted)

                    response['decrypted']=decrypted
                    payment.response_json_status = response


                    # Parse status
                    transfer_status = decrypted.get("status")
                   

                    if transfer_status == "S":
                        payment.status = "success"
                    elif transfer_status == "F":
                        payment.status = "failed"

                    payment.save()
                    time.sleep(4)
                except AxisBankOrganization.DoesNotExist:
                    payment.response_json_status = {"error": "AxisBankOrganization not found"}
                    payment.status = "failed"
                    payment.save()
                except Exception as e:
                    payment.response_json_status = {"error": str(e)}
                    payment.status = "failed"
                    payment.save()

        # Start thread so API returns quickly
        Thread(target=status_worker, args=(list(pending_payments),)).start()

        return res.req_response(
            constants.SUCCESS,
            True,
            '',
            status.HTTP_200_OK,
            f"Status check initiated for {pending_payments.count()} payments."
        )





class DownloadProcurementUploadCSV(APIView):
    def get(self,request):
        # Create CSV data in memory
        csv_data = ["crop_name","full_name","gender","mobile_number","variety","qty","rate","amount","description"]

        # Create the HttpResponse object with CSV content type
        response= helper.downloadCsvSampleCSV(csv_data)

        return response
    



class UploadProcurementCSV(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 

     # number of items per page by default
    page_size = 25
    # max number of items per page
    max_page_size = 100
    model=Procurement    

    def get_queryset(self,procure_register_id):
        queryset=Procurement.objects.filter(payment=None,payment__status=None,procure_register_id=procure_register_id,user_from=self.request.user,type="bulk" ).all()
        return queryset
    

    def get(self,request,procure_register_id):
        queryset = self.get_queryset(procure_register_id)   
          
        page =  self.paginate_queryset(queryset,request)

        procure=None
        if page:          
            procure=ProcurementSerializer(page,many=True).data
            procure=self.get_paginated_response(procure).data
        
        return res.req_response("Data found",True,"",status.HTTP_200_OK,procure)

    def post(self, request,procure_register_id):
        try:
            # Check if a CSV file is uploaded
            if 'csv_upload' not in request.FILES:
                return res.req_response("Please upload a CSV file.",False,"PV-UPC-POST-01",status.HTTP_400_BAD_REQUEST)
            
            try:
                crop = ProcurementRegister.objects.get(id=procure_register_id)
            except ProcurementRegister.DoesNotExist:
                return res.req_response(f"Procurement register '{procure_register_id}' does not exist.",False,"PV-UPC-POST-01",status.HTTP_400_BAD_REQUEST)

            
            # Initialize a list to store Procurement data
            procurement_data = []

            # Get the uploaded CSV file
            csv_file = request.FILES["csv_upload"]
            organization = request.user.organization
            user_data= request.user
            # Open the CSV file and read it as a list of dictionaries
            with TextIOWrapper(csv_file, encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Check if the crop exists
                    try:
                        crop = crop_master.objects.get(crop_name=row['crop_name'])
                    except crop_master.DoesNotExist:
                        return res.req_response(f"Crop '{row['crop_name']}' does not exist.",False,"PV-UPC-POST-01",status.HTTP_400_BAD_REQUEST)
                    farm_data=None
                    # Check if the user exists or create a new one
                    try:
                        user_to = user.objects.get(mobile_number=row['mobile_number'])
                        # farm_data=farm.objects.filter(user=user_to).all()
                        # if farm_data:
                        #     farm_data=farm_data[0]
                    except user.DoesNotExist:
                        # Create a new user
                        
                        user_to = user.objects.create(
                            full_name=row['full_name'],
                            gender=row['gender'],
                            mobile_number=row['mobile_number'],
                            organization=organization,
                            latitude=0,
                            longitude=0
                        )

                        farm_data=farm.objects.create(
                            updated_by_id=user_data,
                            added_by=user_data,
                            user=user_to,
                            crop_id=crop,
                            name=row['full_name'],
                            farmer_contact=row['mobile_number'],
                        )
                        

                    

                    # Create a dictionary for procurement data
                    procurement_dict = {
                        'procure_register_id':procure_register_id,
                        'crop': crop,
                        'user_from': user_data,
                        'user_to': user_to,
                        # Assign other fields from the CSV row
                        'variety': row['variety'],
                        'qty': row['qty'],
                        'rate': row['rate'],
                        'amount': row['amount'],
                        'description': row['description'],
                        "type":"bulk",
                        # "farm":farm_data,
                        "status":0
                    }
                    procurement_data.append(procurement_dict)

            # Bulk create the Procurement objects
            procure= Procurement.objects.bulk_create([Procurement(**data) for data in procurement_data])
            procure=ProcurementSerializer(procure,many=True).data
            
            # Return the response
            return res.req_response("Data uploaded",True,"",status.HTTP_200_OK,procure)
            
        except Exception as e:
            return res.req_response(str(e),False,"PV-UPC-POST-02",status.HTTP_400_BAD_REQUEST)
