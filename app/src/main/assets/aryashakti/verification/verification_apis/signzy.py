from verification.models import SignzyAuth
from app_farm.utils import helper
import json
from django.conf import settings
import datetime
from django.utils import timezone
from django.urls import reverse




class SignZyAuthClass:
    token=""
    base_url=""
    def __init__(self) -> None:
        self.base_url=settings.SIGNZY_BASE_URL
        self.adhar_verify_url=settings.SIGNZY_ADHAR_VERIFY_URL
        self.adhar_verify_token=settings.SIGNZY_ADHAR_VERIFY_TOKEN
        self.contract_base_url=settings.SIGNZY_CONTRACT_BASE_URL
    


    def initiate_contract(self,data):
        self.getToken()
        if self.token:
            print(self.token.auth_token)
            headers = {
                    'Content-Type': 'application/json',
                    "Accept-Language": "en-US,en;q=0.8",
                    "Accept": "*/*",
                    "Authorization": str(self.token.auth_token)
                }
            url= self.contract_base_url+"contract/initiate"
            response= helper.postRequest(url=url,
                                        data=data ,
                                        headers=headers
                                    ) 
            print(response.json())
            return response.json()
        return False


    def getToken(self): 
        # print("----------------------get token -----------------------")
        self.checkIfTokenExist()        
        return self.token
    
    def checkIfTokenExist(self):
        try:  
            token_value= SignzyAuth.objects.filter(id=1).get()
            # print("----------------------check if token exist----------------------")
            # print(token_value.patronid)
        except SignzyAuth.DoesNotExist:
            token_value=None
        if token_value:
            self.token=token_value
            if self.checkIfTokenExpired():
                self.generateToken("Expired Update")
        else:
            self.generateToken()
        

    def checkIfTokenExpired(self):
        if timezone.now() < self.token.expiry_date:
            # print("--------------NOT_Expired--------------")
            return False
        # print("--------------Expired--------------")        
        return True

    
    def patronsLogin(self):
        patronslogin= helper.postRequest(self.base_url+"patrons/login",
                           {
                            "username": settings.SIGNZY_USERNAME,
                            "password": settings.SIGNZY_PASSWORD
                            },
                            {
                            'Content-Type': 'application/json',
                            }
                        )
        return patronslogin
    
    def generateToken(self,create_reason=False):
        login= self.patronsLogin()
        # print("----------------------patrons Login---------------------")
        # print(login.content)
        if create_reason==False:
            create_reason="First creation"
        if(login):
            login=json.loads(login.text)
            today = datetime.datetime.now()        
            converted_time=str(today+datetime.timedelta(days=180))
            self.token= SignzyAuth.objects.update_or_create(
                id=1,defaults={
                    "auth_token":login['id'],
                    "patronid":login['userId'],
                    "ttl":login['ttl'],
                    "token_created_at":login['created'],
                    "expiry_date":converted_time,
                    "reason_creation":create_reason
                }
                
            )
            self.token=self.getToken()
    
    def identityApi(self,type_pan,images=[]):
        # print("type of pan: ",type_pan)
        payload= {
                "type": type_pan,
                "email": settings.SIGNZY_EMAIL,
                "images": images,
                "callbackUrl": settings.SIGNZY_CALLBACK_URL,
                
            }
        header={
            'Content-Type': 'application/json',
                "Authorization":str(self.token.auth_token)
            }
        url=self.base_url+"patrons/"+self.token.patronid+"/identities"
        response= helper.postRequest(url=url,
                                    data=payload ,
                                    headers=header
                                ) 
        # print('------------------------identity--------------------------')
        
        # print(url)
        # print(response)
        # print(response.request.body)
        return response

    def pan_verification(self,data,type_pan):
        self.getToken()
        if self.token:
            identity= self.identityApi(type_pan)
            if(identity):
                identity=json.loads(identity.text)
                url = self.base_url+"snoops"

                payload =  {
                        "service":"Identity",
                        "itemId":str(identity['id']),
                        "task":"fetch",
                        "accessToken":str(identity['accessToken']),
                        "essentials": {
                            "name": "Aryatech",
                            "number": str(data['pan_number']),
                            "fuzzy": "true"
                        }
                    }
                
                # print("------------------------pan verification -----------------")
                # print(payload)
            
                headers = {
                    'Content-Type': 'application/json',
                    "Accept-Language": "en-US,en;q=0.8",
                    "Accept": "*/*",
                    "Authorization": str(self.token.auth_token)
                }
                response = helper.postRequest(url,payload,headers)           
                return json.loads(response.text)
            else:
                print(json.loads(identity.text))
        else:
            return False
    

    def adhar_verification(self,images):
        self.getToken()
        if self.token:
            identity= self.identityApi("aadhaar",images)
            if(identity):
                identity=json.loads(identity.text)
                url = self.base_url+"snoops"

                payload =  {
                        "service":"Identity",
                        "itemId":str(identity['id']),
                        "task":"autoRecognition",
                        "accessToken":str(identity['accessToken']),
                        "essentials": {
                            "name": "Aryatech",                           
                            "fuzzy": "true"
                        }
                    }
                
                # print("------------------------adhar verification -----------------")
                # print(payload)
            
                headers = {
                    'Content-Type': 'application/json',
                    "Accept-Language": "en-US,en;q=0.8",
                    "Accept": "*/*",
                    "Authorization": str(self.token.auth_token)
                }
                response = helper.postRequest(url,payload,headers)
                print(response)           
                return json.loads(response.text)
            else:
                print(json.loads(identity.text))
        else:
            return False

    def adhar_otp_send(self,adhar_number):
        headers = {
                    'Content-Type': 'application/json',
                    "Accept-Language": "en-US,en;q=0.8",
                    "Accept": "*/*",
                    "Authorization": str(self.adhar_verify_token)
                }
        
        payload={
            "aadhaarNumber": adhar_number
        }

        url= self.adhar_verify_url+"getOkycOtp"

        print(headers)
        print(url)
        print(payload)
        
        response = helper.postRequest(url,payload,headers) 
        print(response.json())
        return json.loads(response.text)

    def adhar_otp_verify(self,obj):
        headers = {
                    'Content-Type': 'application/json',
                    "Accept-Language": "en-US,en;q=0.8",
                    "Accept": "*/*",
                    "Authorization": str(self.adhar_verify_token)
                }
        
        payload={
            "requestId": obj.get('request_id'),
            "otp": obj.get('otp')
        }

        url= self.adhar_verify_url+"fetchOkycData"
        response = helper.postRequest(url,payload,headers) 
        return json.loads(response.text)

    def createDigiLockerUrl(self,request,type,director,user,verified_by):
        self.getToken()
        url=self.base_url+'patrons/'+self.token.patronid+"/digilockers"
        payload={
            "task":"url",
            "essentials":{
                "callbackUrl":helper.replaceHttp(request.build_absolute_uri(reverse('verifyadhar',args=[type,user.id,director,verified_by.id]))),
                "redirectUrl":helper.replaceHttp(request.build_absolute_uri(reverse('verifyadharcompleted')))
            }
        }

        print(url)
        print(payload)
        
        headers = {
                'Content-Type': 'application/json',
                "Accept-Language": "en-US,en;q=0.8",
                "Accept": "*/*",
                "Authorization": str(self.token.auth_token)
            }
        response = helper.postRequest(url,payload,headers) 
        print(response.json())
        return json.loads(response.text)
    
    def getEaadhar(self,req_id):
        self.getToken()
        url=self.base_url+'patrons/'+self.token.patronid+"/digilockers"
        payload={
                "task": "getEadhaar",
                "essentials": {
                    "requestId": str(req_id)
                }
            }
        headers = {
                'Content-Type': 'application/json',
                "Accept-Language": "en-US,en;q=0.8",
                "Accept": "*/*",
                "Authorization": str(self.token.auth_token)
            }
        response = helper.postRequest(url,payload,headers) 
        return response.text
    


    def getGSTValue(self,pan):
        self.getToken()
        url=self.base_url+'patrons/'+self.token.patronid+"/gstns"
        payload={
                "task": "panSearch",
                "essentials": {
                    "panNumber": str(pan)
                }
            }
        
        headers = {
                'Content-Type': 'application/json',
                "Accept-Language": "en-US,en;q=0.8",
                "Accept": "*/*",
                "Authorization": str(self.token.auth_token)
            }
        response = helper.postRequest(url,payload,headers) 
        return json.loads(response.text)
    


    def getCinValue(self,company_name):
        org= self.getOrganizationObject()
        url=self.base_url+'hunts'
        # print(org)
        # print(url)
        if 'error' in org.keys():
            return org
        payload={
                    "target": "Organization",
                    "itemId": org['id'],
                    "accessToken": org['accessToken'],
                    "task": "searchCompaniesByName",
                    "essentials": {
                        "name": company_name
                    }
                }

        headers = {
                'Content-Type': 'application/json',
                "Accept-Language": "en-US,en;q=0.8",
                "Accept": "*/*",
                "Authorization": str(self.token.auth_token)
            }
        
        # response={
        #             "target": "Organization",
        #             "itemId": "644627da2f07f62cc4181dd0",
        #             "accessToken": "mr9b1lrgxy0qf44fajrfytjqks5zyd9r",
        #             "task": "searchCompaniesByName",
        #             "id": "644627f42f07f62cc4181df6",
        #             "essentials": {
        #                 "name": "ARYATECH PLATFORMS PRIVATE LIMITED"
        #             },
        #             "result": {
        #                 "message": "Results found for the combination of inputs.",
        #                 "companiesList": [
        #                     {
        #                         "companyName": "ARYATECH PLATFORMS PRIVATE LIMITED",
        #                         "companyID": "U01100UP2021PTC140909"
        #                     }
        #                 ]
        #             }
        #         }
        
        # return response

        response = helper.postRequest(url,payload,headers) 
        return json.loads(response.text)
    

    
    def getOrganizationObject(self):
        self.getToken()
        url=self.base_url+'patrons/'+self.token.patronid+"/organizations"
        # print(self.base_url+'patrons/'+self.token.patronid+"/organizations")
        payload={
                "identifier": "organizations",
                "service": "roc",
                "callbackUrl": settings.SIGNZY_CALLBACK_URL,
                }

        headers = {
                'Content-Type': 'application/json',
                "Accept-Language": "en-US,en;q=0.8",
                "Accept": "*/*",
                "Authorization": str(self.token.auth_token)
            }
        
        # response={
        #     "callbackUrl": "https://arya.ag/",
        #     "accessToken": "mr9b1lrgxy0qf44fajrfytjqks5zyd9r",
        #     "id": "644627da2f07f62cc4181dd0",
        #     "patronId": "63f85a64b0d947b5e55f57d9",
        #     "identifier": "organizations",
        #     "service": "roc"
        # }
        

        response = helper.postRequest(url,payload,headers) 
        return json.loads(response.text)
    

    def getConsolidated(self,cin,request,panid):
        self.getToken()
        url=self.base_url+'patrons/'+self.token.patronid+"/companyconsolidated"
        payload={
                    "task": "fetchRealtime",
                    "essentials": {
                        "cin": cin,
                       
                    }
                }

        headers = {
                'Content-Type': 'application/json',
                "Accept-Language": "en-US,en;q=0.8",
                "Accept": "*/*",
                "Authorization": str(self.token.auth_token)
            }
        response = helper.postRequest(url,payload,headers)         
       
        return json.loads(response.text)
    
  