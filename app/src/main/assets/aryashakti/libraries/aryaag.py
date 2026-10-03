from app_farm.utils.helper import getRequest
from django.conf import settings


class AryaAg:
    api_endpoint=""
    def __init__(self):
        self.api_endpoint=settings.ARYA_AG_URL
    
    def get_mandi_price(self,commodity_name,city_name):
        headers={'Content-Type': 'application/json'}
        url = self.api_endpoint+"get-mandi-price?city_name="+city_name+"&commodity_name="+commodity_name   
        
        print(url)
        response=getRequest(url,{},headers)
  
        # Check the response and handle any errors

        # Return the response data or appropriate result
        return response.json()  
