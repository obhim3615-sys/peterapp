from app_farm.utils.helper import postRequest
from django.conf import settings
from datetime import datetime, timedelta
from insurance.models import Kutumb






import requests

# Global Bearer token (you can update this when refreshed)
BEARER_TOKEN = "your_actual_bearer_token_here"

class MemberOnboardingAPI:
    BASE_URL = "http://localhost:9924/cali/uw/member"

    @staticmethod
    def get_headers():
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {BEARER_TOKEN}"
        }

    @classmethod
    def onboard_members(cls, payload):
        url = f"{cls.BASE_URL}/onboard"
        headers = cls.get_headers()

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # Raise exception for HTTP errors
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err} - Response: {response.text}")
            return None
        except requests.exceptions.RequestException as err:
            print(f"Request exception: {err}")
            return None

# Example usage:
if __name__ == "__main__":
    # Replace this with your actual payload (you can load it from a file or another function)
    payload = {
        "members": [
            {
                "firstName": "John",
                "lastName": "Doe",
                "memberId": "12345",
                "dob": "1990-01-01",
                # ... add remaining fields ...
            }
        ],
        "policyHolderId": "holder123",
        "policyNumber": "POL123456",
        "policyBranch": "HO",
        "transactionDetails": {
            "sourceTransactionRef": "TXN123456",
            "key": "someKey"
        },
        "key": "anotherKey"
    }

    result = MemberOnboardingAPI.onboard_members(payload)
    print(result)

