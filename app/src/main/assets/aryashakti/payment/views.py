from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.urls import reverse
from datetime import datetime, timedelta
import json, time, base64, requests, decimal
import razorpay
from django.db import transaction

from app_farm.authentication import CustomTokenAuthentication
from app_farm.utils import helper, constants, response as res
from app_farm.models import user as UserModel
from django.conf import settings
from app_farm.utils.response import req_response
from . import models, validator
from subscription_service.models import Subscription,UserService,UserSubscription,CouponUser,Coupon,Service
from core.views import BaseView,BaseViewWithoutAuthentication
from insurance.models import Kutumb
from procurement.models import Procurement


client = razorpay.Client(auth=(settings.PAYMENT_API_KEY, settings.PAYMENT_SECRET_KEY))
razorpayx_token = {
    'Content-Type': 'application/json',
    'Authorization': 'Basic '+base64.b64encode((settings.RAZORPAYX_API_KEY+':'+settings.RAZORPAYX_SECRET_KEY).encode('ascii')).decode('ascii')
}

# Function to handle the after part of assuming that payment is done.
def HandlePaymentSuccess(order):
    # Create a User Coupon entry if coupon used.
    if order.coupon:
        CouponUser.objects.create(
            user = order.paid_by,
            coupon = order.coupon
        )
    # Fetch all services in order
    service_array = []
    for service in order.services:
        service_array.append(service['s_id'])
    services = Service.objects.filter(id__in=service_array)
    service_dict = {}
    for service in services:
        service_dict[str(service.id)] = service

    user_orders = models.UserOrder.objects.filter(order=order.id)
    today = datetime.now()
    user_services = []

    # Create UserService and UserSubscription for every user paid for.
    for u_o in user_orders:
        user_subscription = UserSubscription.objects.create(
            user = u_o.user,
            subscription = order.package,
            validity = today+timedelta(days=order.package_validity),
            sponsored_by = order.paid_by
        )

        for service in order.services:
            user_services.append(UserService(
                user = u_o.user,
                service = service_dict[str(service['s_id'])],
                validity = service['validity'],
                remaining = service['validity'],
                user_subscription = user_subscription
            ))
    UserService.objects.bulk_create(user_services)

def create_payment_link(order_id, body_data, request, mobile_number):
    payment_link = client.payment_link.create({
        "amount": int(decimal.Decimal(str(body_data['final_price'])) * decimal.Decimal('100')),
        "customer": {
            "name": request.user.full_name,
            "contact": mobile_number,
        },
        "description": body_data['description'],
        "reference_id": 'O-'+str(int(time.time()*1000))+'OO'+str(order_id),
        "notify": {
            "sms": True,
            "email": True
        },
        "reminder_enable": True,
        "callback_url": helper.replaceHttp(request.build_absolute_uri(reverse("paymentredirect"))),
        "callback_method": "get"
    })
    return payment_link

def create_payment_link_common(payment_id, body_data, request, mobile_number):
    payment_link = client.payment_link.create({
        "amount": int(decimal.Decimal(str(body_data['amount'])) * decimal.Decimal('100')),
        "customer": {
            "name": request.user.full_name,
            "contact": mobile_number,
        },
        "description": body_data['description'],
        "reference_id": 'O-'+str(int(time.time()*1000))+'OOO'+str(payment_id),
        "notify": {
            "sms": True,
            "email": True
        },
        "reminder_enable": True,
        "callback_url": helper.replaceHttp(request.build_absolute_uri(reverse("paymentredirectcommon"))),
        "callback_method": "get",
        "notes": {
            **body_data['notes']
        }
    })
    return payment_link

# Function to get some random farmers of a an organization.
def GetRandomFarmers(num, org_id):
    # users = models.user.objects.filter(organization=org_id,user_role=settings.IDS_FARMER_USER_ROLE).annotate(
    #             subs=Count('user_subscription',filter=Q(user_subscription__validity__gt=datetime.now()))
    #         ).order_by('subs')[:num]
    # users = models.user.objects.filter(Q(user_subscription=None)|Q(user_subscription__subscription__package_type='trial'),organization=org_id,user_role=settings.IDS_FARMER_USER_ROLE)[:num]
    users = models.user.objects.filter(user_subscription=None,organization=org_id,user_role=settings.IDS_FARMER_USER_ROLE)[:num]
    return users
        
class CreateOrder(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            if request.data == None:
                return req_response(constants.EMPTY_REQ_BODY, False, 'PVCO-COPOS-1', status.HTTP_400_BAD_REQUEST)

            body_data = request.data
            if type(body_data) == str:
                body_data = json.loads(body_data)

            if body_data.get('org_id'):
                validation = validator.RandomFarmerCreateOrderValidator(data=body_data)
            else:
                validation = validator.NoRandomFarmerCreateOrderValidator(data=body_data)

            if not validation.is_valid():
                return req_response(constants.INVALID_BODY, False, 'PVCO-COPOS-2', status.HTTP_400_BAD_REQUEST, validation.errors)
                
            if body_data.get('org_id'):
                farmers = GetRandomFarmers(body_data['num_of_farmers'], body_data['org_id'])
                if body_data['num_of_farmers'] != len(farmers):
                    return req_response(constants.NOT_SUFFICIENT_FARMERS.format(len(farmers)), False, 'PVCO-COPOS-3', status.HTTP_400_BAD_REQUEST)
            else:
                farmers = models.user.objects.filter(id__in=body_data['farmers'])

                # Check if any package is already used for that farmer then the trial package will not be available for him.
                if body_data['package_type'] == 'trial' and UserSubscription.objects.filter(user__in=body_data['farmers']).exists():
                    return req_response(constants.TRIAL_NOT_AVAILABLE, False, 'PVCO-COPOS-4', status.HTTP_406_NOT_ACCEPTABLE)

            package = Subscription.objects.get(id=body_data['package_id'])
            coupon = Coupon.objects.get(id=body_data['coupon_id']) if body_data.get('coupon_id') else None

            user_orders = []
            mobile_number = request.user.mobile_number if '+91' in str(request.user.mobile_number) else '+91'+str(request.user.mobile_number)

            order_obj = {
                "paid_by": request.user,
                "paid_by_name": request.user.full_name,
                "paid_by_phone": mobile_number,
                "paid_by_role": request.user.user_role,
                "package": package,
                "package_validity": body_data['package_validity'],
                "package_type": body_data['package_type'],
                "coupon": coupon,
                "coupon_discount": body_data.get('coupon_discount'),
                "coupon_value": body_data.get('coupon_value'),
                "price": body_data['price'],
                "total_discount": body_data['total_discount'],
                "taxes": body_data['taxes'],
                "final_price": body_data['final_price'],
                "status": 'Pending',
                "services": body_data['services']
            }

            if body_data['package_type'] == 'trial':
                order_obj['payment_link_status'] = 'trial_pack'
                order_obj['status'] = 'Paid'
            elif body_data.get('coupon_value') and body_data.get('coupon_value') == 100:
                order_obj['payment_link_status'] = 'full_coupon_discount'
                order_obj['status'] = 'Paid'
            
            # Create an Order
            order = models.Order.objects.create(
                **order_obj
            )

            # Create the entries in order detail table (UserOrder)
            for farmer in farmers:
                user_orders.append(models.UserOrder(order=order, user=farmer))

            models.UserOrder.objects.bulk_create(user_orders)

            if order_obj.get('status') and order_obj['status'] == 'Paid':
                # Skip payment
                HandlePaymentSuccess(order)
                msg = constants.SPONSOR_PAYMENT_SUCCESS.format(body_data['final_price'],body_data['num_of_farmers']) if body_data.get('org_id') else constants.PAYMENT_SUCCESS
                return req_response(msg, True, '', status.HTTP_202_ACCEPTED)

            # Create Payment Link
            link_data = create_payment_link(order.id, body_data, request, mobile_number)

            if not link_data['status'] and link_data['status'] != 'created':
                return req_response(constants.ERROR, False, 'PVCO-COPOS-5', status.HTTP_400_BAD_REQUEST)

            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, link_data['short_url'])
        except Exception as e:
            return req_response(constants.ERROR, False, 'PVCO-COPOS-6', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)

class PaymentRedirect(APIView):
    def get(self,request):
        try:
            data = {
                'payment_link_id': request.GET.get("razorpay_payment_link_id"),
                'payment_link_reference_id': request.GET.get("razorpay_payment_link_reference_id"),
                'payment_link_status': request.GET.get("razorpay_payment_link_status"),
                'razorpay_payment_id': request.GET.get("razorpay_payment_id"),
                'razorpay_signature': request.GET.get("razorpay_signature")
            }

            result = res.ErrRes()
            result['status_code'] = status.HTTP_404_NOT_FOUND
            # client.utility.verify_webhook_signature(request.body.decode(), request.headers.get('X-Razorpay-Signature'), settings.PAYMENT_WEBHOOK_SECRET)
            if not client.utility.verify_payment_link_signature(data):
                result['message'] = constants.ERROR
                result['error_code'] = "PV-PRGET-01"
                return render(
                    request, 'payment_verify.html', {'data': json.dumps(result)}
                )
            
            # Update the Order status
            order = models.Order.objects.get(id=data['payment_link_reference_id'].split('OO')[1])
            order.payment_id = data['razorpay_payment_id']
            order.payment_link_status = data['payment_link_status']
            order.status = 'Paid'
            order.save()
            num_of_farmers = models.UserOrder.objects.filter(order=order.id).count()

            HandlePaymentSuccess(order)
            
            result = res.SuccRes()
            result['status_code'] = status.HTTP_202_ACCEPTED
            result['message'] = constants.SPONSOR_PAYMENT_SUCCESS.format(order.final_price,num_of_farmers) if order.paid_by_role.role_name == constants.SLUGS['USER_ROLES']['SPONSOR'] else constants.PAYMENT_SUCCESS
            return render(
                request, 'payment_verify.html', {'data': json.dumps(result)}
            )
        except Exception as e:
            result = res.ErrRes()
            result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            result['message'] = e
            result['error_code'] = "PV-PRGET-03"
            return render(
                request, 'payment_verify.html', {'data': json.dumps(result)}
            )
        
class PaymentRedirectCommon(APIView):
    """
    Function called from Razorpay redirection for Insurance payment.
    """
    def get(self,request):
        try:
            data = {
                'payment_link_id': request.GET.get("razorpay_payment_link_id"),
                'payment_link_reference_id': request.GET.get("razorpay_payment_link_reference_id"),
                'payment_link_status': request.GET.get("razorpay_payment_link_status"),
                'razorpay_payment_id': request.GET.get("razorpay_payment_id"),
                'razorpay_signature': request.GET.get("razorpay_signature")
            }

            result = res.ErrRes()
            result['status_code'] = status.HTTP_404_NOT_FOUND
            # client.utility.verify_webhook_signature(request.body.decode(), request.headers.get('X-Razorpay-Signature'), settings.PAYMENT_WEBHOOK_SECRET)
            if not client.utility.verify_payment_link_signature(data):
                result['message'] = constants.ERROR
                result['error_code'] = "PV-PRFIGET-01"
                return render(
                    request, 'payment_verify.html', {'data': json.dumps(result)}
                )
            
            result = res.SuccRes()
            result['status_code'] = status.HTTP_202_ACCEPTED
            result['message'] = constants.COMMON_PAYMENT_SUCCESS
            return render(
                request, 'payment_verify.html', {'data': json.dumps(result)}
            )
        except Exception as e:
            result = res.ErrRes()
            result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            result['message'] = e
            result['error_code'] = "PV-PRFIGET-03"
            return render(
                request, 'payment_verify.html', {'data': json.dumps(result)}
            )
        
# Insurance Member Bank Account validation logic
def insurance_bank_validation_logic(member, verified_by, body_data,mobile=0):
    with transaction.atomic():
        bank_acc, created = models.BankAccount.objects.get_or_create(
            account_num = body_data['acc_num'],
            defaults= {
                "name": body_data['name'],

                "contact": member.phone if mobile==0 else member.mobile,
                "email": member.email if mobile==0 else None,
                "verified_by": verified_by,
                "account_num": body_data['acc_num'],
                "ifsc": body_data['ifsc']
            }
        )
        if created:
            member.bank_acc = bank_acc
            member.save()
    
    if bank_acc.fund_account:
        pass
    elif bank_acc.contact_id:
        fund_account = create_fund_account(bank_acc)
        bank_acc.fund_account = fund_account['id']
        bank_acc.bank_name = fund_account['bank_account']['bank_name']
        bank_acc.save()
    else:
        contact = create_contact(bank_acc)
        bank_acc.contact_id = contact['id']
        bank_acc.save()

        fund_account = create_fund_account(bank_acc)
        bank_acc.fund_account = fund_account['id']
        bank_acc.bank_name = fund_account['bank_account']['bank_name']
        bank_acc.save()

    validation = validate_bank_account(bank_acc, body_data['kutumb_id'] if mobile==0 else body_data['insurance_id'],None if mobile==0 else 1)
    if validation.get('status') and validation['status'] == 'created':
        bank_acc.fav_id = validation['id']
        bank_acc.status = 2
        bank_acc.save()

    return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)

# User Bank Account validation logic
def bank_validation_logic(user, verified_by, body_data):
    # user is the User which is to be verified
    # verified_by is the User which is verifying
    user_bank_acc = models.UserBankAccount.objects.get_or_create(
        user = user.id,
        defaults= {
            "name": body_data['name'],
            "contact": user.mobile_number,
            "email": user.email,
            "user": user,
            "account_num": body_data['acc_num'],
            "ifsc": body_data['ifsc']
        }
    )[0]
    helper.addVerification(user,settings.BANK_ACCOUNT_DOCUMENT_ID,user_bank_acc.id,"payment_bankaccountvalidation_request",3,verified_by.id)
    if user_bank_acc.fund_account:
        pass
    elif user_bank_acc.contact_id:
        fund_account = create_fund_account(user_bank_acc)
        user_bank_acc.fund_account = fund_account['id']
        user_bank_acc.bank_name = fund_account['bank_account']['bank_name']
        user_bank_acc.save()
    else:
        contact = create_contact(user_bank_acc)
        user_bank_acc.contact_id = contact['id']
        user_bank_acc.save()

        fund_account = create_fund_account(user_bank_acc)
        user_bank_acc.fund_account = fund_account['id']
        user_bank_acc.bank_name = fund_account['bank_account']['bank_name']
        user_bank_acc.save()

    validation = validate_bank_account(user_bank_acc)
    if validation.get('status') and validation['status'] == 'created':
        user_bank_acc.fav_id = validation['id']
        user_bank_acc.save()
        helper.addVerification(user,settings.BANK_ACCOUNT_DOCUMENT_ID,user_bank_acc.id,"payment_bankaccountvalidation_request",2,verified_by.id)

    return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)


class UserBankValidation(BaseView):
    def user_bank_validation(self, request, err_code, body_data):
        return bank_validation_logic(request.user, request.user, body_data)
    
    def post(self, request):
        return self.common_function(request, 'PV-UBVPOS-', validator.UserBankValidation, self.user_bank_validation)
        
class UserBankValidationByAdmin(BaseView):
    def user_bank_validation_by_admin(self, request, err_code, body_data):
        user = UserModel.objects.get(id=body_data['user_id'])
        return bank_validation_logic(user, request.user, body_data)

    def post(self, request):
        return self.common_function(request, 'PV-UBVBAPOS-', validator.UserBankValidationByAdmin, self.user_bank_validation_by_admin)


        
class BankValidationRedirect(APIView):
    def post(self, request):
        try:
            if request.data == None:
                return req_response(constants.EMPTY_REQ_BODY, False, 'PV-BVRPOS-1', status.HTTP_400_BAD_REQUEST)

            body_data = request.data
            if type(body_data) == str:
                body_data = json.loads(body_data)
            entity = {}

            if body_data.get('payload'):
                entity = body_data['payload']['fund_account.validation']['entity']

            if entity['notes'].get('kutumb'):
                bank_acc = models.BankAccount.objects.get(fund_account=entity['fund_account']['id'])
            else:
                bank_acc = models.UserBankAccount.objects.get(fund_account=entity['fund_account']['id'])

            if body_data.get('payload') and entity['status'] == 'completed' and entity['results']['account_status'] == 'active':
                if helper.do_name_match(entity['results']['registered_name'].strip().lower(), bank_acc.name.strip().lower()):
                    msg = "A/C XX"+bank_acc.account_num[-4:]+" verified for " + bank_acc.name
                    verification_status = 1

                    # Update the status of the Kutumb (that it's bank has been updated)
                    if entity['notes'].get('kutumb'):
                        kutumb = Kutumb.objects.get(id=entity['notes']['kutumb'])
                        # Whther the husband or wife bank was updated
                        if kutumb.wife:
                            kutumb.status = 'wife_bank'
                        else:
                            kutumb.status = 'husband_bank'
                        kutumb.save()
                    
                    if entity['notes'].get('insurance'):
                        InsuranceEnrollment.objects.update(bank_verified=1)
                else:
                    print(body_data['payload'])
                    msg = 'Name mismatch.\n"'+ bank_acc.name.strip() + '" does not match with "' + entity['results']['registered_name'].strip() + '". Please try again.'
                    verification_status = 3
            else:
                print(body_data['payload'])
                msg = "Something went wrong during bank A/C verification. Please try again."
                verification_status = 3

            if entity['notes'].get('kutumb'):
                bank_acc.status = verification_status
                bank_acc.save()
                helper.send_firebase_notification(bank_acc.verified_by.id, msg)
            else:
                helper.addVerification(bank_acc.user,settings.BANK_ACCOUNT_DOCUMENT_ID,bank_acc.id,"payment_bankaccountvalidation_request",verification_status,None,msg)

            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return req_response(constants.ERROR, False, 'PV-BVRPOS-2', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)



from libraries.pams import PAMSClient


# User Bank Account validation logic
def bank_validation_logic_pams(user, verified_by, body_data):
    # user is the User which is to be verified
    # verified_by is the User which is verifying
    # Already verified
    if helper.is_bank_account_verified(user):
        return req_response(
            "Bank account already verified",
            True,
            "",
            status.HTTP_200_OK
        )
    #create or fetch account 
    user_bank_acc,created = models.UserBankAccount.objects.get_or_create(
        user = user,
        defaults= {
            "name": body_data['name'],
            "contact": user.mobile_number,
            "email": user.email,
            "user": user,
            "account_num": body_data['acc_num'],
            "ifsc": body_data['ifsc']
        }
    )
    #add verification in pending
    helper.addVerification(user,settings.BANK_ACCOUNT_DOCUMENT_ID,user_bank_acc.id,"payment_bankaccountvalidation_request",2,verified_by.id)

   

    #call pams and generate request
    try:
        client = PAMSClient()
        
        response = client.register_account(
            user_id=user.id,
            customer_id=100011,
            beneficiary_name=body_data['name'],
            beneficiary_account_no=body_data['acc_num'],
            ifsc_code=body_data['ifsc'],
            bank_name=body_data.get('bank_name'),
            bank_city=body_data.get('city_name')
        )
        #validate if payment made update the status
        if not response.get("success"):
                return req_response(
                    "Bank account validation failed",
                    False,
                    "",
                    status.HTTP_400_BAD_REQUEST
                )

        payload = response.get("payload", {})

        # Save PAMS account id
        user_bank_acc.pams_account_id = payload.get("pamsAccountId")

        if body_data.get("bank_name"):
            user_bank_acc.bank_name = body_data["bank_name"]

        user_bank_acc.save()

        pams_status = payload.get("status")
        is_validated = payload.get("isValidated", False)
        account_exists = payload.get("custAccAlreadyExist", False)

        # VERIFIED
        if (
            pams_status == "ACTIVE"
            and is_validated
        ):

            helper.addVerification(
                user=user,
                doc_type=settings.BANK_ACCOUNT_DOCUMENT_ID,
                doc_id=user_bank_acc.id,
                type="payment_bankaccountvalidation_request",
                status=1,
                verified_by_id=verified_by.id
            )

            return req_response(
                "Bank account verified successfully",
                True,
                "",
                status.HTTP_200_OK
            )

        # PENDING (waiting for PubSub callback)
        helper.addVerification(
            user=user,
            doc_type=settings.BANK_ACCOUNT_DOCUMENT_ID,
            doc_id=user_bank_acc.id,
            type="payment_bankaccountvalidation_request",
            status=2,
            verified_by_id=verified_by.id
        )

        return req_response(
            constants.SUCCESS,
            True,
            '',
            status.HTTP_200_OK,payload
        )
    except Exception as e:

        print(
            f"PAMS bank verification failed for user {user.id}"
        )

        return req_response(
            str(e),
            False,
            "",
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )



class UserBankValidationPams(BaseView):
    def user_bank_validation(self, request, err_code, body_data):
        return bank_validation_logic_pams (request.user, request.user, body_data)
    
    def post(self, request):
        return self.common_function(request, 'PV-UBVPOS-', validator.UserBankValidationPams, self.user_bank_validation)
        
class UserBankValidationByAdminPams(BaseView):
    def user_bank_validation_by_admin(self, request, err_code, body_data):
        user = UserModel.objects.get(id=body_data['user_id'])
        return bank_validation_logic_pams(user, request.user, body_data)

    def post(self, request):
        return self.common_function(request, 'PV-UBVBAPOS-', validator.UserBankValidationByAdminPams, self.user_bank_validation_by_admin)











def create_contact(data):
    url = settings.RAZORPAYX_BASE_URL+"contacts"

    payload = json.dumps({
        'name': data.name,
        'email': data.email,
        'contact': data.contact,
        'type': 'customer',
        'reference_id': 'BA-'+str(int(time.time()*1000))+'OO'+str(data.id)
    })
    response = json.loads(requests.request("POST", url, headers=razorpayx_token, data=payload).text)
    return response

def create_fund_account(data):
    url = settings.RAZORPAYX_BASE_URL+"fund_accounts"

    payload = json.dumps({
        "contact_id": data.contact_id,
        "account_type": "bank_account",
        "bank_account": {
            "name": data.name,
            "ifsc": data.ifsc,
            "account_number": data.account_num
        }
    })
    response = json.loads(requests.request("POST", url, headers=razorpayx_token, data=payload).text)
    return response

def validate_bank_account(data, kutumb=None,i=None):
    url = settings.RAZORPAYX_BASE_URL+"fund_accounts/validations"
    obj = {
        "account_number": settings.RAZORPAYX_ACCOUNT_NUM,
        "fund_account": {
            "id": data.fund_account
        },
        "amount": 100,
        "notes": {
            "vertical": "survey",
            "destination": "aryashakti",
        }
    }
    if kutumb:
        if i:
            obj['notes']['kutumb'] =kutumb
        else :
            obj['notes']['insurance'] = kutumb

    payload = json.dumps({
        **obj
    })
    response = json.loads(requests.request("POST", url, headers=razorpayx_token, data=payload).text)
    return response

def composite_payout(data):
    url = settings.RAZORPAYX_BASE_URL+"payouts"

    payload = json.dumps({
        "account_number": settings.RAZORPAYX_ACCOUNT_NUM,
        "fund_account_id": data['fund_acc'],
        "amount": data['amount'] * 100,
        "currency": "INR",
        "mode": "NEFT",
        "purpose": "payout",
        "queue_if_low_balance": False,
        "reference_id": 'O-'+str(int(time.time()*1000))+'OO'+str(data['procurement_id']),
        "narration": "AryaShakti Payments",
        "notes": {
            "type": "procurement"
        }
    })
    response = json.loads(requests.request("POST", url, headers=razorpayx_token, data=payload).text)
    return response


def cash_upload(amount, image, user_id=None):
    if image is not None:
        if user_id:
            timestamp = int(time.time() * 1000)
            image_url = helper.private_image_upload(image, f"cash_receipts/user_{user_id}/{timestamp}")
        else:
            image_url = helper.image_upload(image)
        
        if image_url is None:
            return {"success": False, "message": "Failed to upload receipt image"}
    else:
        return {"success": False, "message": "Image not found"}
    
    data = models.Payment.objects.create(
        amount=amount,
        payment_type="cash",
        response={"cash_receipt": image_url},
        status="success"
    )
    
    signed_url = None
    if user_id and image_url and "http" not in image_url:
        signed_urls = helper.generate_multiple_signed_urls([image_url], 1440)
        signed_url = signed_urls.get(image_url) if signed_urls else None
    return {"success": True, "message": "Payment added successfully", "data": data, "signed_url": signed_url}

def do_payouts(procurement_ids: str):
    # Format the procurement_ids
    procurement_ids = procurement_ids.replace(' ', ',')
    procurement_ids = json.loads(procurement_ids)

    # fetch the fund accounts of all farmers
    users_amount= {}
    procurements = Procurement.objects.filter(id__in=procurement_ids).values_list('id','user_to_id','amount')
    for p in procurements:
        users_amount[p[1]] = {'id': p[0], 'amount': p[2]}

    # Fetch UserBankAccount objects related to the users of the procurements
    user_fund_accounts = models.UserBankAccount.objects.filter(user_id__in=users_amount.keys()).values_list('user_id','fund_account')

    for ufa in user_fund_accounts:
        payout_res = composite_payout({
            'amount': users_amount[ufa[0]]['amount'],
            'procurement_id': users_amount[ufa[0]]['id'],
            'fund_acc': ufa[1]
        })

        with transaction.atomic():
            payout = models.Payout.objects.create(
                payout_id = payout_res['id'] if payout_res.get('id') else None,
                amount = users_amount[ufa[0]]['amount'],
                status = 'pending' if payout_res.get('id') else 'unpaid'
            )
            procurement = Procurement.objects.get(id=users_amount[ufa[0]]['id'])
            procurement.payout = payout
            procurement.save()

from insurance.models import InsuranceEnrollment
def update_insurance_status(ids,status):
    InsuranceEnrollment.objects.filter(id__in=ids).update(status=status)

# RAZORPAY WEBHOOKS
class RazorpayWebhooks(BaseViewWithoutAuthentication):
    def payment_link_paid(self, payload):
        models.Payment.objects.filter(payment_link_id=payload['payment_link']['entity']['id']).update(
            response = payload,
            status = 'paid',
        )

        # if payload['payment']['entity']['notes'].get('kutumbs'):
        #     # Function to send the insurance data to CA Life
        #     res=add_member_to_ca_life(payload['payment']['entity']['notes']['kutumbs'])

        if payload['payment']['entity']['notes'].get('procurement_ids'):
            do_payouts(payload['payment']['entity']['notes']['procurement_ids'])
        
        if payload['payment']['entity']['notes'].get('insurance_id'):
            update_insurance_status(payload['payment']['entity']['notes'].get('insurance_id'),1)
        
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)

    def payment_link_cancelled(self, payload):
        models.Payment.objects.filter(payment_link_id=payload['payment_link']['entity']['id']).update(
            response = payload,
            status = 'unpaid',
        )
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)
    
    def payout_failed(self, payload):
        models.Payout.objects.filter(payout_id=payload['payout']['entity']['id']).update(
            response = payload,
            status = 'unpaid',
        )
        if payload['payment']['entity']['notes'].get('insurance_id'):
            update_insurance_status(payload['payment']['entity']['notes'].get('insurance_id'),2)
        
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)
    
    def payout_success(self, payload):
        models.Payout.objects.filter(payout_id=payload['payout']['entity']['id']).update(
            response = payload,
            status = 'paid',
        )
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)
    
    def post(self,request):
        try:
            if not client.utility.verify_webhook_signature(request.body.decode(), request.headers.get('X-Razorpay-Signature'), settings.PAYMENT_WEBHOOK_SECRET):
                return req_response('Razorpay Signature Verification Failed', False, 'PV-RWPOS-1', status.HTTP_500_INTERNAL_SERVER_ERROR)

            req_data = request.data
            # print("req_data['event']", req_data['event'])

            if req_data['event'] == "payment_link.paid":
                return self.payment_link_paid(req_data['payload'])
            
            elif req_data['event'] == "payment_link.cancelled" or req_data['event'] == "payment_link.expired":
                return self.payment_link_cancelled(req_data['payload'])
            
            elif req_data['event'] == "payout.rejected" or req_data['event'] == "payout.reversed" or req_data['event'] == "payout.failed":
                return self.payout_failed(req_data['payload'])
            
            elif req_data['event'] == "payout.processed":
                return self.payout_success(req_data['payload'])
            
            return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)
        except Exception as e:
            print("Web hook exception: "+str(e))
            return req_response(constants.ERROR, False, 'PV-RWPOS-2', status.HTTP_500_INTERNAL_SERVER_ERROR, None, e)

