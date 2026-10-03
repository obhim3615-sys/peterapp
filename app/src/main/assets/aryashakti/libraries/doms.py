import requests
from django.conf import settings
import json

class DomsSignedURL:
    base_url = ""

    def __init__(self):
        self.base_url = settings.DOMS_URL

    def get_headers(self):
        return {
            'x-api-client-id': settings.NOMS_API_CLIENT_ID,
            'x-tenant-id': settings.NOMS_TENANT_ID,
            'Content-Type': 'application/json',
            'x-span-id': '234',
            'x-trace-id': '32' ,
            'x-user-id': '23432',
        }

    def generate_signed_url(self, payload):
        url = f"{self.base_url}/docmanager/generatesignedurl"
        headers = self.get_headers()
        print(payload)
        payload={"metaInfo":None,"payload":payload}
        response = requests.post(url=url, data=json.dumps(payload), headers=headers)
        return response.json()

    def upload_file(self, upload_data):
        headers = {
            'Content-Type': "application/json",
            'x-goog-meta-originalFileName': upload_data["original_file_name"],
            'x-goog-content-length-range': '10,31457280',
        }
        response = requests.put(url=upload_data["signed_url"], data=upload_data["file_content"], headers=headers)
        return response
    
