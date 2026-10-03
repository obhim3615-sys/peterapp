import base64
import json
import hashlib
import hmac
import uuid
from typing import Dict, Any
import requests
from django.conf import settings


class PAMSIntegrationError(Exception):
    """Custom exception for PAMS integration errors."""
    pass


class PAMSClient:
    """
    PAMS Penny Drop Integration Client

    Uses configuration from Django settings.
    Only dynamic values:
    - user_id
    - bank payload
    """

    CUSTOMER_TYPE = "ARYASHAKTI"

    REGISTER_ACCOUNT_ENDPOINT = "/accountmanager/registerAccount"

    def __init__(self):

        self.base_url = settings.PAMS_BASE_URL.rstrip("/")

        self.client_id = settings.PAMS_CLIENT_ID

        self.secret_key = settings.PAMS_SECRET_KEY

        self.payload_hashing_salt = settings.PAMS_PAYLOAD_HASHING_SALT

        self.tenant_id = settings.PAMS_TENANT_ID

        self.timeout = getattr(settings, "PAMS_TIMEOUT", 30)

    # ---------------------------------------------------------------------
    # PRIVATE METHODS
    # ---------------------------------------------------------------------

    @staticmethod
    def compute_hash(
        payload: str,
        secret_key: str
    ) -> str:
        

        hmac_hash = hmac.new(
            key=secret_key.encode("utf-8"),
            msg=payload.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()

        return base64.b64encode(
            hmac_hash
        ).decode("utf-8")


    def _generate_trace_id(self) -> str:
        return str(uuid.uuid4())
    

    def sort_keys_recursive(self,data):
        if isinstance(data, dict):
            return {
                k: self.sort_keys_recursive(v)
                for k, v in sorted(data.items())
            }

        if isinstance(data, list):
            return [
                self.sort_keys_recursive(v)
                for v in data
            ]

        return data

    def _generate_payload_token(
        self,
        payload: Dict[str, Any]
    ) -> str:
        """
        Generate x-payload-token using HMAC SHA256
        """
        print("Secret key",self.secret_key)
        print("Secret salt key",self.payload_hashing_salt)
        request_payload = {
            "payload": payload
        }

        sorted_payload = self.sort_keys_recursive(
            request_payload
        )

        payload_string = json.dumps(
            sorted_payload,
            separators=(",", ":")
        )

        token = self.compute_hash(
            payload=payload_string,
            secret_key=self.payload_hashing_salt
        )

        print(f"PAMS token: {payload_string} " )
        print(f"PAMS token: {token} " )

        return token
    
        



    def _build_headers(
        self,
        payload: Dict[str, Any],
        user_id: int
    ) -> Dict[str, str]:

        trace_id = self._generate_trace_id()

        return {
            "x-api-client-id": self.client_id,
            "x-secret-key": self.secret_key,
            "x-user-id": str(user_id),
            "x-tenant-id": str(self.tenant_id),
            "x-trace-id": trace_id,
            "x-span-id": trace_id,
            "x-payload-token": self._generate_payload_token(payload),
            "Content-Type": "application/json"
        }

    def _post(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:

        url = f"{self.base_url}{endpoint}"

        headers = self._build_headers(
            payload=payload,
            user_id=user_id
        )

        body = {
            "payload": payload
        }

        try:

            response = requests.post(
                url=url,
                headers=headers,
                json=body,
                timeout=(5, self.timeout)
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:

            raise PAMSIntegrationError(
                f"PAMS HTTP Error: {str(e)} | "
                f"Response: {response.text}"
            )

        except requests.exceptions.RequestException as e:

            raise PAMSIntegrationError(
                f"PAMS Request Failed: {str(e)}"
            )

        except Exception as e:

            raise PAMSIntegrationError(
                f"PAMS Unexpected Error: {str(e)}"
            )

    # ---------------------------------------------------------------------
    # PUBLIC METHODS
    # ---------------------------------------------------------------------

    def register_account(
        self,
        *,
        user_id: int,
        customer_id: int,
        beneficiary_name: str,
        beneficiary_account_no: str,
        ifsc_code: str,
        bank_name: str,
        bank_city: str,
        account_type: str = "SAVING"
    ) -> Dict[str, Any]:
        """
        Register account and trigger Penny Drop verification.
        """

        payload = {
            "customerId": customer_id,
            "bankName": bank_name,
            "beneficiaryAccountNo": beneficiary_account_no,
            "ifscCode": ifsc_code,
            "beneficiaryName": beneficiary_name,
            "bankCity": bank_city,
            "accountType": account_type,
            "customerType": self.CUSTOMER_TYPE,
            "docsReferenceId": None,
            "saveDocsReferenceId": None,
            "isPennyDropHold": False,
            "pennyDropRequired": True
        }

        return self._post(
            endpoint=self.REGISTER_ACCOUNT_ENDPOINT,
            payload=payload,
            user_id=user_id
        )

    # ---------------------------------------------------------------------
    # RESPONSE HELPERS
    # ---------------------------------------------------------------------

    @staticmethod
    def get_payload(response: Dict[str, Any]) -> Dict[str, Any]:

        return response.get("payload", {})

    @staticmethod
    def is_success(response: Dict[str, Any]) -> bool:

        return response.get("success", False)

    @staticmethod
    def get_pams_account_id(
        response: Dict[str, Any]
    ):

        return response.get(
            "payload",
            {}
        ).get("pamsAccountId")

    @staticmethod
    def get_status(
        response: Dict[str, Any]
    ) -> str:

        return response.get(
            "payload",
            {}
        ).get("status", "")

    @staticmethod
    def is_validated(
        response: Dict[str, Any]
    ) -> bool:

        return response.get(
            "payload",
            {}
        ).get("isValidated", False)

    @staticmethod
    def get_validation_remarks(
        response: Dict[str, Any]
    ) -> str:

        return response.get(
            "payload",
            {}
        ).get("validationRemarks", "")