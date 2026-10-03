from django.shortcuts import render
from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from app_farm.utils import constants,response as res
from . import models
from verification.models import UserVerificationDocument
from django.shortcuts import render
from django.conf import settings
from app_farm.utils import helper
import requests
import json
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from django.urls import reverse

class CommonFunctions():
    headerss = {
        'Content-Type': 'application/json',
        'client_id':settings.ONEMONEY_CLIENT_ID,
        'client_secret':settings.ONEMONEY_CLIENT_SECRET,
        'organisationId':settings.ONEMONEY_ORGANISATION_ID,
        'appIdentifier':settings.ONEMONEY_APP_IDENTIFIER
    }
    def get_consent(self, data):
        result = {
            'data': None,
            'error_code': None,
            'message': None
        }
        try:
            url = settings.ONEMONEY_BASE_URL+"v2/requestconsent"

            payload = json.dumps({
                'partyIdentifierType': 'MOBILE',
                'partyIdentifierValue': data['phone'],
                'productID': settings.ONEMONEY_PRODUCT_ID,
                'accountID': data['phone']+'_'+data['user_id'],
                'vua': data['phone']+'@onemoney'
            })
            
            response = json.loads(requests.request("POST", url, headers=self.headerss, data=payload).text)
            if response['status'] != 'success':
                result['error_code'] = 'OV-CFGCON-01'
                result['message'] = constants.CONSENT_NOT_FOUND
                return result
            result['data'] = response['data']['consent_handle']
            return result
        except Exception as e:
            print(e)
            result['error_code'] = 'OV-CFGCON-02'
            result['message'] = constants.ERROR
            return result

    def get_url(self, consent_handle, return_url):
        result = {
            'data': None,
            'error_code': None,
            'message': None
        }
        try:
            url = settings.ONEMONEY_BASE_URL+"webRedirection/getEncryptedUrl"

            payload = json.dumps({
                "consentHandle": consent_handle,
                "redirectUrl": return_url
            })

            response = json.loads(requests.request("POST", url, headers=self.headerss, data=payload).text)
            print(response)
            if response['status'] != 'success':
                result['error_code'] = 'OV-CFGURL-01'
                result['message'] = constants.URL_NOT_FOUND
                return result
            result['data'] = response['data']['webRedirectionUrl']
            return result
        except Exception as e:
            print(e)
            result['error_code'] = 'OV-CFGURL-02'
            result['message'] = constants.ERROR
            return result
        
    def decrypt_url(self, data):
        result = {
            'data': None,
            'error_code': None,
            'message': None
        }
        try:
            url = settings.ONEMONEY_BASE_URL+"webRedirection/decryptUrl"

            payload = json.dumps({
                "webRedirectionURL": data
            })

            response = json.loads(requests.request("POST", url, headers=self.headerss, data=payload).text)

            if response['status'] != 'success':
                result['error_code'] = 'OV-CFDURL-01'
                result['message'] = constants.DECRYPT_URL_NOT_FOUND
                return result
            result['data'] = response['data']
            return result
        except Exception as e:
            result['error_code'] = 'OV-CFDURL-02'
            result['message'] = constants.ERROR
            return result
        
    def get_statements(self, consent_id):
        result = {
            'data': None,
            'error_code': None,
            'message': None
        }
        try:
            url = settings.ONEMONEY_BASE_URL+"getallfidata"

            payload = json.dumps({
                "consentID": consent_id
            })

            response = json.loads(requests.request("POST", url, headers=self.headerss, data=payload).text)

            if response['status'] != 'success':
                result['error_code'] = 'OV-CFGSTA-01'
                result['message'] = constants.TRANSACTIONS_NOT_FOUND
                return result
            result['data'] = response['data']
            return result
        except Exception as e:
            print(e)
            result['error_code'] = 'OV-CFGSTA-02'
            result['message'] = constants.ERROR
            return result


class BankVerify(APIView, CommonFunctions):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
        try:
            consent_handle = None
            new_consent = False
            result = res.ErrRes()
            try:
                consent = models.OnemoneyConsent.objects.get(user= str(request.user.id), status= 'Pending')

                consent_handle = consent.consent_handle
            except ObjectDoesNotExist:
                new_consent = True
                consent = self.get_consent({'phone': str(request.user.mobile_number), 'user_id': str(request.user.id)})

                if not consent.get('data'):
                    result['error_code'] = consent['error_code']
                    result['message'] = consent['message']
                    result['status_code'] = status.HTTP_404_NOT_FOUND
                    return Response(result, status=result['status_code'])
                consent_handle = consent['data']
                
            url = self.get_url(consent_handle, helper.replaceHttp(request.build_absolute_uri(reverse("onemoneyredirect"))))

            if not url.get('data'):
                result['error_code'] = url['error_code']
                result['message'] = url['message']
                result['status_code'] = status.HTTP_404_NOT_FOUND
                return Response(result, status=result['status_code'])

            if new_consent:
                consent = models.OnemoneyConsent.objects.create(
                    user= request.user,
                    status= 'Pending',
                    consent_handle= consent_handle
                )
            
            result = res.SuccRes()
            result['data'] = url['data']
            return Response(result, status=result['status_code'])
        except Exception as e:
            print(e)
            result = res.ErrRes()
            result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            result['message'] = constants.ERROR
            result['error_code'] = "OV-BVPOS-02"
            return Response(result, status=result['status_code'])
        
class OnemoneyRedirect(APIView, CommonFunctions):
    def get(self,request):
        try:
            ecres = request.GET.get("ecres")
            resdate = request.GET.get("resdate")
            fi = request.GET.get("fi")

            result = res.ErrRes()
            result['status_code'] = status.HTTP_404_NOT_FOUND
            if not (ecres and resdate and fi):
                result['message'] = constants.ERROR
                result['error_code'] = "OV-ORGET-01"
                return render(
                    request, 'bank_verify.html', {'data': json.dumps(result)}
                )
            
            decrypted_data = self.decrypt_url({'ecres': ecres, 'resdate': resdate, 'fi': fi})

            if not decrypted_data.get('data'):
                result['error_code'] = decrypted_data['error_code']
                result['message'] = decrypted_data['message']
                return render(
                    request, 'bank_verify.html', {'data': json.dumps(result)}
                )
            
            consent = models.OnemoneyConsent.objects.get(consent_handle= decrypted_data['data']['srcref'])
            
            if decrypted_data['data']['errorcode'] != '0':
                result['status_code'] = status.HTTP_400_BAD_REQUEST
                result['error_code'] = 'OV-ORGET-02'
                result['message'] = constants.CONSENT_REJECTED
                return render(
                    request, 'bank_verify.html', {'data': json.dumps(result)}
                )
            msg = 'Bank statements are being fetched.'
            helper.addVerification(consent.user,settings.ONEMONEY_DOCUMENT_ID,consent.id,"onemoney_onemoneyconsent_request",2,consent.user.id,msg)
            helper.updateDocumentStep(consent.user)
            
            result = res.SuccRes()
            result['status_code'] = status.HTTP_202_ACCEPTED
            result['message'] = 'Pending'
            return render(
                request, 'bank_verify.html', {'data': json.dumps(result)}
            )
        except Exception as e:
            print("eeeee")
            print(e)
            result = res.ErrRes()
            result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            result['message'] = constants.ERROR
            result['error_code'] = "OV-ORGET-03"
            return render(
                request, 'bank_verify.html', {'data': json.dumps(result)}
            )
        
class ConsentWebhook(APIView, CommonFunctions):
    def post(self, request):
        try:
            result = res.ErrRes()
            if helper.generate_signature(request.body) != request.headers.get('X-Webhook-Signature'):
                result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
                result['message'] = constants.ERROR
                result['error_code'] = "OV-CWPOS-01"
                return Response(result, status=result['status_code'])
            
            request_body = request.data
            try:
                consent = models.OnemoneyConsent.objects.get(consent_handle = request_body['consentHandle'])
                
                consent.status = request_body['eventStatus']
                consent.timestamp = request_body['timestamp']
                consent.consent_id = request_body['consentId']
                consent.vua = request_body['vua']
                consent.timestamp = request_body['timestamp']
                consent.save()

                if request_body['eventStatus'] == 'CONSENT_REJECTED':
                    msg = 'Something went wrong during bank statement fetch. Please try again.'
                    helper.addVerification(consent.user,settings.ONEMONEY_DOCUMENT_ID,consent.id,"onemoney_onemoneyconsent_request",0,consent.user.id,msg)
                    helper.updateDocumentStep(consent.user)
            except ObjectDoesNotExist:
                result['error_code'] = 'OV-CWPOS-02'
                result['message'] = constants.CONSENT_NOT_FOUND
                result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
                return Response(result, status=result['status_code'])
            
            result = res.SuccRes()
            return Response(result, status=result['status_code'])
        except Exception as e:
            print("1q1q1", e)
            result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            result['message'] = constants.ERROR
            result['error_code'] = "OV-CWPOS-03"
            return Response(result, status=result['status_code'])

class DataWebhook(APIView, CommonFunctions):
    def post(self, request):
        try:
            result = res.ErrRes()
            if helper.generate_signature(request.body) != request.headers.get('X-Webhook-Signature'):
                result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
                result['message'] = constants.ERROR
                result['error_code'] = "OV-DWPOS-01"
                return Response(result, status=result['status_code'])
            
            request_body = request.data
            try:
                consent = models.OnemoneyConsent.objects.get(consent_handle = request_body['consentHandle'], consent_id = request_body['consentId'])

                if consent.consent_id != request_body['consentId']:
                    result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
                    result['message'] = constants.ERROR
                    result['error_code'] = "OV-DWPOS-02"
                    return Response(result, status=result['status_code'])
                
                statements = self.get_statements(request_body['consentId'])

                if not statements.get('data') or len(statements.get('data')) == 0:
                    result['error_code'] = statements['error_code']
                    result['message'] = statements['message']
                    return render(
                        request, 'bank_verify.html', {'data': json.dumps(result)}
                    )

                msg = ''
                for statement in statements['data']:
                    print(len(statement['Transactions']['Transaction']))
                    csv = helper.export_csv_from_dicts(statement['Transactions']['Transaction'])

                    models.BankStatementVerifcation.objects.create(
                        consent = consent,
                        linkReferenceNumber = statement['linkReferenceNumber'],
                        maskedAccountNumber = statement['maskedAccountNumber'],
                        fiType = statement['fiType'],
                        bank = statement['bank'],
                        startDate = statement['Transactions']['startDate'],
                        endDate = statement['Transactions']['endDate'],
                        bank_statement = csv['data']
                    )
                    msg = msg + str(statement['maskedAccountNumber'])+', '
                msg = "Bank statement for "+ msg[:-2] +" fetched successfully"
                helper.addVerification(consent.user,settings.ONEMONEY_DOCUMENT_ID,consent.id,"onemoney_onemoneyconsent_request",1,consent.user.id,msg)
                helper.updateDocumentStep(consent.user)
            except ObjectDoesNotExist:
                result['error_code'] = 'OV-DWPOS-03'
                result['message'] = constants.CONSENT_NOT_FOUND
                result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
                return Response(result, status=result['status_code'])
            
            result = res.SuccRes()
            return Response(result, status=result['status_code'])
        except Exception as e:
            print("1q1q1", e)
            result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            result['message'] = constants.ERROR
            result['error_code'] = "OV-DWPOS-04"
            return Response(result, status=result['status_code'])
        
def get_bank_statements(user_id):
    try:
        result = []
        document = UserVerificationDocument.objects.get(user = user_id, document_type = settings.ONEMONEY_DOCUMENT_ID)
        statements = models.BankStatementVerifcation.objects.filter(consent = document.document_id)

        for statement in statements:
            result.append(statement.bank_statement)

        return result
    except:
        return []
