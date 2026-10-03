from app_farm.utils.helper import postRequest
from django.conf import settings


# --------------------------
# NoMS: single-send SMS helper (thread safe)
# --------------------------
class NoMS:
    def __init__(self):
        self.base_url = settings.NOMS_URL
        self.user_id = settings.NOMS_USER_ID

    def send_sms(self, customer_id, notification_type, created_by, payload):
        url = f"{self.base_url}/api/v1/notification/send"
        headers = {
            'x-auth-key': settings.NOMS_AUTH_KEY,
            'x-api-client-id': settings.NOMS_API_CLIENT_ID,
            'x-tenant-id': settings.NOMS_TENANT_ID,
            'Content-Type': 'application/json',
            "x-user-id": self.user_id
        }
        data = {
            'payload': {
                'customerId': customer_id,
                'notificationType': notification_type,
                'createdBy': created_by,
                'smsInfo': payload
            }
        }
        response = postRequest(url, data, headers)
        if response.status_code == 200:
            return response.json()
        return {"success": False, "error": f"status_code_{response.status_code}"}

    def send_smsv2(self, customer_id, notification_type, created_by, payload, language="EN"):
        """
        Single SMS send — NO internal sleeps.
        Safe to call from a worker thread.
        """
        url = f"{self.base_url}/api/v2/notification/send"
        headers = {
            'x-auth-key': settings.NOMS_AUTH_KEY,
            'x-api-client-id': settings.NOMS_API_CLIENT_ID,
            'x-tenant-id': settings.NOMS_TENANT_ID,
            'Content-Type': 'application/json',
            "x-user-id": self.user_id
        }
        data = {
            'payload': {
                'customerId': customer_id,
                'notificationType': notification_type,
                'createdBy': created_by,
                'smsInfo': payload,
                "preferredLanguage": language
            }
        }
        response = postRequest(url, data, headers)
        # be defensive: ensure response.json() call is safe
        try:
            result = response.json()
            
        except Exception:
            result = {"success": False, "error": "invalid_json_response"}
       
        result["success"] = (response.status_code == 200)
        return result

    def send_bulk_message(self, notification_type, created_by, payload, customer_id=0):
        url = f"{self.base_url}/api/v1/notification/bulk/send"
        headers = {
            'x-auth-key': settings.NOMS_AUTH_KEY,
            'x-api-client-id': settings.NOMS_API_CLIENT_ID,
            'x-tenant-id': settings.NOMS_TENANT_ID,
            "x-user-id": self.user_id,
            'Content-Type': 'application/json',
        }
        data = {
            'payload': {
                'customerId': customer_id,
                'notificationType': notification_type,
                'createdBy': created_by,
                'bulkSmsInfo': payload
            }
        }
        response = postRequest(url, data, headers)
        if response.status_code == 200:
            return response.json()
        return {"success": False, "error": f"status_code_{response.status_code}"}

    def send_email(self, msg_body, template_id, send_to, send_from, msg_header, attachments, ccList):
        url = f"{self.base_url}/api/v1/notification/send"
        headers = {
            'x-auth-key': settings.NOMS_AUTH_KEY,
            'x-api-client-id': settings.NOMS_API_CLIENT_ID,
            'x-tenant-id': settings.NOMS_TENANT_ID,
            'Content-Type': 'application/json',
            "x-user-id": self.user_id
        }
        data = {
            "metaInfo": {
                "version": "v1",
                "servedBy": "localhost",
                "requestId": "somereq",
                "apiKey": "pams",
                "userContext": {"userId": 876556, "userAgentContext": {"userAgent": "Mobile"}},
                "experiments": [],
                "traceContext": {},
                "tenantContext": {"tenantId": settings.NOMS_TENANT_ID, "tenantName": "AryaTech", "active": True}
            },
            'payload': {
                'customerId': 123456,
                'notificationType': 'TRANSACTIONAL',
                'createdBy': 'User',
                'emailInfo': {
                    'msgBody': msg_body,
                    'templateId': template_id,
                    'sendTo': send_to,
                    'sendFrom': send_from,
                    'msgHeader': msg_header,
                    'attachments': attachments,
                    'ccList': ccList
                }
            }
        }
        response = postRequest(url, data, headers)
        if response.status_code == 200:
            return response.json()
        return {"success": False, "error": f"status_code_{response.status_code}"}
