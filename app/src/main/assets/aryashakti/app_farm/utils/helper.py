import json
import requests
import re
import mimetypes
import uuid
from google.cloud import storage
from fuzzywuzzy import fuzz
from django.core.files.storage import default_storage
import basehash
from django.conf import settings
from app_farm.models import tb_application_access
from verification.models import Document,UserVerificationDocument,UserUnsecureLoan,UnsecureLoanStep
from app_farm.serializers import key_serializer
from app_farm.models import compliance
import csv
from . import constants
import time
from django.db.models import Q,F
import hashlib
import hmac
from django.http import HttpResponse
from subscription_service.models import UserService
from app_farm.models import user as userModel
import base64, math
from datetime import date
from libraries.push_notification import FirebaseHelper
from math import radians, sin, cos, sqrt, atan2
import os
from libraries.doms import DomsSignedURL
from datetime import datetime,timezone

from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from google.auth.transport.requests import Request
from google.auth import default
from google.api_core.exceptions import PreconditionFailed


from google.cloud import storage


hash_fn = basehash.base36()

# ***
# Constant common mapings
# ***
area_unit_dict = {
    'Acre': 'एकड़',
    "Hectare": "हैक्टर"
}
"""
English to Hindi mapping for area unit.

'Acre': 'एकड़',
"Hectare": "हैक्टर"
"""

kenya_address = {
    'pincode': 100,
    'village': 'Kenya',
    'taluka': 'Kenya',
    'district': 'Kenya',
    'state': 'Kenya',
    'country': 'Kenya',
}
"""
Hard-codded value for Kenya country address.
"""


# ***
# Constant common functions
# ***
def is_valid_pincode(pincode):
    """
    Function to check whether the pincode is valid or not.
    """
    # Regex to check valid pin code
    regex = "^[1-9]{1}[0-9]{2}\\s{0,1}[0-9]{3}$"
 
    # Compile the ReGex
    p = re.compile(regex)
     
    # If the pin code is empty
    # return false
    if pincode == None or pincode == '':
        return False
    m = re.match(p, pincode)
     
    # Return True if the pin code
    # matched the ReGex else False
    if m is None:
        return False
    else:
        return True

def get_current_iso8601_datetime():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'


def verify_otp(session_id, otp):
    """
    Send otp on the mobile number.
    """
    result = {
        'otp_verified': False,
        'error': None,
        'error_code': None
    }
    try:
        url = "https://2factor.in/API/V1/"+"02812b9f-c939-11e7-94da-0200cd936042"+"/SMS/VERIFY/"+session_id+"/"+otp
        response = requests.get(url)
        response = response.json()

        if response['Status'] == "Success" and response['Details'] == "OTP Matched":
            result['otp_verified'] = True
        else:
            result['error'] = response['Details']
            result['error_code'] = 'EESAF-01'

        return result
    except:
        result['error'] = 'Something went wrong during otp verification.'
        result['error_code'] = 'EESAF-02'
        return result
    
def send_sms(msg, phone):
    """
    Send sms on the mobile number.
    """
    url = "https://alerts.cbis.in/SMSApi/send"
    payload = {
        'userid': 'aryacma',
        'password': 'fqGnYXMS',
        'msg': msg,
        'type': 'text',
        'senderid': 'aryaMK',
        'test': 'true',
        'duplicatecheck': 'true',
        'format': 'json',
        'mobile': phone,
        'sendMethod': 'quick',
        'msgType': "text",
        'dltTemplateId': "1707167948516066799"
    }
    headers = {
        'apikey': 'sdfds',
        'Cookie': 'SERVERID=webC1'
    }
    files=[]
    return requests.request("POST", url, headers=headers, data=payload, files=files)
    
def verify_secret_key(key):
    """
    Function to verify the secret key.
    """
    try:
        qs = tb_application_access.objects.filter(key=key)
        serializer = key_serializer(qs, many=True)

        if len(serializer.data) != 0 :
            return True
        
        return False
    except Exception as e:
        return False
    
def get_address_from_pincode(postal_code):
    address_data = {
        'pincode': None,
        'village': None,
        'taluka': None,
        'district': None,
        'state': None,
        'country': None,
        'flag': False
    }
    url = 'https://api.postalpincode.in/pincode/' + postal_code
    response = requests.get(url)
    response = response.json()[0]

    if response['Status'] == 'Success' and len(response['PostOffice']) > 0:
        data = response['PostOffice'][0]
        return {
            'pincode': postal_code,
            'village': data['Name'],
            'taluka': data['Block'],
            'district': data['District'],
            'state': data['State'],
            'country': data['Country'],
            'flag': False
        }
    else:
        address_data['flag'] = True
        return address_data

def get_address_data(lat, long, is_location=False):
    """
    Function to get address data from lat and long.
    """
    address_data = {
        'pincode': None,
        'village': None,
        'taluka': None,
        'district': None,
        'state': None,
        'country': None,
        'flag': False
    }
    try:
        # if is_location:
        if lat and long:
            # Getting the pincode from lat and long
            url = "https://maps.googleapis.com/maps/api/geocode/json?latlng=" + str(lat) + ',' + str(long) + '&key='+settings.GOOGLE_GEO_API_KEY
            response = requests.get(url)
            response = response.json()

            if response['status'] == 'OK' and len(response.get('results')) > 0:
                results = response['results']
                postal_code = None

                for result in results:
                    if 'postal_code' in result['types']:
                        for address_component in result['address_components']:
                            if 'postal_code' in address_component['types'] and is_valid_pincode(address_component['long_name']):
                                postal_code = address_component['long_name']
                                break
                        break

                if postal_code:
                    # Getting other address data from pincode.
                    address_data = get_address_from_pincode(postal_code)
                else:
                    address_data['flag'] = True
            else:
                address_data['flag'] = True
        return address_data
        
    except:
        address_data['flag'] = True
        return address_data
    

def get_lat_long_from_pin(pincode):
    url = "https://maps.googleapis.com/maps/api/geocode/json?address=" + str(pincode) + '&key='+settings.GOOGLE_GEO_API_KEY
    response = requests.get(url)
    response = response.json()

    location = {
        'lat': 0.0,
        'lng': 0.0
    }
    if response['status'] == 'OK' and len(response.get('results')) > 0:
        results = response['results']

        for result in results:
            if 'postal_code' in result['types']:
                location = result['geometry']['location']
            
    return location

# def image_upload(file):
#     """
#     Upload a file and return its URL.
#     """
#     # Generate a unique filename for the file
#     name = "_".join(file.name.split())
#     # file_name = default_storage.save(name, file)
#     # file_url = default_storage.url(file_name)

#     # Get the content type of the file
#     content_type, _ = mimetypes.guess_type(name)
#     if not content_type:
#         content_type = 'application/octet-stream'

#     s3 = boto3.client('s3', aws_access_key_id=settings.AWS_ACCESS_KEY, aws_secret_access_key=settings.BUCKET_SECRET_KEY)
#     s3.upload_fileobj(file, settings.BUCKET_NAME, settings.BUCKET_PREFIX+'/X'+name, ExtraArgs={'ContentType': content_type, 'ACL': 'public-read'})
#     file_url = f"https://{settings.BUCKET_NAME}.s3.amazonaws.com/{settings.BUCKET_PREFIX}/X{name}"
#     return file_url



def temp_image_upload(file,filename,file_type):
    # Upload CSV file to DOMS
    doms_url_handler = DomsSignedURL()
    generate_url_payload = {
        'contentType': file_type,
        'originalFileName': filename
    }

    signed_url_response = doms_url_handler.generate_signed_url(generate_url_payload)
    # print(signed_url_response)
    if signed_url_response.get('success') :
        attachment_url= signed_url_response['payload']['downloadUrl']
        # print("----------------------------------- signed_url response is here--------------------")
        signed_url = signed_url_response['payload']['signedUrl']
        content_type = file_type
        original_file_name = filename
        
        upload_payload = {
            'signed_url': signed_url,
            'file_content': file,
            'content_type': content_type,
            'original_file_name': original_file_name
        }
        # print(upload_payload)
        upload_response = doms_url_handler.upload_file(upload_payload)
        # print(upload_response)
        if upload_response.status_code == 200:
            return attachment_url
    
    return False
        
                    
ALLOWED_UPLOAD_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv',
    '.json', '.geojson',
    '.mp4', '.mov', '.avi',
}
MAX_UPLOAD_SIZE = 25 * 1024 * 1024  # 25 MB


def validate_upload(file, allowed_extensions=None, max_size=None):
    """
    Validate an uploaded file's extension and size.
    Returns a safe UUID-based filename.
    Raises ValueError on validation failure.
    """
    if file is None:
        raise ValueError("No file provided")

    if allowed_extensions is None:
        allowed_extensions = ALLOWED_UPLOAD_EXTENSIONS
    if max_size is None:
        max_size = MAX_UPLOAD_SIZE

    ext = os.path.splitext(file.name)[1].lower() if file.name else ''
    if ext not in allowed_extensions:
        raise ValueError(f"File type '{ext}' is not allowed")

    if hasattr(file, 'size') and file.size is not None and file.size > max_size:
        raise ValueError(f"File size {file.size} exceeds maximum {max_size} bytes")

    safe_name = f"{uuid.uuid4().hex}{ext}"
    return safe_name


def image_upload(file):
    """
    Upload a file and return its URL.
    """
    # Validate and generate a safe filename
    safe_name = validate_upload(file)

    # Get the content type of the file
    content_type, _ = mimetypes.guess_type(safe_name)
    if not content_type:
        content_type = 'application/octet-stream'

    # Initialize a client and get the bucket
    client = storage.Client()
    bucket = client.bucket(os.getenv('GCS_BUCKET_NAME'))

    # Create a blob and upload the file
    blob = bucket.blob(os.getenv('GCS_PREFIX') + '/' + safe_name)
    blob.upload_from_file(file, content_type=content_type)

    # Construct the file URL
    file_url = blob.public_url

    return file_url


from datetime import timedelta
# def generate_multiple_signed_urls(file_paths, expiration_minutes=60):
#     """
#     Generate signed URLs for multiple private files.
#     """
#     print(file_paths)
#     client = storage.Client(project="vikshep-prod-service-project")
#     bucket = client.bucket(settings.GCS_PRIVATE_BUCKET_NAME)

#     signed_urls = {}

#     for file_path in file_paths:
#         blob = bucket.blob(file_path)
#         signed_urls[file_path] = blob.generate_signed_url(expiration=timedelta(minutes=expiration_minutes))

#     return signed_urls



def delete_gcs_folder(folder_path):
    """
    Delete all files inside a GCS folder.
    Example: delete_gcs_folder("documents/adhar/9876543210")
    """
    client = storage.Client(project="vikshep-prod-service-project")
    bucket = client.bucket(settings.GCS_PRIVATE_BUCKET_NAME)

    prefix = f"{settings.GCS_PRIVATE_PREFIX}/{folder_path}/"
    blobs = bucket.list_blobs(prefix=prefix)

    deleted_files = []
    for blob in blobs:
        deleted_files.append(blob.name)
        blob.delete()

    # print(f"Deleted files: {deleted_files}")
    return deleted_files

def delete_gcs_file(file_path):
    """
    Delete a single file from GCS.
    Example: delete_gcs_file("documents/adhar/9876543210/front.png")
    """
    client = storage.Client(project="vikshep-prod-service-project")
    bucket = client.bucket(settings.GCS_PRIVATE_BUCKET_NAME)

    blob = bucket.blob(f"{file_path}")
    # print("deleting begin")
    if blob.exists():
        blob.delete()
        # print(f"Deleted file: {blob.name}")
        return True
    else:
        # print(f"File not found: {blob.name}")
        return False


def get_service_account_info():
    """
    Retrieve the service account email and access token using Google's Application Default Credentials (ADC).

    This function initializes the Application Default Credentials (ADC) and ensures that the credentials have a valid
    access token. It then retrieves the access token and the service account email associated with the credentials.

    Returns:
        tuple: A tuple containing the service account email (str) and the access token (str).
    """
    # Initialize ADC and get the credentials
    credentials, project_id = default()

    # Ensure the credentials have a valid access token
    credentials.refresh(Request())

    # Retrieve the access token and service account email
    access_token = credentials.token
    service_account_email = credentials.service_account_email

    return service_account_email, access_token




def generate_multiple_signed_urls(file_paths, expiration_minutes=60):
    """
    Generate signed URLs for multiple private files using ADC info.
    """
    project_name  = "vikshep-prod-service-project"
    client = storage.Client(project=project_name)
    bucket = client.bucket(settings.GCS_PRIVATE_BUCKET_NAME)

    signed_urls = {}
    expiration = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)
    
    try:
        service_account_email, access_token = get_service_account_info()
    except Exception as e:
        print(f"Failed to get service account info: {e}")
        service_account_email, access_token = None, None

    for file_path in file_paths:
        blob = bucket.blob(file_path)
        try:
            signed_urls[file_path] = blob.generate_signed_url(
                expiration=expiration,
                service_account_email=service_account_email,
                access_token=access_token
            )
        except Exception as e:
            print(f"Error generating signed URL for {file_path}: {str(e)}")
            signed_urls[file_path] = None

    return signed_urls


def generate_signed_url(blob_path, project_name, expiration=3600):
    """
    Generate a signed URL for accessing a private GCS file.
    """
    client = storage.Client(project=project_name)
    bucket = client.bucket(settings.GCS_PRIVATE_BUCKET_NAME)
    blob = bucket.blob(blob_path)

    url = blob.generate_signed_url(expiration=expiration)
    return url

from google.cloud import storage
import os
import mimetypes



def private_image_upload(file, folder_name="general", overwrite=False):
    """
    Upload a file to a private GCS bucket and return its storage path.
    If overwrite=True, delete the existing object (if any) and re-upload.
    """

    # Validate and generate a safe filename
    safe_name = validate_upload(file)

    # Determine content type
    content_type, _ = mimetypes.guess_type(safe_name)
    if not content_type:
        content_type = "application/octet-stream"

    # Init GCS client and bucket
    client = storage.Client(project="vikshep-prod-service-project")
    bucket = client.bucket(settings.GCS_PRIVATE_BUCKET_NAME)

    # Path in GCS
    file_path = f"{settings.GCS_PRIVATE_PREFIX}/{folder_name}/{safe_name}"
    blob = bucket.blob(file_path)

    # Handle overwrite
    if blob.exists(client=client):
        
        print(f"File already exists (skipping upload): {file_path}")
        return file_path

    # Reset file pointer and upload
    file.seek(0)
    try:
       
        # precondition ensures safe creation only if not exists
        blob.upload_from_file(
            file,
            content_type=content_type,
            if_generation_match=0
        )
        print(f"File uploaded successfully to {file_path}")
    except Exception as e:
        print(f"Error during upload: {e}")
        return None

    return file_path

# def private_image_upload(file, folder_name="general"):
#     """
#     Upload a file to a private GCS bucket and return its storage path.
#     Uses a generation match precondition to ensure safe uploads.
#     """
#     # Generate a unique filename
#     name = "_".join(file.name.split())

#     # Determine the content type
#     content_type, _ = mimetypes.guess_type(name)
#     if not content_type:
#         content_type = "application/octet-stream"

#     # Initialize GCS client with the correct project
#     client = storage.Client(project="vikshep-prod-service-project")
#     bucket = client.bucket(settings.GCS_PRIVATE_BUCKET_NAME)

#     # Define file path inside the bucket
#     file_path = f"{settings.GCS_PRIVATE_PREFIX}/{folder_name}/X{name}"

#     # Upload file as a private object with generation match precondition
#     blob = bucket.blob(file_path)
#     if blob.exists(client=client):
#         print(f"File already exists: {file_path}")
#         return file_path
#     file.seek(0)

#     try:
#         generation_match_precondition = 0  # Ensures file is only created if it doesn’t exist
#         blob.upload_from_file(file, content_type=content_type, if_generation_match=generation_match_precondition)
#         print(f"File uploaded successfully to {file_path}")
#     except Exception as e:
#         print(f"Error during upload: {e}")
#         return None

#     # Return the storage path (to be saved in the model)
#     return file_path


def get_pagination_start_end(page_number, number_of_records):
    """
    Function to get start and end according to the page number.
    """
    if page_number == None or not page_number.isnumeric() or int(page_number) < 1:
        page_number=1
    page_number = int(page_number)
    start, end = 0, number_of_records

    if page_number != 1:
        start = page_number * number_of_records - number_of_records
        end = start + number_of_records
    
    return start, end, page_number

def translate_text(source, target, text):
    """
    Translates text into the target language.

    Target must be an ISO 639-1 language code.
    See https://g.co/cloud/translate/v2/translate-reference#supported_languages
    """
    url = "https://translation.googleapis.com/language/translate/v2?key="+settings.GOOGLE_TRANSLATE_API_KEY

    payload = json.dumps({
        "q": [text],
        "target": target,
        "source": source
    })

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'key='+settings.GOOGLE_TRANSLATE_API_KEY
    }

    # response = requests.request("POST", url, headers=headers, data=payload)

    # print(response)
    return text



def postRequest(url,data,headers):
    response = requests.post(url, data=json.dumps(data), headers=headers)   
    return response

def putRequest(url, data, headers, raw=False):
    try:
        if raw:
            response = requests.put(url, data=data, headers=headers)
        else:
            response = requests.put(url, json=data, headers=headers)
        
        # Print the details of the request and response
        # print(f"PUT Request URL: {url}")
        # print(f"Headers: {headers}")
        # if raw:
        #     print(f"Data (bytes): {len(data)} bytes")
        # else:
        #     print(f"Data (json): {data}")

        # print(f"Response Status Code: {response.status_code}")
        # print(f"Response Content: {response.content}")

        return response
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise

def getRequest(url,data,headers):
    response = requests.get(url=url,params=data,headers=headers)   
    return response

def is_bank_account_verified(user):
    return UserVerificationDocument.objects.filter(
        user=user,
        document_type_id=settings.BANK_ACCOUNT_DOCUMENT_ID,
        type="payment_bankaccountvalidation_request",
        status=1
    ).exists()

def addVerification(user,doc_type,doc_id,type,status=1,verified_by_id=None,msg=None,):
    obj = {
        "document_id":doc_id,
        "status":status,
    }
    if verified_by_id and verified_by_id!='0' :
        obj['verified_by_id'] = verified_by_id
    
    doc, created = UserVerificationDocument.objects.update_or_create(
        user=user,
        document_type_id=doc_type,
        type=type,
        defaults = {**obj}
    )
    if msg:
        send_firebase_notification(str(doc.verified_by.id) if doc.verified_by else str(doc.user.id), msg)

# Function to update firebase real time data.
def send_firebase_notification(user_id, msg):
    """
    Function to update firebase real time data.
    """
    firebase_helper = FirebaseHelper(use_adc=True)
    firebase_helper.update_firebase_database(str(user_id), msg)

def export_csv_from_dicts(data):
    result = {
        'data': None,
        'error_code': None,
        'message': None
    }
    try:
        file_path = 'media/bank_statements/'+str(int(time.time()*1000))+'.csv'
        myFile = open(file_path, 'w')
        writer = csv.writer(myFile)
        writer.writerow(data[0].keys())
        for obj in data:
            writer.writerow(obj.values())
        myFile.close()
        result['data'] = file_path
        return result
    except Exception as e:
        print(e)
        result['error_code'] = 'AFUH-ECFDIC-01'
        result['message'] = constants.CSV_NOT_EXPORTED
        return result


def _get_smtp_settings():
    import os
    from cms.models import Setting
    
    try:
        smtp_host = Setting.objects.getKey('SMTP_HOST').value
    except Setting.DoesNotExist:
        smtp_host = ''
    
    try:
        smtp_port = int(Setting.objects.getKey('SMTP_PORT').value)
    except Setting.DoesNotExist:
        smtp_port = ''
    
    try:
        smtp_username = Setting.objects.getKey('SMTP_USERNAME').value
    except Setting.DoesNotExist:
        smtp_username = ''
    
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    
    return smtp_host, smtp_port, smtp_username, smtp_password


def _get_email_recipients(recipients_key):
    """Get recipients list from Settings."""
    from cms.models import Setting
    
    try:
        recipients_str = Setting.objects.getKey(recipients_key).value
    except Setting.DoesNotExist:
        return []
    
    return [email.strip() for email in recipients_str.split(',') if email.strip()]


def _create_email_message(subject, text_content, html_content, smtp_username, recipients):
    """Create MIME email message with text and HTML parts."""
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    
    msg = MIMEMultipart('alternative')
    msg['From'] = smtp_username
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    
    part1 = MIMEText(text_content, 'plain', 'utf-8')
    msg.attach(part1)
    
    if html_content:
        part2 = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(part2)
    
    return msg


def _add_attachments_to_message(msg, attachments):
    """Add file attachments to email message."""
    from email.mime.base import MIMEBase
    from email import encoders
    
    if not attachments:
        return
    
    for attachment in attachments:
        file_path = attachment.get('file_path')
        filename = attachment.get('filename', os.path.basename(file_path))
        
        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                msg.attach(part)


def send_email_notification(subject, text_content, html_content=None, attachments=None, recipients_key='DRONE_SPRAY_EMAIL_RECIPIENTS'):
   
    import smtplib
    
    try:
        # Get SMTP configuration
        smtp_host, smtp_port, smtp_username, smtp_password = _get_smtp_settings()
        
        if not smtp_username or not smtp_password:
            return False, "SMTP credentials not configured in Settings. Please add SMTP_USERNAME and SMTP_PASSWORD."
        
        # Get recipients
        recipients = _get_email_recipients(recipients_key)
        
        if not recipients:
            return False, f"No recipients configured for key: {recipients_key}. Please add this setting with comma-separated emails."
        
        # Create message
        msg = _create_email_message(subject, text_content, html_content, smtp_username, recipients)
        
        # Add attachments
        _add_attachments_to_message(msg, attachments)
        
        # Send email
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_username, recipients, msg.as_string())
        server.quit()
        
        return True, f"Email sent successfully to {len(recipients)} recipient(s): {', '.join(recipients)}"
        
    except (smtplib.SMTPException, OSError) as exc:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error sending email: {error_details}")
        return False, f"Error sending email: {str(exc)}"


def _get_formatted_created_time(booking):
    """Extract and format creation time from booking."""
    return booking.created_at.strftime('%B %d, %Y at %I:%M %p IST') if booking.created_at else 'N/A'


def _get_preferred_week_range(booking):
    """Extract preferred week date range from booking."""
    if booking.preferred_week_start and booking.preferred_week_end:
        return f"{booking.preferred_week_start} to {booking.preferred_week_end}"
    return 'Not specified'


def _get_farm_coordinates(booking):
    """Extract and format farm latitude and longitude."""
    farm_lat = booking.farm.latitude if booking.farm and booking.farm.latitude else None
    farm_lng = booking.farm.longitude if booking.farm and booking.farm.longitude else None
    return farm_lat, farm_lng


def _get_google_maps_link(farm_lat, farm_lng):
    """Generate Google Maps link from coordinates."""
    if farm_lat and farm_lng:
        return f"https://www.google.com/maps?q={farm_lat},{farm_lng}"
    return 'N/A'


def _get_farmer_and_org_details(booking):
    """Extract farmer and organization details."""
    return {
        'farmer_name': booking.farmer.full_name if booking.farmer else 'N/A',
        'farmer_phone': booking.farmer.mobile_number if booking.farmer else 'N/A',
        'farm_name': booking.farm.name if booking.farm else 'N/A',
        'organization_name': booking.organization.org_name if booking.organization else 'N/A',
    }


def _get_location_details(booking):
    """Extract location details."""
    return {
        'village': booking.village or 'N/A',
        'tehsil': booking.tehsil or 'N/A',
        'district': booking.district or 'N/A',
        'state': booking.state or 'N/A',
    }


def _get_coordinates_data(farm_lat, farm_lng):
    """Extract coordinate data."""
    return {
        'farm_latitude': farm_lat or 'N/A',
        'farm_longitude': farm_lng or 'N/A',
        'farm_coordinates': f"{farm_lat}, {farm_lng}" if farm_lat and farm_lng else 'N/A',
    }


def _get_crop_and_area_data(booking):
    """Extract crop and area details."""
    return {
        'crop': booking.crop or 'N/A',
        'area_total': booking.area_total,
        'area_unit': booking.area_unit or 'acres',
    }


def _get_user_details(user):
    """Extract user details."""
    return {
        'user_name': user.full_name or user.mobile_number,
        'user_id': user.id,
    }


def _build_template_context(booking, user):
    """Build context dictionary for email templates."""
    created_time = _get_formatted_created_time(booking)
    preferred_week = _get_preferred_week_range(booking)
    spray_type = booking.get_spray_type()
    
    farm_lat, farm_lng = _get_farm_coordinates(booking)
    google_maps_link = _get_google_maps_link(farm_lat, farm_lng)
    
    context = {
        'reference_id': booking.reference_id,
        'booking_id': booking.id,
        'status': booking.status,
        'created_time': created_time,
        'spray_type': spray_type,
        'google_maps_link': google_maps_link,
        'preferred_week': preferred_week,
    }
    
    context.update(_get_farmer_and_org_details(booking))
    context.update(_get_location_details(booking))
    context.update(_get_coordinates_data(farm_lat, farm_lng))
    context.update(_get_crop_and_area_data(booking))
    context.update(_get_user_details(user))
    
    return context


def _get_default_text_template(context):
    """Get default text email template."""
    return f"""
New Drone Spray Booking Requested
==================================

Reference ID: {context['reference_id']}
Booking ID: {context['booking_id']}
Status: {context['status']}
Requested At: {context['created_time']}

FARMER & FARM DETAILS:
----------------------
Farmer: {context['farmer_name']}
Farmer Phone: {context['farmer_phone']}
Farm: {context['farm_name']}
Organization: {context['organization_name']}

LOCATION:
---------
Village: {context['village']}
Tehsil: {context['tehsil']}
District: {context['district']}
State: {context['state']}
Coordinates: {context['farm_coordinates']}
Google Maps: {context['google_maps_link']}

SPRAY REQUEST DETAILS:
----------------------
Spray Type: {context['spray_type']}
Crop: {context['crop']}
Total Farm Area: {context['area_total']} {context['area_unit']}
Preferred Week: {context['preferred_week']}

REQUESTED BY:
-------------
Name: {context['user_name']}
User ID: {context['user_id']}

NEXT STEPS:
-----------
1. Review the booking details
2. Verify farm location and area
3. Schedule the drone spray operation

View booking details: /admin/recordActivity/dronesprayactivity/{context['booking_id']}/

Best regards,
Arya.ag Drone Spray System
"""


def _get_default_html_template(context):
    """Get default HTML email template."""
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 700px;
            margin: 20px auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 600;
        }}
        .header .ref-id {{
            font-size: 14px;
            opacity: 0.9;
            margin-top: 8px;
            font-family: monospace;
        }}
        .content {{
            padding: 30px;
        }}
        .status-badge {{
            display: inline-block;
            padding: 8px 16px;
            background: #FFC107;
            color: #333;
            border-radius: 4px;
            font-weight: bold;
            font-size: 14px;
            margin: 10px 0;
        }}
        .section {{
            margin: 25px 0;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            color: #2196F3;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .field {{
            margin: 10px 0;
            padding: 8px 0;
        }}
        .label {{
            font-weight: 600;
            color: #555;
            min-width: 160px;
            display: inline-block;
        }}
        .value {{
            color: #333;
        }}
        .highlight {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #2196F3;
            margin: 15px 0;
        }}
        .action-box {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .action-box h3 {{
            margin-top: 0;
            color: #856404;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            background: #f9f9f9;
            border-top: 1px solid #e0e0e0;
            color: #777;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🆕 New Drone Spray Request</h1>
            <div class="ref-id">Reference: {context['reference_id']}</div>
        </div>
        
        <div class="content">
            <div class="section">
                <div class="field">
                    <span class="label">Status:</span>
                    <span class="status-badge">{context['status']}</span>
                </div>
                <div class="field">
                    <span class="label">Requested At:</span>
                    <span class="value">{context['created_time']}</span>
                </div>
                <div class="field">
                    <span class="label">Booking ID:</span>
                    <span class="value">#{context['booking_id']}</span>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">Farmer & Farm Details</div>
                <div class="highlight">
                    <div class="field">
                        <span class="label">Farmer:</span>
                        <span class="value" style="font-weight: bold;">{context['farmer_name']}</span>
                    </div>
                    <div class="field">
                        <span class="label">Phone:</span>
                        <span class="value">{context['farmer_phone']}</span>
                    </div>
                    <div class="field">
                        <span class="label">Farm:</span>
                        <span class="value">{context['farm_name']}</span>
                    </div>
                    <div class="field">
                        <span class="label">Organization:</span>
                        <span class="value">{context['organization_name']}</span>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">Location</div>
                <div class="field">
                    <span class="label">Village:</span>
                    <span class="value">{context['village']}</span>
                </div>
                <div class="field">
                    <span class="label">Tehsil:</span>
                    <span class="value">{context['tehsil']}</span>
                </div>
                <div class="field">
                    <span class="label">District:</span>
                    <span class="value">{context['district']}</span>
                </div>
                <div class="field">
                    <span class="label">State:</span>
                    <span class="value">{context['state']}</span>
                </div>
                <div class="field">
                    <span class="label">Coordinates:</span>
                    <span class="value">{context['farm_coordinates']}</span>
                </div>
                <div class="field">
                    <span class="label">Navigate:</span>
                    <span class="value"><a href="{context['google_maps_link']}" style="color: #2196F3; text-decoration: none;">📍 Open in Google Maps</a></span>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">Spray Request Details</div>
                <div class="field">
                    <span class="label">Spray Type:</span>
                    <span class="value" style="font-weight: bold; color: #2196F3;">{context['spray_type']}</span>
                </div>
                <div class="field">
                    <span class="label">Crop:</span>
                    <span class="value">{context['crop']}</span>
                </div>
                <div class="field">
                    <span class="label">Total Farm Area:</span>
                    <span class="value" style="font-weight: bold;">{context['area_total']} {context['area_unit']}</span>
                </div>
                <div class="field">
                    <span class="label">Preferred Week:</span>
                    <span class="value">{context['preferred_week']}</span>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">Requested By</div>
                <div class="field">
                    <span class="label">Name:</span>
                    <span class="value">{context['user_name']}</span>
                </div>
                <div class="field">
                    <span class="label">User ID:</span>
                    <span class="value">{context['user_id']}</span>
                </div>
            </div>
            
        </div>
        
        <div class="footer">
            <p><strong>Powered by Arya.ag Drone Spray System</strong></p>
            <p>This is an automated notification for new booking requests.</p>
            <p>Booking Reference: {context['reference_id']}</p>
        </div>
    </div>
</body>
</html>
"""


def _get_template_from_settings(key, context, default_template):
    """Get template from Settings and format it with context."""
    from cms.models import Setting
    
    try:
        template = Setting.objects.getKey(key).value
        return template.format(**context)
    except (Setting.DoesNotExist, KeyError, AttributeError):
        return default_template


def get_drone_spray_booking_request_email_template(booking, user):
    from cms.models import Setting
    
    # Build context
    context = _build_template_context(booking, user)
    
    # Get subject
    subject = _get_template_from_settings(
        'DRONE_SPRAY_EMAIL_SUBJECT',
        context,
        f"🆕 New Drone Spray Request - {booking.reference_id}"
    )
    
    # Get text content
    text_content = _get_template_from_settings(
        'DRONE_SPRAY_EMAIL_TEXT_TEMPLATE',
        context,
        _get_default_text_template(context)
    )
    
    # Get HTML content
    html_content = _get_template_from_settings(
        'DRONE_SPRAY_EMAIL_HTML_TEMPLATE',
        context,
        _get_default_html_template(context)
    )
    
    return subject, text_content, html_content



def getDocumentDetails(user):
    data= Document.objects.order_by('id').all()
    for k,i in enumerate(data):
        data_verified=UserVerificationDocument.objects.filter(user=user,document_type=i).last()
        if data_verified:
            data[k].is_verified=data_verified.status
        else:
            data[k].is_verified=0

    return data


def getCompliance(user):
    data= compliance.objects.filter(user_id=user).all()
    return data

def checkIfDocumentUploaded(user,data=False):
    if data is False:
        data= getDocumentDetails(user)
    not_completed=1
    flag=flag2=flag3=flag4=0

    for i in data:
        if i.id==settings.SIGNZY_ADHAR_DOC_ID and i.is_verified==1:
            flag=1
        elif i.id==settings.ONEMONEY_DOCUMENT_ID and i.is_verified==1: 
            flag2=1
        elif i.id==settings.SIGNZY_PAN_DOC_ID and i.is_verified==1:
            flag3=1
        elif i.id==settings.SIGNZY_GST_DOC_ID and i.is_verified==1:
            flag4=1
            

    uploaded_data=getCompliance(user)
    for i in uploaded_data:
        if i.document_type=="aadhaarProofDocument":
            flag=1
        elif i.document_type=="bankStatement":
            flag2=1
        elif i.document_type=="businessPAN":
            flag3=1
        elif i.document_type=="gstProof":
            flag4=1
        
    if flag==1 and flag2==1 and flag3==1 and flag4==1:
        not_completed=0
    
    return not_completed==0


def updateDocumentStep(user,data=False):
    unsecure_step= UnsecureLoanStep.objects.get_loan_document()        
    if checkIfDocumentUploaded(user=user,data=data):
        UserUnsecureLoan.objects.update_or_create(user=user,unsecure_step=unsecure_step)
    else:
        delete_obj=UserUnsecureLoan.objects.filter(user=user,unsecure_step=unsecure_step)
        if delete_obj:
            delete_obj.delete()
def generate_signature(message):
    try:
        secret = bytes(settings.ONEMONEY_WEBHOOK_SECRET, 'utf-8')

        signature = base64.b64encode(hmac.new(secret, message, digestmod=hashlib.sha256).digest())
        return str(signature, 'utf-8')
    except:
        return None


def short_url(url_data):    

    url = settings.APILAYER_SHORT+"hash"

    payload = url_data.encode("utf-8")
    headers= {
    "apikey": settings.APILAYER_SHORT_KEY
    }
    response = requests.request("POST", url, headers=headers, data = payload)

    status_code = response.status_code
    if status_code==200:
        return response.text    
    return False
    
def replaceHttp(s):
    return s.replace("http://","https://")



def remove_media(self, instance,SerializerInstance,key):
    rep = super(SerializerInstance,self).to_representation(instance)
    try:
        url = None
        if self.context.get('request'):
            url= self.context['request'].build_absolute_uri("/")
            url=url.rstrip(url[-1])
        if key in rep.keys() and rep[key] != None:
            rep[key] = rep[key].replace("/media/","")
            rep[key] = rep[key].replace("%3A",":/")
            if url:
                rep[key] = rep[key].replace(url,"")
    except KeyError:
        return rep
    return rep

def downlod_sample(fields):
    pass

def upload_csv(csv_file,model,fields_name: list,custom:dict=None,unique:list=None):
    
    data=[]
    result={"success":False,"message":'',"data":data}
    
    if not csv_file.name.endswith('.csv'):
        result={"success":False,"data":data,"message":'The wrong file type was uploaded'}
    a = csv_file.read()
    file_data = a.decode("utf-8")
    csv_data = file_data.split("\n")

    
    for k,x in enumerate(csv_data):
        if k>0 and x:
            fields = x.split(",")
            temp_data={}
            unique_flag=False
            for count,i in enumerate(fields_name):
                if i in unique:
                    filter_args = Q(**{i: fields[count]})                    
                    check=model.objects.filter(filter_args).exists()

                    if check:
                        unique_flag=True
                    else:
                        temp_data[i]=fields[count]

                else:
                    temp_data[i]=fields[count]
                
            if not unique_flag:
                if custom:
                    temp_data=dict(temp_data.items() | custom.items())
                data.append(
                        temp_data
                    )

    created = model.objects.bulk_create([model(**item) for item in data])
   
    result={"success":True,"data":created,"message":'File uploaded'}

    return result


def downloadCsvSampleCSV(heading:list):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="data.csv"'

    # Create a CSV writer and write the data to the response
    writer = csv.writer(response)
    
    writer.writerow(heading)

    return response

def getusersifadmin(user):
    user_id=[]
    if user.user_role.role_name=="Admin":
        user_id=userModel.objects.get_all_admin(user.organization_id)
    else:
        user_id=[user.id]
    return user_id

def deductValidityNumber(user:userModel,service_slug,value):  
    user_id=getusersifadmin(user) 
    today_date = date.today()  
    service=UserService.objects.get_remaining(service_slug,user_id).filter(user_subscription__validity__gt=today_date).order_by('id').first()
   
    if service:
        UserService.objects.filter(id=service.id).update(remaining=F('remaining') - value)

def getRemainingService(service_slug,user):
    user_id=getusersifadmin(user)   
    service=UserService.objects.get_remaining(service_slug,user_id).first()
    return service


def getCibilCalculation(cibil_setting,avgcibil):
    cibil_setting=cibil_setting.value.split('/')
    for i in cibil_setting:
            x= i.split(',')
            if float(avgcibil) >= float(x[0]) and float(avgcibil) <=float(x[1]):
                avgcibil=x[2]
    
    return avgcibil
def calculate_magnitude(vector):
    # Calculate the magnitude of the 3D vector
    magnitude = math.sqrt(sum(component**2 for component in vector))
    return magnitude

# Function to do 60% fuzzy match between 2 strings.
def do_name_match(name1, name2):
    """
    # Function to do 60% fuzzy match between 2 strings.
    """
    # Calculate the similarity ratio
    similarity_ratio = fuzz.ratio(name1, name2)

    # Check if the ratio is greater than or equal to 60%
    return similarity_ratio >= 60


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the distance between two points on the Earth's surface
    using the Haversine formula.

    Parameters:
        lat1, lon1: Latitude and longitude of the first point (in degrees)
        lat2, lon2: Latitude and longitude of the second point (in degrees)

    Returns:
        Distance between the two points in kilometers.
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = 6371 * c  # Earth radius in kilometers (use 3958.8 for miles)

    return distance



def resize_image_if_needed(file, max_size=(1000, 1000)):
    """
    Resize the image if its dimensions exceed the specified max_size.

    Args:
        file (InMemoryUploadedFile): The original image file.
        max_size (tuple): Maximum allowed dimensions (width, height).

    Returns:
        InMemoryUploadedFile: The resized image file, or the original if resizing was not needed.
    """
    # Open the image using Pillow
    image = Image.open(file)

    # Check if the image needs to be resized
    if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
        # Resize the image while maintaining the aspect ratio
        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.ANTIALIAS
        image.thumbnail(max_size, resample)
        # Save the resized image to a BytesIO object
        img_io = BytesIO()
        image_format = image.format if image.format else 'JPEG'
        image.save(img_io, format=image_format)
        img_io.seek(0)
        
        # Create a new InMemoryUploadedFile object from the BytesIO object
        resized_file = InMemoryUploadedFile(
            img_io, 
            None, 
            file.name, 
            file.content_type, 
            img_io.getbuffer().nbytes, 
            None
        )

        # Reset the file pointer to the beginning
        resized_file.seek(0)
        return resized_file
    
    # Reset the file pointer to the beginning for the original file
    file.seek(0)
    return file

import base64
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_pdf_base64_from_json(json_data):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    x = 50
    y = height - 50
    p.setFont("Helvetica", 12)

    for key, value in json_data.items():
        line = f"{key}: {value}"
        p.drawString(x, y, line)
        y -= 20
        if y < 50:
            p.showPage()
            y = height - 50

    p.save()
    buffer.seek(0)
    pdf_bytes = buffer.read()
    encoded_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    return encoded_pdf



def truncate_text(text, max_length):
    """
    Trims a string to a specified maximum length and appends an ellipsis if truncated.

    Args:
        text (str): The input string to be truncated.
        max_length (int): The maximum desired length of the string, including the ellipsis.

    Returns:
        str: The truncated string with or without an ellipsis.
    """
    if len(text) > max_length:
        return text[:max_length - 3] + "..."  # Subtract 3 for the "..."
    else:
        return text
