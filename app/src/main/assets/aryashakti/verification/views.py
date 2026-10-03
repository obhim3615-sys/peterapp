from django.shortcuts import render
from rest_framework.views import APIView
from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from . import validator
from app_farm.utils import constants,response as res
from rest_framework import status
from .verification_apis.signzy import SignZyAuthClass
from .verification_apis.aryaprofin import AryaProfin
import json
from . import models
from django.shortcuts import render
from django.conf import settings
from django.urls import reverse
from . import serializers
from django.db.models import Q
from app_farm.utils.helper import private_image_upload,generate_multiple_signed_urls,addVerification,getDocumentDetails,updateDocumentStep,delete_gcs_file
from django.urls import reverse
from django.db.models import Case,When,IntegerField,Q
import datetime
from app_farm import models as models2
from app_farm.utils import helper
from app_farm import serializers as serializers2
from onemoney.views import get_bank_statements
from django.http import HttpResponse
from django.core.mail import send_mail
from cms.models import Setting
# Create your views here.



class Verify(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request):
        return Response({"success":True})


class Pan(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request):
        try:            
            validation = validator.PANVerification(data=request.POST)
            if not validation.is_valid():
                result = res.ErrRes()
                result['message'] = constants.INVALID_BODY
                result['error_code'] = "VVPP-01"
                result['data'] = validation.errors
                return Response(result, status=result['status_code'])
            response=[]
            for i in request.POST.getlist('pan_number'):
                data_sent={"pan_number":i}
                signzy= SignZyAuthClass()
                response_pan= signzy.pan_verification(data_sent,request.POST.get('type_pan'))
                if(response_pan):
                    response.append(response_pan)
                print(response)
            if len(response)>0:
                result=res.SuccRes()
                result['data']=response
                return Response(result,status=result['status_code'  ])
            
            result = res.ErrRes()
            result['message'] = constants.ERROR
            result['error_code'] = "VVPP-03"
            return Response(result, status=result['status_code'])
        except Exception as e:
             result = res.ErrRes()
             result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
             result['message'] = constants.ERROR+" "+str(e)
             result['error_code'] = "VVPP-02"
             return Response(result, status=result['status_code'])
             

class PanCreate(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request):
        try:            
            data= json.loads(request.body)[0]
            validation = validator.PANSaveVerification(data=data)
            if not validation.is_valid():
                result = res.ErrRes()
                result['message'] = constants.INVALID_BODY
                result['error_code'] = "VVSR-01"
                result['data'] = validation.errors
                return Response(result, status=result['status_code'])
            
            if not data['bd_email']:
                result = res.ErrRes()
                result['message'] = "Please select BD email"
                result['error_code'] = "VVSR-01"
                result['data'] = validation.errors
                return Response(result, status=result['status_code'])

            models.organizations.objects.filter(id=request.user.organization.id).update(relationship_manager_name=data['bd_email'])
            pan_user= models.PanVerifcation.objects.update_or_create(
                    user=request.user,
                    organization=request.user.organization,
                      defaults={ 
                    "pan_number":data['response']['result']['number'],
                    "pan_dob":None,
                    "pan_name":data['response']['result']['name'],
                    "father_name":"",
                    "response_details":json.dumps(data),                               
                    }
                
            )
            if(pan_user):
                    verfication= models.Document.objects.filter(name="PAN").first()                    
                    # verfication= models.Document.objects.get(id=data['verification_id'])
                    addVerification(request.user,str(verfication.id),pan_user[0].id,"verification_panuser_request")
                    updateDocumentStep(request.user)
                    result=res.SuccRes()
                    result['status_code']=status.HTTP_201_CREATED
                    result['message']="Pan is saved"
                    return Response(result, status=result['status_code'])
            result = res.ErrRes()
            result['message'] = constants.ERROR
            result['error_code'] = "VVSR-02"
            return Response(result, status=result['status_code'])
        
        except Exception as e:
             result = res.ErrRes()
             result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
             result['message'] = constants.ERROR+" "+str(e)
             result['error_code'] = "VVSR-03"
             return Response(result, status=result['status_code'])
         
         


class PanSubmitView(APIView):
    #  authentication_classes = [CustomTokenAuthentication]
    #  permission_classes = [IsAuthenticated]
     def get(self,request):          
          verfication= models.Document.objects.filter(name="PAN").first()
          bd_email=models.BDProfin.objects.all()
          return render(
            request,
            'pan_verify.html',
            {   
                'bd_email':bd_email,
                'token':request.GET.get('token'),
                'verification_id':str(verfication.id)
            }
        )
     

class PanUrl(APIView):
     authentication_classes = [CustomTokenAuthentication]
     permission_classes = [IsAuthenticated]
     def get(self,request):
        result=res.SuccRes()        
        result['message']="You can use url"        
        result['data']=helper.replaceHttp(request.build_absolute_uri(reverse('panview')))     
          
        return Response(result, status=result['status_code'])


class DigiLockerUrlCreation(APIView):
     authentication_classes = [CustomTokenAuthentication]
     permission_classes = [IsAuthenticated]
     def get(self, request,user_id=None):
        # try:
            if user_id:
                # If user_id is provided from the frontend, use that user
                try:
                    user = models2.user.objects.get(id=user_id)
                except models2.user.DoesNotExist:
                    user=None           
            
            else:
                # Otherwise, use the user from the request
                user = request.user
            
            created_by=request.user            
            if not user:
                result = res.ErrRes()
                result['status_code'] = status.HTTP_404_NOT_FOUND
                result['message'] = "User not found"
                result['error_code'] = "VVDUC-02"
                return Response(result, status=result['status_code'])

            signzy= SignZyAuthClass()
            response= signzy.createDigiLockerUrl(request,"user",0,user,created_by)
            # callback_url =helper.replaceHttp(request.build_absolute_uri(reverse('verifyadhar',args=["user",user.id,0,created_by.id]))),
            # redirect_url = helper.replaceHttp(request.build_absolute_uri(reverse('verifyadharcompleted')))
            # atms =AtMS()
            # response=atms.digilocker_info_request(user.email,callback_url,redirect_url)

            result=res.SuccRes()
            result['data']=response
            return Response(result,status=result['status_code'])
        # except Exception as e:
        #     result = res.ErrRes()
        #     result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
        #     result['message'] = constants.ERROR+" "+str(e)
        #     result['error_code'] = "VVDUC-01"
        #     return Response(result, status=result['status_code'])
        
class DigiLockerGetEAdhar(APIView):
     authentication_classes = [CustomTokenAuthentication]
     permission_classes = [IsAuthenticated]
     def post(self, request):
        try:
            request_data=json.loads(request.body)
            validation = validator.EadharVerification(data=request_data)
            if not validation.is_valid():
                result = res.ErrRes()
                result['message'] = constants.INVALID_BODY
                result['error_code'] = "VVDGE-01"
                result['data'] = validation.errors
                return Response(result, status=result['status_code'])
            signzy= SignZyAuthClass()
            response= signzy.getEaadhar(request_data.get('req_id'))
            
            json_res=json.loads(response)
            if json_res:
                if 'error' in json_res.keys():
                    result = res.ErrRes()
                    result['message'] = json_res['error']['message']
                    result['error_code'] = "VVDGE-03"
                    return Response(result, status=result['status_code'])
            data= models.AdharVerifcation.objects.update_or_create(user=request.user,
                                                            defaults={
                                                             "response_details":response
                                                            }
                                                             )
            # verfication= models.Document.objects.get(id=request.GET.get('verfication_id'))
            if data:
                addVerification(request.user,request_data.get('verification_id'),data[0].id,"verification_adharuser_request")
                updateDocumentStep(request.user)
                result=res.SuccRes()
                result['status_code']=status.HTTP_201_CREATED
                result['message']="Adhar is saved"
                return Response(result, status=result['status_code'])
            result = res.ErrRes()
            result['message'] = constants.ERROR
            result['error_code'] = "VVDGE-04"
            return Response(result, status=result['status_code'])
        except Exception as e:
            result = res.ErrRes()
            result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            result['message'] = constants.ERROR+" "+str(e)
            result['error_code'] = "VVDGE-05"
            return Response(result, status=result['status_code'])
             



class GetGSTByPAN(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request):
        try:
            try:
                panData= models.PanVerifcation.objects.get(user=request.user)
            except models.PanVerifcation.DoesNotExist:
                panData=None
            if(panData):
                signzy= SignZyAuthClass()
                response= signzy.getGSTValue(panData.pan_number)
                result=res.SuccRes()
                result['data']=response
                if 'error'in response.keys():
                    result = res.ErrRes()
                    result['message'] =response['error']['message']
                    result['status_code'] =response['error']['statusCode']
                    result['error_code'] ="VVGGBG-02"
                    return Response(result,status=result['status_code'])
                return Response(result,status=result['status_code'])
            
            result = res.ErrRes()
            result['message'] = "Pan not found."
            result['error_code'] = "VVGGBG-01"
            result['status_code'] = status.HTTP_404_NOT_FOUND
            return Response(result, status=result['status_code'])

        except Exception as e:
            result = res.ErrRes()
            result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            result['message'] = constants.ERROR+" "+str(e)
            result['error_code'] = "VVGGBP-02"
            return Response(result, status=result['status_code'])
         
    def post(self,request):
        try:
            response= json.loads(request.body)
            validation = validator.GSTSaveVerification(data=json.loads(request.body))
            if not validation.is_valid():
                result = res.ErrRes()
                result['message'] = constants.INVALID_BODY
                result['error_code'] = "VVGGBP-01"
                result['data'] = validation.errors
                return Response(result, status=result['status_code'])
            
            
            data= models.GSTData.objects.update_or_create(user=request.user,
                                                            defaults={
                                                             "gstin":response['gstin'],
                                                             "registrationDate":response.get('registrationDate'),
                                                             "principalAddress":response.get('principalAddress'),                                                             
                                                             "response":response,
                                                            }
                                                             )
            if data:
                addVerification(request.user,response.get('verification_id'),data[0].id,"verification_gstuser_request")
                updateDocumentStep(request.user)
                result=res.SuccRes()
                result['status_code']=status.HTTP_201_CREATED
                result['message']="GST is saved"
                return Response(result, status=result['status_code'])
            result = res.ErrRes()
            result['message'] = constants.ERROR
            result['error_code'] = "VVGGBP-04"
            return Response(result, status=result['status_code'])
        except Exception as e:
            result = res.ErrRes()
            result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            result['message'] = constants.ERROR+" "+str(e)
            result['error_code'] = "VVGGBP-02"
            return Response(result, status=result['status_code'])



class GetVerificationStatus(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request,user_id=None):
        
        if user_id:
            # If user_id is provided from the frontend, use that user
            try:
                user = models2.user.objects.get(id=user_id)
            except models2.user.DoesNotExist:
                user=None
        else:
            # Otherwise, use the user from the request
            user = request.user
        
        if not user:
            result = res.ErrRes()
            result['status_code'] = status.HTTP_404_NOT_FOUND
            result['message'] = "User not found"
            result['error_code'] = "VVGVS-02"
            return Response(result, status=result['status_code'])
        
        user_verification= getDocumentDetails(user)
        updateDocumentStep(user,user_verification)
        
        serialized= serializers.Documenterializer(user_verification,many=True)
        if(serialized):
            result=res.SuccRes()
            result['data']=serialized.data
            mobile_verify={
                "name":"Mobile verification",
                "status":True,

            }
            if user.otp_verfied:
                mobile_verify['is_verified']=1
            else:
                mobile_verify['is_verified']=0
            
            result['data'].append(mobile_verify)
            return Response(result,status=result['status_code'])
        
        result=res.ErrRes()
        result['error_code'] = "VVGVS-01"

        return Response(result,status=result['status_code'])



class GetUserJourney(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
        unsecured_user= models.UnsecureLoanStep.objects.filter(Q(unsecure_step__user_id=request.user)|Q(unsecure_step__isnull=True)).order_by('id').all().annotate(
            is_completed=Case(When(Q(unsecure_step__user_id=request.user) & Q(unsecure_step__status=1), then=1),When(Q(id=3) & Q(unsecure_step__isnull=True), then=2),default=0,output_field=IntegerField())
            )
        serialized= serializers.UnsecureLoanStepSerializer(unsecured_user,many=True)
        if(serialized):
            result=res.SuccRes()
            result['data']=serialized.data
            return Response(result,status=result['status_code'])
        
        result=res.ErrRes()
        result['error_code'] = "VVGUJ-01"

        return Response(result,status=result['status_code'])
    


class CreateLoanLead(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request):
        pan_data=adhardata=gst_data=compliance_data={}
        pan_data_query= models.PanVerifcation.objects.filter(user=request.user).last()
        adhardata_query=models.AdharVerifcation.objects.filter(user=request.user).last()
        gst_data_query=models.GSTData.objects.filter(user=request.user).last()
        compliance_query=models2.compliance.objects.filter(user_id=request.user,status="Active",document_name="bankStatement").all()
        bank_statement_data=get_bank_statements(request.user.id)

        if pan_data_query is not None:
            pan_data=serializers.PanSerializer(pan_data_query)
            if pan_data:
                pan_data= pan_data.data            
       

        if adhardata_query is not None:
            adhardata=serializers.AdharSerializer(adhardata_query)
            if adhardata:
                adhardata= adhardata.data
        

        if gst_data_query is not None:
            gst_data=serializers.GSTSerializer(gst_data_query)
            if gst_data:
                gst_data=gst_data.data
            
        if compliance_query is not None:
            compliance_data=serializers2.complianceSerializer(compliance_query,many=True)
            if compliance_data:
                compliance_data=compliance_data.data

        
        bd_email=request.user.organization.relationship_manager_name
        if(not bd_email or bd_email==""):
            bd_value=Setting.objects.getKey('DEFAULT_BD')
            bd_email=bd_value.value

        models.organizations.objects.filter(id=request.user.organization.id).update(relationship_manager_name=bd_email)
        
        data={
            "pan":pan_data,
            "state":request.user.organization.state,
            "address":request.user.organization.manual_address,
            "pincode":request.user.organization.pincode,
            "contact_no":request.user.organization.fpo_contact_no,
            "bd_email":bd_email,
            #"adhar":adhardata,
            #"gst":gst_data,
            "uploads":compliance_data,
            "bank_statements":bank_statement_data
        }
        

        return res.req_response("Data found",True,"",status.HTTP_200_OK,data)

        

class VerifyLogic(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self,request):
        pan_data_query= models.PanVerifcation.objects.filter(user=request.user).last()
        result={}
        result_data=request.data
        allowedIndividualCibil=Setting.objects.getKey('ALLOWED_INDIVIDUAL_CIBIL')
        allowedbusinessCibil=Setting.objects.getKey('ALLOWED_BUISNESS_CIBIL')
        cibilnumber=0
        cibilallowed=True
        if result_data['status']:
            indcibil=result_data['data']['indcibil']
            businesscibil=result_data['data']['compnaycibil']
            leadid=result_data['data']['leadId']
            dpd_status=result_data['data']['dpd_status']
            dpd_fail=result_data['data']['dpd_fail']
            write_off_status=result_data['data']['write_off_status']
            write_off_fail=result_data['data']['write_off_fail']
            individual_flag=0
            for cibil in indcibil:
                models.OrganizationConsolidationDirector.objects.filter(id=cibil['director_id']).update(cibilIndividual=cibil['cibil']) 
                individual_error=0
                
                if cibil['cibil']:
                    individual_error=cibil['cibil']
                #Individial Cibil check
                if float(individual_error) >= float(allowedIndividualCibil.value):
                    individual_flag=1
            
            #If Individial Cibil check -1

            if individual_flag>0:                
                cibilnumber=cibilnumber+1

            #If Business cibil check -2
            if businesscibil and float(businesscibil) <= float(allowedbusinessCibil.value):
                cibilnumber=cibilnumber+1

            #Dpd status   check-3
            if dpd_fail==0 and dpd_status>0:
                cibilnumber=cibilnumber+1

            #Dpd status   check-4
            if write_off_fail==0 and write_off_status>0:
                cibilnumber=cibilnumber+1


            
            pan_data_query.business_cibil_avg=businesscibil
            pan_data_query.cibil_fetch_date=datetime.datetime.now()
            pan_data_query.leadId=leadid
            pan_data_query.dpd_status=dpd_status
            pan_data_query.write_off_status=write_off_status
            pan_data_query.go_no_go_case_passed=cibilnumber+1
            pan_data_query.save()

            status_arya="G"
            leadstatus="NA"
            if cibilnumber==4:
                status_arya="G" 
                leadstatus="Green"
            elif cibilnumber ==3:
                status_arya="A" 
                leadstatus="Amber"
            else:
                status_arya="R" 
                status_arya="Red" 




                          
            #reject lead
            result['indcibil']=indcibil
            result['businesscibil']=businesscibil
            result['cibilallowed']=cibilallowed
            result['aryashakti_status']=status_arya
            result['leadId']=leadid

            bd_email=""

            bd_email=request.user.organization.relationship_manager_name
            if(not bd_email or bd_email==""):
                bd_value=Setting.objects.getKey('DEFAULT_BD')
                bd_email=bd_value.value

            

            message= "Borrower Name- "+pan_data_query.pan_name+" \nLeadId- "+str(leadid)+"\nVerdict- "+leadstatus
            send_mail(
                "AryaMitra new Lead",
                message,
                settings.EMAIL_FROM,
                [bd_email],
                fail_silently=False,
            )

            

            return res.req_response(result_data['message'],True,"",status.HTTP_200_OK,result)
        

        return res.req_response(result_data['message'],False,"VA-CLLGET-01",status.HTTP_400_BAD_REQUEST)

        
        
        

def getDirectorPanverificationView(request,cibil,message):
    user_id=request.GET.get('user_id')
    try:
        panData= models.PanVerifcation.objects.get_user_pan(user_id=user_id)
        directors= panData.directors.all()
    except models.PanVerifcation.DoesNotExist:
        panData=None
        directors=[]

    return render(
        request,
        'director_verify.html',
        {
            'pan_data':panData,
            'token':request.GET.get('token'),
            'directors':directors,
            'user_id':user_id,
            'cibil':cibil,
            'message':message,
        }
    )


class UploadBankStatement(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self,request):
        try:
            data=request.data
            if 'leadid' not in data.keys():
                return res.req_response("Lead not found",False,"VVUBS-POST-02",status.HTTP_400_BAD_REQUEST)

            bank_statement_path=""
            bank_statement_instance = get_bank_statements(request.user.id)  # You need to implement this method
            is_url=False
            if not bank_statement_instance:
                compliance_query=models2.compliance.objects.filter(user_id=request.user,document_name="bankStatement").last()
                if compliance_query:
                    is_url=True
                    bank_statement_path=compliance_query.file_url1
            else:
                bank_statement_path=bank_statement_instance[0]

            # Call the function to upload the bank statement to the third-party API
            if not bank_statement_path:                
                return res.req_response("Bank statement not found",False,"VVUBS-POST-02",status.HTTP_400_BAD_REQUEST)

            pan_data_query= models.PanVerifcation.objects.filter(user=request.user).last()
            pan_data_query.bank_uploaded=1
            pan_data_query.save()
            return res.req_response("File uploaded successfully",True,"",status.HTTP_200_OK,data=[])
            
        except Exception as e:            
            return res.req_response(constants.ERROR+" "+str(e),False,"VVUBS-POST-01",status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def upload_bank_statement(self,request, file_path,leadid,is_url):
        # try:
            # Initialize your third-party integration class
            arya_profin = AryaProfin(request)

            # Call the AryaProfin method to upload the bank statement
            result = arya_profin.upload_bank_statement(file_path,leadid,is_url)

            
            return result
        # except Exception as e:
        #     # Handle exceptions, e.g., file not found or API request failed
        #     return {'status': 'error', 'message': str(e)}

class ViewForDirectorCibil(APIView):
    def get(self,request): 
        return getDirectorPanverificationView(request,1,"Director Details submitted!")
        



class ViewForDirectorVerification(APIView):
    def get(self,request):        
        return getDirectorPanverificationView(request,0,"Message sent for adhar verification!")
        
    

    def post(self,request):
        formdata=json.loads(request.data) if type(request.data) == str else request.data
        user_id=formdata['user_id']
        print(user_id)
        try:
            panData= models.PanVerifcation.objects.get_user_pan(user_id=user_id)            
        except models.PanVerifcation.DoesNotExist:
            panData=None

        try:
            user_data= models2.user.objects.get_user_by_id(user_id)
        except models2.user.DoesNotExist:
            user_data=None
        

        mobile_numbers= formdata['mobile_number']
        directors_pan= formdata['director_pan']
        pan_data= formdata['pan_data']
        pincode= formdata['pincode']
        ids= formdata['ids']
        if not ids: 
            ids_count=0
        else:
            ids_count= len(ids)
        if(len(directors_pan)<1):
            result=res.ErrRes()
            result['message']="No pan found."
            result['error_code']="VV-VFDV-01"
            return Response(result,status=result['status_code'])
        
        for i,m in enumerate(directors_pan):
            addr=helper.get_address_from_pincode(pincode[i])          
            if i<ids_count:
                fatherName=dob=None                
                if(addr['flag']):
                    result=res.ErrRes()
                    result['message']="Address not found."
                    result['error_code']="VV-VFDV-02"
                    return Response(result,status=result['status_code'])
        
                if 'fatherName' in pan_data[i]['response']['result'].keys():
                    fatherName=pan_data[i]['response']['result']['fatherName']
                    if pan_data[i]['response']['result']['dob'] != "":
                        dob=pan_data[i]['response']['result']['dob']
                data= models.OrganizationConsolidationDirector.objects.filter(id=ids[i]).update(
                    pan=panData,
                    user=user_data,
                    father_name=fatherName,
                    director=pan_data[i]['response']['result']['name'],
                    director_state=addr['state'],
                    mobile_number=mobile_numbers[i], 
                    director_pan=m,
                    pincode=pincode[i],                 
                    email="",                 
                    dob=dob,                 
                    address=addr['village']+", "+addr['taluka']+", "+addr['district']+", "+addr['state'],                 
                )
                
            else:
                fatherName=dob=None
                if 'fatherName' in pan_data[i]['response']['result'].keys():
                    fatherName=pan_data[i]['response']['result']['fatherName']
                    if pan_data[i]['response']['result']['dob'] != "":
                        dob=pan_data[i]['response']['result']['dob']

                data=models.OrganizationConsolidationDirector.objects.create(
                pan=panData,
                director_pan=m,
                user=user_data,
                father_name=fatherName,
                director=pan_data[i]['response']['result']['name'],
                mobile_number=mobile_numbers[i],
                pincode=pincode[i],                 
                email="",                 
                dob=dob,                
                director_state=addr['state'],
                address=addr['village']+", "+addr['taluka']+", "+addr['district']+", "+addr['state'], 
                )
                
                data.save()
            
            panData.address=addr['village']+", "+addr['taluka']+", "+addr['district']+", "+addr['state']
            panData.pincode=pincode[0]
            panData.state=addr['state']
            panData.save()


            
        result=res.SuccRes()

        return Response(result,status=result['status_code'])
    
class GetPanVerificationDetails(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request):
        status_value=0
        leadid=None
        data= models.PanVerifcation.objects.filter(leadId__isnull=False,organization_id=request.user.organization.id).last()
        if data:
            status_value=1        
            isbank_uploaded= data.bank_uploaded
            if isbank_uploaded>0:
                status_value=2
        
        result=res.SuccRes()
        result['data']=status_value
        result['message']="Data found"
        result['leadid']=leadid
        return Response(result,status=result['status_code'])




class UploadAdharData(APIView):
    def post(self,request,type,userid,director,verified_by_id=None):
        data=request.data
        if(type=="director"):
            data_adhar=models.OrganizationConsolidationDirector.objects.filter(id=director)
            
            data_adhar=data_adhar.update(
                adhar_verification_response=data,
                is_adhar_verified=True,
                )
            user=data_adhar[0].user
        elif(type=="user"):
            user=models2.user.objects.get_user_by_id(user_id=userid)
            data_adhar=models.AdharVerifcation.objects.update_or_create(
                 user=user,defaults={
                        "response_details":data
                    }
            )
            if data['status'] == 'success':
                name=data['aadharDetail']['name']
                
                if name.lower()!=user.full_name.lower():
                    msg = "Adhar name "+name+" didn't match with entered name- "+user.full_name
                    addVerification(user,settings.SIGNZY_ADHAR_DOC_ID,data_adhar[0].id,"verification_adharuser_request",3,verified_by_id,msg)#verification status - 3 is rejected

                    result=res.SuccRes()
                    return Response(result,status=result['status_code'])

        # count=models.OrganizationConsolidationDirector.objects.get_not_verified_director_count(user)
        # verification_status =2
        # if count==0:
        verification_status=1
        
        addVerification(user,settings.SIGNZY_ADHAR_DOC_ID,data_adhar[0].id,"verification_adharuser_request",verification_status,verified_by_id)
        
        # if(count==0):            
        #     updateDocumentStep(user)           
            
        result=res.SuccRes()
        return Response(result,status=result['status_code'])

class VerifyAdharCompleted(APIView):
    def get(self,request):
        return HttpResponse("You adhar is verified successfully")
    


class EsignCompleted(APIView):
    def get(self,request):
        return HttpResponse("You adhar esign completed")


class DeleteDirector(APIView):
    def post(self,request):
        idvalue=request.POST.get('id')
        models.OrganizationConsolidationDirector.objects.filter(pk=idvalue).delete()
        return Response({"success":True},status=200)

class GetTemplate(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request):
        data= models.TemplateData.objects.all()
        if request.user.organization:
            data=serializers.TemplateDataSerializer(data,many=True,context={"org":request.user.organization.id})
            if data:
                data= data.data
            result=res.SuccRes()
            result['data']=data
            return Response(result,status=result['status_code'])
        
        result=res.ErrRes()
        result['status_code']=status.HTTP_400_BAD_REQUEST
        result['message']="Organization not found"
        result['error_code']="VV-GT-01"
        return Response(result,status=result['status_code'])


class DownloadDoc(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self,request,docid):
        try:
            template= models.TemplateData.objects.filter(id=docid).get()
        except models.TemplateData.DoesNotExist:
            template=None
        if not template:
            result= res.ErrRes()
            result['status_code']=status.HTTP_404_NOT_FOUND
            return Response(result,status=result['status_code'])
        
        data=template.template_template_key.all()
        text=template.body
        if request.user.organization:
            try:
                key_data=models.OrganizationKeyValues.objects.filter(organization_id=request.user.organization.id).get()
            except models.OrganizationKeyValues.DoesNotExist:
                key_data=None
            if key_data:
                serialized=serializers.OrganizationKeyDataSerializer(key_data)
                if(serialized):
                    key_value=serialized.data

                    for c,i in enumerate(data):
                        key_value_data=""
                        if i.key in key_value.keys():
                            key_value_data= key_value[i.key]
                            if key_value_data:
                                text=text.replace("{{"+i.key+"}}",key_value_data)
    
        result=res.SuccRes()
        result['data']=text
        return Response(result,status=result['status_code'])


class DownloadAllDoc(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self,request):
        type_value= request.GET.get('type')
        if not type_value:
            result=res.ErrRes()
            result['status_code']=status.HTTP_400_BAD_REQUEST            
            result['error_code']="VV-DAP-01"           
            result['message']="Type not found"           
            return Response(result)
        if type_value=="other":
            try:
                template= models.TemplateData.objects.filter(~Q(type="pre_sanction"),~Q(type="post_sanction")).order_by('-id').all()
            except models.TemplateData.DoesNotExist:
                template=None
        else:
            try:
                template= models.TemplateData.objects.filter(type=type_value).order_by('-id').all()
            except models.TemplateData.DoesNotExist:
                template=None

        
        if not template:
            result= res.ErrRes()
            result['status_code']=status.HTTP_404_NOT_FOUND
            result['error_code']="VV-DAP-02"    
            result['message']="Template not found"          
            return Response(result,status=result['status_code'])

        text="<style>   .page-data{page-break-before: always;}</style>"
        count=0
        try:
            key_data=models.OrganizationKeyValues.objects.filter(organization_id=request.user.organization.id).get()
        except models.OrganizationKeyValues.DoesNotExist:
            key_data=None

        organization_user=request.user.organization

        for i in template:
            if count==0:                
                count=count+1
            else:
                text=text+"<div class='page-data'>"
            
            data=i.template_template_key.all()
            text=text+i.body
            text=text+" </div><div class='page-data'></div>"

            if organization_user:                
                if key_data:
                    serialized=serializers.OrganizationKeyDataSerializer(key_data)
                    if(serialized):
                        key_value=serialized.data

                        for c,i in enumerate(data):
                            key_value_data=""
                            if i.key in key_value.keys():
                                key_value_data= key_value[i.key]
                                if key_value_data:
                                    text=text.replace("{{"+i.key+"}}",key_value_data)
        
        result=res.SuccRes()
        result['data']=text
        return Response(result,status=result['status_code'])


class UploadDocForTemplate(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self,request,docid):
        try:
            template= models.TemplateData.objects.filter(id=docid).get()
        except models.TemplateData.DoesNotExist:
            template=None
        if not template:
            result= res.ErrRes()
            result['status_code']=status.HTTP_404_NOT_FOUND
            return Response(result,status=result['status_code'])
        

        file= request.FILES.get('file')
        if(file):
            file_url=helper.image_upload(file)
            organization= request.user.organization
            if file_url and organization:
                # if organization:
                data=models.OrganizationTemplate.objects.update_or_create(
                    organization=organization,
                    template=template,
                    defaults={"file_url":file_url}
                )

                result=res.SuccRes()
                result['status_code']=status.HTTP_201_CREATED
                return Response(result,status=result['status_code'])
        
        result=res.ErrRes()
        result['status_code']=status.HTTP_400_BAD_REQUEST
        result['message']="Could not upload the file"
        result['error_code']="VV-UFT-01"
        return Response(result,status=result['status_code'])


class GenerateDoc(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self,request): 
        if request.user.organization:       
            message= "Dear team,\n\n"+request.user.organization.org_name+" is requesting for generating Document. Please fill the data here - "+request.build_absolute_uri("/admin/verification/organizationkeyvalues/")
            send_mail(
                "Request for document generate - "+request.user.organization.org_name,
                message,
                settings.EMAIL_FROM,
                settings.EMAIL_TO,
                fail_silently=False,
            )
            result=res.SuccRes()
            return Response(result,status=result['status_code'])

        result=res.ErrRes()
        result['status_code']=status.HTTP_400_BAD_REQUEST
        result['message']="Organization not found."
        return Response(result,status=result['status_code'])



class CheckIfDataCreated(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self,request):
        key_data=0
        if request.user.organization:
            try:                
                key_data=models.OrganizationKeyValues.objects.filter(organization_id=request.user.organization.id).last()
                if key_data and key_data.is_completed:
                    key_data=2
                else:
                    key_data=1
            except models.OrganizationKeyValues.DoesNotExist:
                key_data=0
        result=res.SuccRes()
        
        result['data']=key_data
        return Response(result,status=result['status_code'])

        

class GetConsolidateData(APIView):
    def get(self,request):
        try:
            try:
                panData= models.PanVerifcation.objects.get(user=request.user)
            except models.PanVerifcation.DoesNotExist:
                panData=None
            signzy= SignZyAuthClass()
            if(panData ):
                print(panData)
                result=res.SuccRes()
                if( not panData.cin_number):
                    
                    response= signzy.getCinValue(panData.pan_name)
                    result=res.SuccRes()
                    result['data']=response
                    if 'error'in response.keys():
                        result = res.ErrRes()
                        result['message'] =response['error']['message']
                        result['status_code'] =response['error']['statusCode']
                        result['error_code'] ="VVGCD-01"
                        return Response(result,status=result['status_code'])
                    
                    
                    if(len(response['result']['companiesList'])>0):
                        cin=response['result']['companiesList'][0]['companyID']
                        panData.cin_number=cin
                        panData.save()
                        result['data']={'cin':cin}
                   
                 

                #Call consolidate API here. 

                consolidated=signzy.getConsolidated(panData.cin_number,request,panData.id)


                if 'error'in consolidated.keys():
                    result = res.ErrRes()
                    result['message'] =consolidated['error']['message']
                    result['status_code'] =consolidated['error']['statusCode']
                    result['error_code'] ="VVGCD-02"
                    return Response(result,status=result['status_code'])
                

                panData.response_consolidate=consolidated
                panData.save()
                if 'requestId' in consolidated['result'].keys():
                    panData.consolidate_requestId=consolidated['result']['requestId']
                    panData.save()
                if 'companyData' in consolidated['result'].keys():                
                    address=consolidated['result']['companyData']['registeredAddress']['addressLine1']
                    pincode=consolidated['result']['companyData']['registeredAddress']['pincode']
                    email=consolidated['result']['companyData']['email']
                    state=consolidated['result']['companyData']['registeredAddress']['state']
                    panData.address=address
                    panData.pincode=pincode
                    panData.state=state
                    panData.email=email
                    
                    panData.save()
                    for x in consolidated['result']['companyData']['authorizedSignatories']:

                        if x['designation']=='DIRECTOR':
                            models.OrganizationConsolidationDirector.objects.update_or_create(
                                user=request.user,
                                pan=panData,
                                director=x['name'],
                                defaults={
                                    "director_pan":x['pan'],
                                    "dob":datetime.datetime.strptime(x['dateOfBirth'], '%d/%m/%Y').strftime('%Y-%m-%d'),
                                    "pincode":pincode,
                                    "address":address,
                                    "email":email,
                                    "director_state":state,
                                }
                            )
                           
                    
                
                serialized= serializers.PanSerializer(panData)
                if(serialized):
                    result=res.SuccRes()
                    result['data']=serialized.data

                    return Response(result,status=result['status_code'])
            

            result = res.ErrRes()
            result['message'] = "Pan not found."
            result['error_code'] = "VVGCD-02"
            result['status_code'] = status.HTTP_404_NOT_FOUND
            return Response(result, status=result['status_code'])

        except Exception as e:
            result = res.ErrRes()
            result['status_code'] = status.HTTP_500_INTERNAL_SERVER_ERROR
            result['message'] = constants.ERROR+" "+str(e)
            result['error_code'] = "VVGCD-03"
            return Response(result, status=result['status_code'])


class AdharSendOTP(APIView): 
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self,request):
        data=request.data
        validation = validator.AdharOTPVerification(data=data)
        if not validation.is_valid():           
            return res.req_response(constants.INVALID_BODY,False,"VV-ASO-POST-01",status.HTTP_400_BAD_REQUEST)
        
        signzy= SignZyAuthClass()
        response= signzy.adhar_otp_send(data['adhar_number'])

        
        return res.req_response("OTP API",True,"",status.HTTP_200_OK,response)
    

class AdharOTPVerify(APIView): 
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request,user_id=False):
        
        data=request.data
        validation = validator.AdharOTPValidationVerification(data=data)
        if not validation.is_valid():           
            return res.req_response(constants.INVALID_BODY,False,"VV-AOV-POST-01",status.HTTP_400_BAD_REQUEST)
        
        signzy= SignZyAuthClass()
        response= signzy.adhar_otp_verify(data)

        if not user_id:
            user_id=request.user.id

        try:
            user= models2.user.objects.filter(id=user_id).get()
        except models2.user.DoesNotExist:
            return res.req_response("User not Found",False,"VV-AOV-POST-03",status.HTTP_404_NOT_FOUND,response)

        if 'data' in response.keys() and response['statusCode']==200  :
            name= response['data']['full_name']

            data_adhar=models.AdharVerifcation.objects.update_or_create(
                    user=user,defaults={
                        "response_details":response
                    }
                   
                )
            if name and name.lower()!=user.full_name.lower():
                msg = "Adhar name "+name+" didn't match with entered name- "+user.full_name
                addVerification(user,settings.SIGNZY_ADHAR_DOC_ID,data_adhar[0].id,"verification_adharuser_request",3,request.user.id,msg)#verification status - 3 is rejected
                return res.req_response(msg,False,"",status.HTTP_400_BAD_REQUEST,response)

            verification_status=1        
            addVerification(user,settings.SIGNZY_ADHAR_DOC_ID,data_adhar[0].id,"verification_adharuser_request",verification_status,request.user.id)
            return res.req_response("OTP API",True,"",status.HTTP_200_OK,response)

        error_message= "OTP API Failed"

        if 'error' in response.keys():
            error_message=response['error']['message']
        return res.req_response(error_message,False,"VV-AOV-POST-02",status.HTTP_400_BAD_REQUEST,response)



from libraries.internal_aadhar import ExtractAPIClient


class AdharVerificationByImageSingle(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        front_aadhaar = request.FILES.get('front_aadhaar')
        back_aadhaar = request.FILES.get('back_aadhaar')

        if not front_aadhaar or not back_aadhaar:
            return res.req_response("Both front and back required", False, "VV-AOV-POST-01", 400, {})

        client = ExtractAPIClient()
        aadhaar_data = client.extract_from_file_objects(front_aadhaar, back_aadhaar)

        if not aadhaar_data or 'success' not in aadhaar_data or not aadhaar_data['success']:
            return res.req_response("Something is wrong with generating url", False, "VV-AOV-POST-04", 400, {})

        return res.req_response("Aadhaar data extracted successfully", True, "VV-AOV-POST-00", 200, aadhaar_data['data'])

        # except Exception as e:
        #     return res.req_response(
        #         f"Error processing Aadhaar: {str(e)}",
        #         False,
        #         "VV-AOV-POST-99",
        #         status.HTTP_500_INTERNAL_SERVER_ERROR,
        #         {}
        #     )


    # def post(self,request,user_id=False):
    #     front_aadhar = request.FILES['front_aadhaar']
    #     back_aadhaar = request.FILES['back_aadhaar']
    #     if not front_aadhar  and not back_aadhaar :           
    #         return res.req_response(constants.INVALID_BODY,False,"VV-AOV-POST-01",status.HTTP_400_BAD_REQUEST)
        
    #     front_img = private_image_upload(front_aadhar,"documents/adhar/insurance/"+str(request.user.mobile_number)+"")
    #     back_img = private_image_upload(back_aadhaar,"documents/adhar/insurance/"+str(request.user.mobile_number)+"")
    #     adhar_imgs= generate_multiple_signed_urls([front_img,back_img])
    #     if (front_img not in adhar_imgs.keys() and back_img not in adhar_imgs.keys()) or (adhar_imgs[front_img]==None and adhar_imgs[back_img]==None) :
    #         return res.req_response("Something is wrong with generating url",False,"VV-AOV-POST-04",status.HTTP_400_BAD_REQUEST)

    #     # signzy = SignZyAuthClass()
    #     # aadhaar_data = signzy.adhar_verification([adhar_imgs[front_img], adhar_imgs[back_img]])
    #     # if aadhaar_data:
    #     #     aadhaar_data['front_adhar']=front_img
    #     #     aadhaar_data['back_adhar']=back_img

    #     atms = AtMS()
    #     aadhaar_data=atms.fetch_signzy_details_by_img(adhar_imgs[front_img],adhar_imgs[back_img],None)
    #     if 'success' in aadhaar_data.keys() and aadhaar_data["success"]:
    #         aadhaar_data=aadhaar_data['payload']['aadharDetailsFromImage']['result']
    #         aadhaar_data['front_adhar']=front_img
    #         aadhaar_data['back_adhar']=back_img
    #         return res.req_response("OTP API",True,"",status.HTTP_200_OK,aadhaar_data)
    #     print(aadhaar_data)
    #     return res.req_response("Something is wrong with generating url",False,"VV-AOV-POST-04",status.HTTP_400_BAD_REQUEST,aadhaar_data)

class SignzyInitiateContractAPIView(APIView):

    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data=request.data
        ref_id=data.get('ref_id')
        base64_str=helper.generate_pdf_base64_from_json(
            data.get('data')
        )
        try:
            payload = {
                "pdf":base64_str,
                "successRedirectUrl":helper.replaceHttp(request.build_absolute_uri(reverse('esignSuccess',args=[ref_id]))),
                "failureRedirectUrl":helper.replaceHttp(request.build_absolute_uri(reverse('esignFailed',args=[ref_id]))),
                "signerdetail": [{
                    "signerName": data.get('signerName'),
                    "signerGender": data.get('signerGender'),
                    "signatureType": "AADHAARESIGN-OTP",
                    "uidLastFourDigits": "",
                    "signerYearOfBirth": "",
                    "signatures": [
                        {
                            "pageNo": [
                                "All"
                            ],
                            "signaturePosition": [
                                "BottomLeft"
                            ]
                        }
                    ]
                }],
                "callbackUrl":helper.replaceHttp(request.build_absolute_uri(reverse('esignverifycallback'))),
                
            }
            signzy = SignZyAuthClass()
            result = signzy.initiate_contract(payload)
            return Response({
                "message": "Contract initiated successfully",
                "status": True,
                "data": result
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "message": "Contract initiation failed",
                "status": False,
                "error": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)        



from libraries.prakshepdb import mask_aadhaar_file
from django.core.files.base import ContentFile


class AdharVerificationByImage(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self,request,user_id=False):
        data= request.data
        validation = validator.AdharImageValidationVerification(data=data)
        if not validation.is_valid():           
            return res.req_response(constants.INVALID_BODY,False,"VV-AOV-POST-01",status.HTTP_400_BAD_REQUEST)
        if not user_id:
            user_id=request.user.id

        try:
            user= models2.user.objects.filter(id=user_id).get()
        except models2.user.DoesNotExist:
            return res.req_response("User not Found",False,"VV-AOV-POST-03",status.HTTP_404_NOT_FOUND)

        # ✅ Directly use validated files
        front_file = request.FILES["front_aadhaar"]
        back_file = request.FILES["back_aadhaar"]
        

        # ---- Step 1: Upload original files (temporarily) ----
        front_img = private_image_upload(front_file,"documents/adhar/"+str(user.mobile_number),overwrite=False)
        print(front_img)
        back_img = private_image_upload(back_file,"documents/adhar/"+str(user.mobile_number),overwrite=False)
        print(back_img)
        if not front_img or not back_img:
            return res.req_response("Something is wrong with file uploading ",False,"VV-AOV-POST-04",status.HTTP_400_BAD_REQUEST)
            

        adhar_imgs= generate_multiple_signed_urls([front_img,back_img])
        print(adhar_imgs)
        if front_img not in adhar_imgs.keys() and back_img not in adhar_imgs.keys():
            return res.req_response("Something is wrong with generating url",False,"VV-AOV-POST-04",status.HTTP_400_BAD_REQUEST)

        
        # ---- Step 2: Aadhaar verification with ORIGINALS ----
        signzy = SignZyAuthClass()
        aadhaar_data = signzy.adhar_verification([adhar_imgs[front_img], adhar_imgs[back_img]])


        # ---- Step 3: Mask Aadhaar files ----
        try:
            # Delete all unmasked files first
            front_bytes, _, front_name = mask_aadhaar_file(front_file)
            back_bytes, _, back_name = mask_aadhaar_file(back_file)

            # overwrite originals in GCS with masked versions
            masked_front=private_image_upload(ContentFile(front_bytes, name=front_name), f"documents/adhar/{user.mobile_number}")
            masked_back=private_image_upload(ContentFile(back_bytes, name=back_name), f"documents/adhar/{user.mobile_number}")
            print(masked_front)
            print(masked_back)
        except Exception as e:
            return res.req_response(
                "Something is wrong with generating url", False, "VV-AOV-POST-04", status.HTTP_400_BAD_REQUEST, None
            )
        delete_gcs_file(front_img)
        delete_gcs_file(back_img)
        # ---- Step 4: Continue verification logic ----
        # print("aadhaar_data", aadhaar_data)
        summary=None
        if aadhaar_data.get('response').get('result').get('validBackAndFront') == True:
            summary = aadhaar_data.get('response').get('result').get('summary')
            if summary.get('number') and summary.get('name') and summary.get('dob') and summary.get('gender') and summary.get('splitAddress'):
                name = summary['name']
                data_adhar=models.AdharVerifcation.objects.update_or_create(
                    user=user,defaults={
                        "response_details":summary
                    }
                   
                )
                if name and name.lower()!=user.full_name.lower():
                    msg = "Adhar name "+name+" didn't match with entered name- "+user.full_name
                    addVerification(user,settings.SIGNZY_ADHAR_DOC_ID,data_adhar[0].id,"verification_adharuser_request",3,request.user.id,msg)#verification status - 3 is rejected
                    return res.req_response("OTP API",True,"",status.HTTP_200_OK,summary)

            verification_status=1        
            addVerification(user,settings.SIGNZY_ADHAR_DOC_ID,data_adhar[0].id,"verification_adharuser_request",verification_status,request.user.id)
            
            return res.req_response("OTP API",True,"",status.HTTP_200_OK,summary)
        error_message= "Adhar verification Failed"

        return res.req_response(error_message,False,"VV-AOV-POST-02",status.HTTP_400_BAD_REQUEST,summary)

from celery.result import AsyncResult
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.utils import timezone
import csv
import io
import os
from pathlib import Path
from farm_category.models import CelreyTaskStatus
from libraries.celery_task import celery_test_task, update_farm_boundaries_from_geojson_csv

from libraries.pams import PAMSClient
class Test(APIView):

    def post(self, request):

        account_number = request.data.get("account_number")
        ifsc_code = request.data.get("ifsc_code")
        task_id = request.data.get("task_id")
        try:
            if task_id:
                task_status = CelreyTaskStatus.objects.filter(task_id=task_id).first()
                if task_status:
                    return Response(
                        {
                            "task_id": task_status.task_id,
                            "state": task_status.status,
                            "status": task_status.status,
                            "input_csv": task_status.input_csv,
                            "batch_size": task_status.batch_size,
                            "total_processed": task_status.total_processed,
                            "updated_count": task_status.updated_count,
                            "inserted_count": task_status.inserted_count,
                            "skipped_count": task_status.skipped_count,
                            "failed_count": task_status.failed_count,
                            "error_message": task_status.error_message,
                            "result": task_status.result_files,
                        },
                        status=status.HTTP_200_OK
                    )

                result = AsyncResult(task_id)
                return Response(
                    {
                        "success": True,
                        "response": response
                    },
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response(
                            {
                                "success": False,
                                "message": str(e)
                            },
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )

            
    