
from django.conf import settings

import requests
import os


class Castler:
    def __init__(self,auth_token=None):
        pass
        # self.base_url = settings.CASTLER_API_BASE_URL
        # self.api_key = settings.CASTLER_API_KEY
        # self.api_secret = settings.CASTLER_API_SECRET_KEY
        # self.x_api_key=settings.CASTLER_X_API_KEY
        # self.auth_token=auth_token

    

    # def general_headers(self):
    #     return {
    #         "Authorization":"Token "+self.auth_token,
    #         "x-api-key": self.x_api_key,
    #         "Content-Type": "application/json",
    #     }
    # def authenticate(self):
    #     url= self.base_url+"/auth/api-credential/token"
    #     data= {
    #             "apiKey": self.api_key,
    #             "apiSecret": self.api_secret
    #         }
    #     print(url)
    #     header={
    #             "Content-Type": "application/json",
    #             "x-api-key":self.x_api_key
    #         }
    #     response = requests.post(url, headers=header, json=data)
    #     return response.json()
    
    

    # def create_virtual_account(self,payload):
    #     url= self.base_url+"/account"
        
    #     print(url)
    #     header=self.general_headers()
    #     print(header)
    #     print(payload)
    #     response = requests.post(url, headers=header, json=payload)
    #     return response.json()

    # def create_payee(self):
    #     pass


    # def send_individual(self):
    #     pass

    # def send_in_bulk(self,account_id,total_amount,org_name,list_procure,payment_id,ref):
    #     url= self.base_url+"/multi-transfer"

    #     payload={
    #         "accountId": account_id,
    #         "totalAmount": total_amount,
    #         "batchName": "Payment for "+org_name,
    #         "customerRefId": ref+"-"+str(payment_id),
    #         "transferList": list_procure
    #     }
    #     print(url)
    #     header=self.general_headers()
    #     print(header)
    #     print(payload)
    #     response = requests.post(url, headers=header, json=payload)
    #     return response.json()

    # def get_account_details(self,account_id):
    #     url= self.base_url+"/account/"+str(account_id)

        
    #     header=self.general_headers()
    #     response = requests.get(url, headers=header)
    #     return response.json()

