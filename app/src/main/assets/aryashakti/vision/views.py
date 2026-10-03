from rest_framework import generics
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status
from . import models
from django.db.models import Sum,Prefetch
from django.db.models import Subquery
from decimal import Decimal
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
#from urllib import unquote
#from .models import User
from . import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from datetime import timedelta
from rest_framework import status
from django.shortcuts import get_object_or_404
from urllib.parse import unquote
#from rest_framework_api_key.permissions import HasAPIKey
import json
import re
import urllib.request
import ast
import ssl
from django.http import JsonResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from django.core.files.storage import default_storage
import basehash
#from Crypto.Cipher import AES
import base64
import hashlib
from decimal import Decimal
import datetime
from itertools import chain
import os
#from azure.storage.blob import BlobServiceClient, BlobClient,ContainerClient
from rest_framework.viewsets import ViewSet
import requests
import json
import re
from pdf2image import convert_from_path
from django.conf import settings as django_settings

class Khaitoni(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def post(self, request):
        #try:
        image = request.data["image"]


        file_name = default_storage.save(image.name, image)

            # Receiving File
        file = default_storage.open(file_name)
        file_url = default_storage.path(file_name)
        if file_name.endswith('.pdf'):
            images = convert_from_path(file_url,  350,fmt='jpeg')
            fname = os.path.join(django_settings.STATIC_ROOT,'image0.png')
            images[0].save(fname, "png")
            #z=images[0].tobytes()
            with open(fname, "rb") as imageFile:
                str1 = base64.b64encode(imageFile.read())
                str2 = str1.decode("utf-8")
        else:
            # opening and decoding the file
            with open(file_url, "rb") as imageFile:
                str1 = base64.b64encode(imageFile.read())
                str2 = str1.decode("utf-8")

            # Preparing String for Request to Google Vision API
        data1 = {
                "requests": [
                    {
                        "image": {
                            "content": str2
                        },
                        "features": [
                            {
                                "type": "DOCUMENT_TEXT_DETECTION"
                            }
                        ]
                    }
                ]
            }
            # Setting HTTP Headers
        headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

            # Sending Request to Google Vision API
        r = requests.post('https://vision.googleapis.com/v1/images:annotate?key=AIzaSyAjN1AEQJ76x0ue_4MGvwuCnMwJ5sszP7E', json=data1, headers=headers)

            # Handling the response of Vision API
        lst = []
        api_response = r.json()
        #api_response=r
            #print(api_response)
            #a
        aa = api_response['responses'][0]['textAnnotations']
        #aa = api_response['textAnnotations']
            #print(aa)

        details = []
        for i in aa:
            desc = i.get("description","")
            details.append(desc)

            #Fuction to classify english words or others
            #def isEnglish(s):
            #    try:
            #        s.encode(encoding='utf-8').decode('ascii')
            #    except UnicodeDecodeError:
            #        return False
            #    else:
            #        return True

            #Fuction definitionn to check substring is present ot not
            #def check(string, sub_str):
            #    if (string.find(sub_str) == -1):
            #         print("NO")
            #        return False
            #    else:
            #         print("YES")
            #        return True

            # print(details,'\n\n')
        details = details[0].split('\n')
            #Filtering only english words
        #details=[x for x in details if isEnglish(x)]

            #List to store dob and pan_number
        lst1 = []
            # Storing Pan_number details
        k=''
        count = 0
        for j in details:
            if j=='खतौनी.' or j=='खतौनी':
                #continue
                k=details[count+2]
                break

            if j=='खतौनीन.' or j=='खतौनी.न.':
                k=details[count+1]
                break

            count = count+1
        #pan_details = [x for x in details if x=='खतौनी.' or x=='खतौनी' ]

        url = "https://plots.prakshep.com/myplots/plotinfo_khasra/?khasra="+k+"&&secret_key=7f9a33a5-9c73-4eda-bbe9-d71b7fb842f4"

        payload={}
        headers = {}

        response1 = requests.request("GET", url, headers=headers, data=payload)

        print(response1.text)
        response = {'status': status.HTTP_200_OK, 'message': 'success', 'khasra number':k,'Plot details':response1.text }

    # Passing the object to serializer and generating response


        #except MultiValueDictKeyError as err:
        #    response = {'status': status.HTTP_400_BAD_REQUEST, 'message': str(err) +'missing', 'pan_number': 'invalid','name':'invalid','dob' :'invalid','father_name':'invalid' }
        #except KeyError as err:
        #    response = {'status': status.HTTP_400_BAD_REQUEST,'message': 'invalid image or image size should be smaller than 4 mb' , 'pan_number': 'invalid','name':'invalid','dob' :'invalid','father_name':'invalid' }
        #except RuntimeError as err:
        #    response = {'status': status.HTTP_500_INTERNAL_SERVER_ERROR, 'error_message': str(err),'pan_number': 'invalid','name':'invalid','dob' :'invalid','father_name':'invalid' }
        #except FileNotFoundError as err:
        #    response = {'status': status.HTTP_400_BAD_REQUEST, 'message': 'invalid file name', 'pan_number': 'invalid','name':'invalid','dob' :'invalid','father_name':'invalid' }
        #except IndexError as err:
        #    response = {'status': status.HTTP_400_BAD_REQUEST, 'message': 'wrong format', 'pan_number': 'invalid','name':'invalid','dob' :'invalid','father_name':'invalid' }
        return Response(response, status=response['status'])
