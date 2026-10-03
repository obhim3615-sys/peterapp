import requests
import json
from django.conf import settings
from app_farm.utils.helper import postRequest
import os
import mimetypes


class AryaProfin:
    def __init__(self,request ):
        self.base_url = settings.ARYA_PROFIN_URL
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': str(request.META.get('HTTP_AUTHORIZATION'))
        }

        self.headersformdata = {
            'Authorization': str(request.META.get('HTTP_AUTHORIZATION'))
        }


    def create_lead(self, data):
        url = self.base_url + "createlead"
        response = postRequest(url, data,self.headers)  
        result_data = json.loads(response.text)
        return result_data

    def reject_lead(self,data):
        url = self.base_url + "rejectlead"
        response = postRequest(url, data,self.headers)
        result_data = json.loads(response.text)
        return result_data    

    def upload_bank_statement(self, file_path, leadid, is_url):
        url = self.base_url + "uploadbankstatement"

        # try:
        # Prepare data for the request
        data = {'leadid': leadid}

        if is_url:
            # It's a URL, fetch the content
            response = requests.get(file_path)
            files = {'bank_stm': (os.path.basename(file_path), response.content)}
            headers = self.headersformdata  # Use JSON headers for URL
        else:
            # It's a local file, open and read it
            file_path = os.path.abspath(file_path)
            mime_type, _ = mimetypes.guess_type(file_path)
            filename = os.path.basename(file_path)
            files = {'bank_stm': (filename, open(file_path, 'rb'), mime_type)}
            headers = self.headersformdata  # Use formdata headers for local file

        # Make the API request with the proper headers
        response = requests.post(url, data=data, files=files, headers=headers)

        # Parse the response
        result_data = response.json()

        return result_data

        # except Exception as e:
        #     # Handle exceptions, e.g., file not found or API request failed
        #     return {'status': False, 'message': str(e)}
