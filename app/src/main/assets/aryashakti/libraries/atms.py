import subprocess
import json
from django.conf import settings
from typing import Optional, Dict


class AtMS:
    def __init__(self):
        self.api_endpoint = settings.ATMS_URL  # e.g., 'http://atms-dev.arya.ag/api/v1/'

    def get_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        base_headers = {
            'x-tenant-id': '1001',
            'x-api-client-id': 'aryashakti',
            'x-trace-id': '1001',
            'x-span-id': '1001',
            'x-user-id': 'AZ0181',
            'Content-Type': 'application/json',
            'x-private-key': settings.ATMS_PRIVATE_KEY,
        }
        if extra_headers:
            base_headers.update(extra_headers)
        return base_headers

    def run_curl(self, url: str, payload: dict, headers: dict) -> dict:
        # Convert headers to curl format
        header_args = []
        for key, value in headers.items():
            header_args.extend(["-H", f"{key}: {value}"])

        # Build curl command
        cmd = [
            "curl", "-s", "-X", "POST", url,
            "-d", json.dumps(payload)
        ] + header_args

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            print(e)
            return {"error": f"Curl failed: {e.stderr}"}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response"}

    def digilocker_info_request(
        self, email: str, redirect_url: str, callback_url: str,
        extra_headers: Optional[Dict[str, str]] = None
    ):
        headers = self.get_headers(extra_headers)
        payload = {
            "metaInfo": {
                "version": "v1",
                "servedBy": "localhost",
                "userAgent": "Mobile",
                "apiKey": "atms",
                "userContext": {
                    "userAgentContext": {"userAgent": "Mobile"}
                },
                "experiments": [
                    {"experimentId": 1234, "bucketId": 1},
                    {"experimentId": 4567, "bucketId": 0}
                ],
                "traceContext": {
                    "traceId": "1f35900b-3f40-4e9a-9ef2-66359f5b71df",
                    "parentSpanId": None,
                    "spanId": "851a1d16-7b48-4e35-9369-0a8855d18ff5",
                    "timestamp": "2024-09-05T14:59:44.000000+05:30"
                },
                "tenantContext": {
                    "tenantId": 1001,
                    "tenantName": "AryaTech",
                    "active": True,
                    "parentBusinessGroup": {
                        "groupId": 10000,
                        "groupName": "Arya CM & Warehouse Service Pvt. Ltd."
                    }
                }
            },
            "payload": {
                "digilockerInfo": {
                    "email": email,
                    "redirectUrl": redirect_url,
                    "callbackUrl": callback_url
                }
            }
        }

        url = self.api_endpoint + "signzy/details"
        return self.run_curl(url, payload, headers)

    def fetch_signzy_details_by_img(
        self, front_url: str, back_url: str,
        extra_headers: Optional[Dict[str, str]] = None
    ):
        headers = self.get_headers(extra_headers)
        payload = {
            "metaInfo": {
                "version": "v1",
                "servedBy": "localhost",
                "userAgent": "Mobile",
                "apiKey": "atms",
                "userContext": {"userAgentContext": {"userAgent": "Mobile"}},
                "experiments": [
                    {"experimentId": 1234, "bucketId": 1},
                    {"experimentId": 4567, "bucketId": 0}
                ],
                "traceContext": {
                    "traceId": "1f35900b-3f40-4e9a-9ef2-66359f5b71df",
                    "parentSpanId": None,
                    "spanId": "851a1d16-7b48-4e35-9369-0a8855d18ff5",
                    "timestamp": "2024-09-05T14:59:44.000000+05:30"
                },
                "tenantContext": {
                    "tenantId": 1001,
                    "tenantName": "AryaTech",
                    "active": True,
                    "parentBusinessGroup": {
                        "groupId": 10000,
                        "groupName": "Arya CM & Warehouse Service Pvt. Ltd."
                    }
                }
            },
            "payload": {
                "aadharDetailsFromImage": {
                    "frontUrl": front_url,
                    "backUrl": back_url
                }
            }
        }

        url = self.api_endpoint + "signzy/details"
        return self.run_curl(url, payload, headers)
