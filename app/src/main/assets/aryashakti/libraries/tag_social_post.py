import requests
from django.conf import settings
import json

class TagSocialPost:

    def __init__(self) -> None:
        self.url=settings.SOCIAL_POST_TAG_API_URL

    def gettag(self,post_text):
        url= self.url+'classify/'
        headers = {
            'Content-Type': "application/json",
        }
        response = requests.post(url=url, json={"text":post_text}, headers=headers)
        return response.json()