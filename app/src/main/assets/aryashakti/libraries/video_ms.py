import jwt
import uuid
import datetime
from django.shortcuts import get_object_or_404
from cms.models import Setting
from app_farm.utils.helper import postRequest
from django.conf import settings


class VideoMS:
    api_endpoint=settings.HUNDRED_MS_API_URL
    def __init__(self):
        self.app_access_key = settings.HUNDRED_MS_APP_ACCESS_KEY
        self.app_secret = settings.HUNDRED_MS_SECRET_KEY            
        self.management_token = self.get_or_generate_management_token()
        
    # def generate_token(self, room_id, user_id, role, expires=None):
    #     expires = expires or 24 * 3600
    #     now = datetime.datetime.utcnow()
    #     exp = now + datetime.timedelta(seconds=expires)
        
    #     return jwt.encode(payload={
    #         "access_key": self.app_access_key,
    #         "type": "app",
    #         "version": 2,
    #         "room_id": room_id,
    #         "user_id": user_id,
    #         "role": role,
    #         "jti": str(uuid.uuid4()),
    #         "exp": exp,
    #         "iat": now,
    #         "nbf": now,
    #     }, key=self.app_secret)

    def generateManagementToken(self):
        expires = 24 * 3600
        now = datetime.datetime.utcnow()
        exp = now + datetime.timedelta(seconds=expires)
        return jwt.encode(payload={
            'access_key': self.app_access_key,
            'type': 'management',
            'version': 2,
            'jti': str(uuid.uuid4()),
            'iat': now,
            'exp': exp,
            'nbf': now
            }, key=self.app_secret)

    def get_or_generate_management_token(self):
        try:
            setting = Setting.objects.get(key="management_token")
            if self.is_valid_token(setting.value, self.app_secret):
                return setting.value
        except Setting.DoesNotExist:
            pass

        # Generate a new token
        #new_token = self.generate_token(room_id="", user_id="", role="management", expires=3600)
        new_token = self.generateManagementToken()

        # Save the new token in the Setting model
        Setting.objects.update_or_create(key="management_token", defaults={"value":new_token} )

        return new_token

    @staticmethod
    def is_valid_token(token, secret_key):
        try:
            # Decode the token and verify the signature using the secret key
            decoded_token = jwt.decode(token, secret_key, algorithms=["HS256"])

            # Check the token's expiration
            current_time = datetime.datetime.utcnow()
            expiration_time = datetime.datetime.fromtimestamp(decoded_token["exp"])
            if current_time > expiration_time:
                return False

            # The token is valid
            return True

        except jwt.ExpiredSignatureError:
            # The token has expired
            return False

        except jwt.InvalidTokenError:
            # The token is invalid or has an invalid signature
            return False


    def createCode(self,roomid):
        if not self.is_valid_token(self.management_token, self.app_secret):
            # If not valid, generate a new one and save it in the Setting model
            self.management_token = self.get_or_generate_management_token()

        # Perform the API call to create the room using the management token
        # Implement your API call using the appropriate library or method
        # Example using requests library:
        
        headers={'Authorization': f'Bearer {self.management_token}', 'Content-Type': 'application/json'}
        url = self.api_endpoint+"room-codes/room/"+roomid   
        
        response=postRequest(url,{},headers)
  
        # Check the response and handle any errors

        # Return the response data or appropriate result
        return response.json()  # Example response handling

    def create_room(self, name, description):
        # Check if the management token is valid
        if not self.is_valid_token(self.management_token, self.app_secret):
            # If not valid, generate a new one and save it in the Setting model
            self.management_token = self.get_or_generate_management_token()

        # Perform the API call to create the room using the management token
        # Implement your API call using the appropriate library or method
        # Example using requests library:
        json={
                "name": name,
                "description": description,
                "template_id": "6568486bc75a69c5f8103699",
                #"region": "in",
            }
        headers={'Authorization': f'Bearer {self.management_token}', 'Content-Type': 'application/json'}
        url = self.api_endpoint+"rooms"   
        
        response=postRequest(url,json,headers)

        # Check the response and handle any errors

        # Return the response data or appropriate result
        return response.json()  # Example response handling
    


    def create_live_stream(self, room_id, meeting_url):
        url = f"{self.api_endpoint}live-streams/room/{room_id}/start"
        headers = {
            "Authorization": f"Bearer {self.management_token}",
            "Content-Type": "application/json",
        }
        json = {
            "meeting_url": meeting_url,
            "recording": {
                "hls_vod": True,
                "single_file_per_layer": True
            }
        }
        response = response=postRequest(url,json,headers)
        #requests.post(endpoint, headers=headers, json=data)

        # Process the API response and return the result
        # status_code = response.status_code
        # data = response.json() if response.ok else response.text
        return response.json()