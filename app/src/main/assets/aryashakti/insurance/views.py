from django.shortcuts import render
from rest_framework import status
from django.db import transaction
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

from core.views import BaseView
from . import models,validator,serializer
from app_farm.utils import constants
from app_farm.utils.response import req_response
from verification.verification_apis.signzy import SignZyAuthClass
from app_farm.utils.helper import image_upload,private_image_upload,generate_multiple_signed_urls
from payment.views import insurance_bank_validation_logic, create_payment_link_common
from app_farm.models import OTPValidation
from payment.models import Payment


def get_aadhaar_details(front_img, back_img):
    signzy = SignZyAuthClass()
    adhar_imgs= generate_multiple_signed_urls([front_img,back_img])
    if front_img not in adhar_imgs.keys() and back_img not in adhar_imgs.keys():
        return None
    
    aadhaar_data = signzy.adhar_verification([adhar_imgs[front_img], adhar_imgs[back_img]])
    # print("aadhaar_data", aadhaar_data)

    if aadhaar_data.get('response').get('result').get('validBackAndFront') == True:
        summary = aadhaar_data.get('response').get('result').get('summary')
        if summary.get('number') and summary.get('name') and summary.get('dob') and summary.get('gender') and summary.get('splitAddress'):
            obj = {}
            names = summary['name'].split(' ')
            obj['masked_aadhaar'] = summary['number']
            obj['first_name'] = names[0]
            obj['last_name'] = names[-1]
            obj['dob'] = summary['dob']
            obj['gender'] = summary['gender']
            
            address = summary.get('splitAddress')
            if address.get('addressLine') and address.get('pincode') and address.get('district')[0] and address.get('state')[0] and address.get('state')[0][0] and address.get('city')[0] and address.get('country')[2]:
                addresses = None
                if ',' in address['addressLine']:
                    addresses = address['addressLine'].split(',', 1)
                else:
                    temp = address['addressLine'].split(' ', 5)
                    addresses = [' '.join(temp[:5]), temp[5]]
                obj['pincode'] = address['pincode']
                obj['city'] = address['city'][0]
                obj['state'] = address['state'][0][0]
                obj['district'] = address['district'][0]
                obj['country'] = address['country'][2]
                obj['address1'] = addresses[0]
                obj['address2'] = addresses[1]

                return obj
    return None


def get_aadhaar_details_with_otp(obj):
    signzy = SignZyAuthClass()
    response = signzy.adhar_otp_verify(obj)
    
    if 'data' in response.keys() and response['statusCode']==200  :
        obj = {}
        data=response['data']
        obj['masked_aadhaar'] = data['aadhaar_number']
        names = data['full_name'].split(' ')
        obj['first_name'] = names[0]
        obj['last_name'] = names[-1]
        obj['dob'] = data['dob']

        if data['gender'] == 'M':
            obj['gender']= "Male"
        elif data['gender'] == 'F':
            obj['gender']= "Female"
        obj['pincode'] = data['zip']    



        if 'address' in data.keys():
            address = data.get('address')          
                        
            obj['city'] = address['loc']
            obj['state'] = address['state']
            obj['district'] = address['dist']
            obj['country'] = address['country']
            obj['address1'] = address['street']+", "+address['loc']+", "+address['subdist']
            obj['address2'] = address['po']+", "+address['dist']+", "+address['state'] 
            

        return obj
    return None


# Create your views here.
class AddMember(BaseView):
    def add_member(self, request, err_code, req_data):

        if 'front_aadhaar' in req_data.keys():
            front_aadhaar = private_image_upload(req_data['front_aadhaar'],"documents/adhar"/+req_data['phone']+"/")
            back_aadhaar = private_image_upload(req_data['back_aadhaar'],"documents/adhar"+req_data['phone']+"/")
        
            aadhaar_data = get_aadhaar_details(front_aadhaar, back_aadhaar)
        else:
            aadhaar_data = get_aadhaar_details_with_otp(req_data)

        #aadhaar_data = get_aadhaar_details_with_otp(req_data)
        # aadhaar_data = {'masked_aadhaar': '000000002393', 'first_name': 'Suraj', 'last_name': 'Kumar', 'dob': '04/12/1994', 'gender': 'MALE', 'pincode': '854105', 'city': 'KATIHAR', 'state': 'BIHAR', 'district': 'KATIHAR', 'country': 'INDIA', 'address1': 'S O JAICHAND PRASAD SAH', 'address2': 'M G ROAD,BARBANNA TOLA'}

        if not aadhaar_data:
            return req_response(constants.INVALID_AADHAAR, False, err_code+'3', status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            member = models.Member.objects.create(
                **aadhaar_data,
                phone = req_data['phone'],
                email = req_data.get('email'),
                # aadhaar_num = req_data['aadhaar_num'],
                
                front_aadhaar = front_aadhaar,
                back_aadhaar = back_aadhaar
            )
            member = serializer.MemberDetailsSerializer(member, many=False).data

            if req_data.get('gender').lower() == 'male' and not req_data.get('kutumb_id'):
                kutumb = models.Kutumb.objects.create(
                    kutumb_id = 'ARYA-'+ constants.INDIAN_STATES[req_data['fpo_state']] +'-'+ req_data['fpo_name'] +'-'+ req_data['phone'],
                    husband_id = member['id'],
                    added_by_org_id = req_data['org_id'],
                )
            elif req_data.get('gender').lower() == 'female' and req_data.get('kutumb_id'):
                kutumb = models.Kutumb.objects.get(id = req_data['kutumb_id'])
                kutumb.wife_id = member['id']
                kutumb.status = 'wife_aadhaar'
                kutumb.added_by_org_id = req_data['org_id']
                kutumb.save()
            else:
                transaction.set_rollback(True)
                return req_response(constants.GENERAL_ERROR, False, err_code+'4', status.HTTP_400_BAD_REQUEST)

        return req_response(constants.SUCCESS, True, '', status.HTTP_201_CREATED, {
            'kutumb_id': req_data['kutumb_id'] if req_data.get('kutumb_id') else kutumb.id,
            **member
        })
    
    def update_member(self, request, err_code, req_data):
        
        height=req_data.get('height')
        weight=req_data.get('weight')
        face_closeup_img = image_upload(req_data['face_closeup_img'])
        height_determination_img = image_upload(req_data['height_determination_img'])
        print(face_closeup_img)
        print(height_determination_img)
        
        member = models.Member.objects.get(id=req_data['member_id'])
        if req_data.get('pincode') and req_data.get('state') and req_data.get('address1'):
            member.pincode = req_data.get('pincode')
            member.state = req_data.get('state')
            member.address1 = req_data.get('address1')
            member.address2 = req_data.get('address2')
        if height and weight:
            member.height= height
            member.weight= weight
        
        if face_closeup_img:
            member.face_closeup_img= face_closeup_img
        if height_determination_img:
            member.height_determination_img= height_determination_img

        member.save()
        # data = serializer.MemberDetailsSerializer(member, many=False)

        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK)
    
    def get_member_details(self, request, err_code, req_data):
        member = models.Member.objects.get(id=req_data['member_id'])
        data = serializer.MemberDetailsWithBankDetailsSerializer(member, many=False)

        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data.data)

    def post(self, request):
        return self.common_function(request, 'IV-AMPOS-', validator.AddMemberValidator, self.add_member)
    
    def put(self, request):
        return self.common_function(request, 'IV-UMPOS-', validator.UpdateMemberValidator, self.update_member)
    
    def get(self, request):
        return self.common_function(request, 'IV-GMDGET-', validator.MemberDetailsValidation, self.get_member_details)
    
class MemberBankValidation(BaseView):
    def member_bank_validation(self, request, err_code, req_data):
        member = models.Member.objects.get(id = req_data['member_id'])
        return insurance_bank_validation_logic(member, request.user, req_data)
    
    def post(self, request):
        return self.common_function(request, 'IV-MBVPOS-', validator.MemberBankValidation, self.member_bank_validation)



class InsuranceBankValidation(BaseView):
    def member_bank_validation(self, request, err_code, req_data):
        insurance = models.InsuranceEnrollment.objects.get(id = req_data['insurance_id'])
        return insurance_bank_validation_logic(insurance, request.user, req_data,1)
    
    def post(self, request):
        return self.common_function(request, 'IV-IBV-POS-', validator.InsuranceBankValidation, self.member_bank_validation)
    
    
class SameBankAccount(BaseView):
    def same_bank_account(self, request, err_code, req_data):
        wife = models.Member.objects.get(id = req_data['member_id'])
        husband = models.Member.objects.get(id = req_data['husband_id'])

        if wife.gender != 'Female':
            return req_response('Bank account can be same of wife only.', False, err_code+'3', status.HTTP_400_BAD_REQUEST)
        
        if husband.husband.first().id != wife.wife.first().id:
            return req_response('Husband and Wife does not belong to same Kutumb.', False, err_code+'4', status.HTTP_400_BAD_REQUEST)
        
        wife.bank_acc = husband.bank_acc
        wife.save()
        wife = serializer.MemberDetailsWithBankDetailsSerializer(wife, many=False)
        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, wife.data)
    
    def post(self, request):
        return self.common_function(request, 'IV-SBAPOS-', validator.SameBankAccountValidation, self.same_bank_account)
    
class KutumbsSummary(BaseView):
    def kutumbs_summary(self, request, err_code, req_data):
        kutumbs = models.Kutumb.objects.filter(added_by_org = req_data['org_id'])
        data = serializer.KutumbsSerializer(kutumbs, many=True)
        obj = {
            'kutumbs_added': 0,
            'coi_generated': 0,
            'reconcilation_pending': []
        }

        for k in data.data:
            if k['status'] == 'completed':
                obj['kutumbs_added'] += 1
            elif k['status'] == 'reconcilation_pending':
                obj['reconcilation_pending'].append(k['id'])
            elif k['status'] == 'coi_generated':
                obj['coi_generated'] += 1

        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, obj)
    
    def get(self, request):
        return self.common_function(request, 'IV-KSGET-', validator.KutumbsSummaryValidator, self.kutumbs_summary)
    
class GetIncompleteKutumbs(BaseView):
    def get_incomplete_kutumbs(self, request, err_code, req_data):
        kutumbs = models.Kutumb.objects.filter(~Q(status='completed'),~Q(status='reconcilation_pending'),~Q(status='coi_generated'),added_by_org=req_data['org_id'])
        data = serializer.KutumbDetailsSerializer(kutumbs, many=True)

        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data.data)
    
    def get(self, request):
        return self.common_function(request, 'IV-GIKGET-', validator.KutumbsSummaryValidator, self.get_incomplete_kutumbs)
    
class GetClaimableKutumbs(BaseView):
    def get_incomplete_kutumbs(self, request, err_code, req_data):
        kutumbs = models.Kutumb.objects.filter(status='coi_generated',added_by_org=req_data['org_id'])
        data = serializer.ClaimableKutumbDetailsSerializer(kutumbs, many=True)

        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, data.data)
    
    def get(self, request):
        return self.common_function(request, 'IV-GIKGET-', validator.KutumbsSummaryValidator, self.get_incomplete_kutumbs)
    
class AddNominee(BaseView):
    def add_nominee(self, request, err_code, req_data):
        with transaction.atomic():
            models.Kutumb.objects.filter(id=req_data['kutumb_id']).update(status='completed')

            nominee = models.Nominee.objects.create(
                phone = req_data['phone'],
                name = req_data['name'],
                relationship = req_data['relationship'],
                kutumb_id = req_data['kutumb_id'],
                assignee = req_data.get('assignee'),
                assignee_relationship = req_data.get('assignee_relationship')
            )
            # data = serializer.NomineeSerializer(nominee, many=False)

            return req_response(constants.SUCCESS, True, '', status.HTTP_201_CREATED)
    
    def post(self, request):
        return self.common_function(request, 'IV-KSGET-', validator.AddNomineeValidator, self.add_nominee)

class VerifyConsent(BaseView):
    def verify_consent(self, request, err_code, req_data):
        try:
            OTPValidation.objects.get(phone_number=req_data['phone'],otp_value=req_data['otp'],status=0).delete()
        except ObjectDoesNotExist:
            return req_response(constants.INVALID_OTP, False, err_code+'3', status.HTTP_400_BAD_REQUEST)

        kutumb = models.Kutumb.objects.get(id=req_data['kutumb_id'])
        kutumb.status = kutumb.status.split('_')[0] + '_consent'
        kutumb.save()

        return req_response(constants.VALID_OTP, True, '', status.HTTP_200_OK)

    def post(self, request):
        return self.common_function(request, 'IV-VCPOS-', validator.VerifyConsentValidator, self.verify_consent)




class CashPayment(BaseView):
    def cash_payment(self, request, err_code, req_data):
        cash_receipt = image_upload(req_data['cash_receipt'])
        with transaction.atomic():
            payment = Payment.objects.create(
                amount = req_data['amount'],
                payment_type = 'cash',
                response = {
                    'cash_receipt': cash_receipt,
                    'paid_for': req_data['kutumb_id']
                },
                status = 'paid'
            )

            kutumb = models.Kutumb.objects.get(id=req_data['kutumb_id'])
            kutumb.payment = payment
            kutumb.status = 'reconcilation_pending'
            kutumb.save()

        return req_response(constants.PAYMENT_SUCCESS, True, '', status.HTTP_200_OK)

    def post(self, request):
        return self.common_function(request, 'IV-CPPOS-', validator.CashPaymentValidator, self.cash_payment)
    
class OnlinePayment(BaseView):
    def online_payment(self, request, err_code, req_data):
        mobile_number = request.user.mobile_number if '+91' in str(request.user.mobile_number) else '+91'+str(request.user.mobile_number)
        
        with transaction.atomic():
            payment = Payment.objects.create(
                amount = req_data['amount'],
                payment_type = 'online',
                status = 'pending'
            )

            kutumbs_updated = models.Kutumb.objects.filter(id__in=req_data['kutumb_ids']).update(
                payment = payment,
            )
            if kutumbs_updated != len(req_data['kutumb_ids']):
                transaction.set_rollback(True)
                return req_response(constants.ERROR, False, err_code+'-3', status.HTTP_400_BAD_REQUEST, None, 'Please send correct kutumbs.')
            
            req_data['description'] = 'Payment for Insurance.'
            req_data['notes'] = {
                'kutumbs': req_data['kutumb_ids']
            }
            
            link_data = create_payment_link_common(payment.id, req_data, request, mobile_number)

            if not link_data['status'] and link_data['status'] != 'created':
                transaction.set_rollback(True)
                return req_response(constants.ERROR, False, err_code+'-4', status.HTTP_400_BAD_REQUEST)
            
            payment.payment_link_id = link_data['id']
            payment.save()

        return req_response(constants.SUCCESS, True, '', status.HTTP_200_OK, link_data['short_url'])

    def post(self, request):
        return self.common_function(request, 'IV-OPPOS-', validator.OnlinePaymentValidator, self.online_payment)



from rest_framework.views import APIView
from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated

class ImageVerificationForHealth(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self,request):
        pass
        
from datetime import datetime


class AadhaarEstimateAPIView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            dob_str = request.data.get("dob")
            if not dob_str:
                return req_response("Date of birth is required.",False,"AEAV-POST-01",status.HTTP_400_BAD_REQUEST)
           
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
            today = datetime.today().date()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

            # Sample logic for premium based on age
            if age < 18:
                amount = 0
            elif age <= 30:
                amount = 500
            elif age <= 45:
                amount = 750
            elif age <= 60:
                amount = 1000
            else:
                amount = 1500

            return req_response("Estimated amount based on age",True,"",status.HTTP_200_OK,{"age": age,"estimated_amount": amount})
       

        except ValueError:
            return req_response("Invalid date format. Use YYYY-MM-DD.",False,"AEAV-POST-01",status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return req_response(str(e),False,"AESAV-POST-01",status.HTTP_500_INTERNAL_SERVER_ERROR)



class AadhaarEnrollmentAPIView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request):
        req_data = request.data


        with transaction.atomic():

            payload = {
                "added-by": request.user,
                "aadhaar_number": req_data.get('aadhaar_number'),
                "first_name": req_data.get('first_name'),
                "last_name": req_data.get('last_name'),
                "dob": req_data.get('dob'),
                "gender": req_data.get('gender'),
                "city": req_data.get('city'),
                "state": req_data.get('state'),
                "country": req_data.get('country'),
                "pin": req_data.get('pin'),
                "address": req_data.get('address1') + ", " + req_data.get('address2'),
                "front_aadhaar": req_data.get('front_aadhaar'),
                "back_aadhaar": req_data.get("back_aadhaar"),

                # Fields from frontend
                "mobile": req_data.get("mobile"),
                "occupation": req_data.get("occupation"),
                "education": req_data.get("education"),
                "smoker_status": req_data.get("smoker_status"),
                "photograph_upload": req_data.get("photograph_upload"),

                "nominee_first_name": req_data.get("nominee_first_name"),
                "nominee_last_name": req_data.get("nominee_last_name"),
                "nominee_gender": req_data.get("nominee_gender"),
                "nominee_dob": req_data.get("nominee_dob"),
                "nominee_relation": req_data.get("nominee_relation"),
                "nominee_mobile": req_data.get("nominee_mobile"),
                "nominee_email": req_data.get("nominee_email"),

                "bank_name": req_data.get("bank_name"),
                "account_number": req_data.get("account_number"),
                "ifsc": req_data.get("ifsc"),
                "height": req_data.get("height"),
                "weight": req_data.get("weight"),
                "amount": req_data.get("amount"),
                "social_scheme": req_data.get("social_scheme"),

            }

            serializers = serializer.InsuranceEnrollmentSerializer(data=payload)
            insurance_data_=None
            if serializers.is_valid():
                insurance_data_= serializers.save()

            if insurance_data_:
                return req_response("Enrollment submitted successfully", True, "", status.HTTP_201_CREATED, { "insurance":serializers.data
                                                                                                                })

        return req_response("Invalid input", False, "AEAV-POST-01", status.HTTP_400_BAD_REQUEST, serializers.errors)


class EnrollmentPaymentUrl(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self,request):
        data = request.data
        insurance_id= data.get('insurance_id')
        try:
            insurance_data_= models.InsuranceEnrollment.objects.get(id=insurance_id)
        except models.InsuranceEnrollment.DoesNotExist:
            return req_response("Insurance not found", False, "EPU-POST-01", status.HTTP_404_NOT_FOUND)


        if insurance_data_:
                
                payment = Payment.objects.create(
                            amount = insurance_data_.id,
                            payment_type = 'online',
                            status = 'pending'
                        )
                insurance_data_.payment=payment

                insurance_data_.save()

                serializer_= serializer.InsuranceEnrollmentSerializer(insurance_data_,many=False)
                if serializer_:

                    insurance_enroll= serializer_.data
                    req_data={'insurance_id':[insurance_data_.id]}
                    req_data['description'] = 'Payment for Procurement.'
                    req_data['amount'] = insurance_enroll['amount']
                    req_data['notes'] = {
                        'procurement_ids': [insurance_data_.id]
                    }
                
                    link_data = create_payment_link_common(payment.id, req_data, request, insurance_data_.mobile)

                    if not link_data['status'] and link_data['status'] != 'created':
                        transaction.set_rollback(True)
                        return req_response(constants.ERROR, False, "PRV-PPPOST-01", status.HTTP_400_BAD_REQUEST)
                
                    payment.payment_link_id = link_data['id']
                    payment.save()   

                    return req_response("Enrollment submitted successfully", True, "", status.HTTP_200_OK, {"payment":{
                                                                                                                 "payment_link":payment.payment_link_id,
                                                                                                                        "payment_id":payment.id,
                                                                                                                        "payment_amount":payment.amount,
                                                                                                                        "payment_url":link_data['short_url']
                                                                                                                        },
                                                                                                                "insurance":insurance_enroll
                                                                                                                })
        return req_response("Something is wrong", False, "EPU-POST-02", status.HTTP_400_BAD_REQUEST)


class CheckStatus(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request,insurance_id):
        try:
            insurance= models.InsuranceEnrollment.objects.get(id=insurance_id)
        except models.InsuranceEnrollment.DoesNotExist :
            return req_response("Insurance not found", False, "EPU-POST-01", status.HTTP_404_NOT_FOUND)

        return req_response("Enrollment submitted successfully", True, "", status.HTTP_200_OK, serializer.InsuranceEnrollmentSerializer(insurance,many=False).data)


class UpdateInsuranceEsignSuccess(APIView):
    def post(self,request,ref_id):
        models.InsuranceEnrollment.objects.filter(id=ref_id).update(status_esign=1)
        return req_response("Enrollment updated successfully", True, "", status.HTTP_200_OK)


class UpdateInsuranceEsignFailure(APIView):
    def post(self,request,ref_id):
        models.InsuranceEnrollment.objects.filter(id=ref_id).update(status_esign=2)
        return req_response("Enrollment updated successfully", True, "", status.HTTP_200_OK)
    

class VerifyConsentInsurance(BaseView):
    def verify_consent(self, request, err_code, req_data):
        try:
            OTPValidation.objects.get(phone_number=req_data['phone'],otp_value=req_data['otp'],status=0).delete()
        except ObjectDoesNotExist:
            return req_response(constants.INVALID_OTP, False, err_code+'3', status.HTTP_400_BAD_REQUEST)

        insurance = models.InsuranceEnrollment.objects.get(id=req_data['insurance_id'])
        insurance.status_esign = 1
        insurance.save()

        return req_response(constants.VALID_OTP, True, '', status.HTTP_200_OK)

    def post(self, request):
        return self.common_function(request, 'IV-VCIPOS-', validator.VerifyInsuranceConsentValidator, self.verify_consent)
