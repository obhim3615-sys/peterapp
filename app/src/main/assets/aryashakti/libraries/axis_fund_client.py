import json
import subprocess
import time
from uuid import uuid4
from django.conf import settings
from .encryption_utils import prepare_encrypted_request


class AxisFundTransferClient:
    def __init__(self):
        self.base_url = settings.AXIS_API_BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "x-ibm-client-id": settings.AXIS_CLIENT_ID,
            "x-ibm-client-secret": settings.AXIS_CLIENT_SECRET
        }
        self.pkcs12_path = settings.AXIS_P12_FILE_PATH
        self.pkcs12_password = settings.AXIS_P12_PASSWORD

    def _generate_subheader(self, uuid=None):
        return {
            "requestUUID": uuid or str(uuid4()),
            "serviceRequestId": "OpenAPI",
            "serviceRequestVersion": "1.0",
            "channelId": settings.AXIS_CORP_CHANNEL_ID
        }
    
    def set_dynamic_context(self, corp_code: str, corp_acc_num: str):
        self.dynamic_corp_code = corp_code
        self.dynamic_corp_acc_num = corp_acc_num

    def _default_payment_body(self, txnPaymode: str, overrides: dict = None) -> dict:
        default = {
            "channelId": settings.AXIS_CORP_CHANNEL_ID,
            "corpCode": self.dynamic_corp_code,
            "paymentDetails": [
                {
                    "txnPaymode": txnPaymode,
                    "custUniqRef": "TXN-REF-001",
                    "corpAccNum": self.dynamic_corp_acc_num,
                    "valueDate": "2025-07-21",
                    "txnAmount": "1000.00",
                    "beneLEI": "",
                    "beneName": "BENEFICIARY NAME",
                    "beneCode": "123456",
                    "beneAccNum": "0000000000",
                    "beneAcType": "11",
                    "beneAddr1": "ADDR1",
                    "beneAddr2": "ADDR2",
                    "beneAddr3": "ADDR3",
                    "beneCity": "CITY",
                    "beneState": "STATE",
                    "benePincode": "000000",
                    "beneIfscCode": "",
                    "beneBankName": "BANK NAME",
                    "baseCode": "",
                    "chequeNumber": "",
                    "chequeDate": "",
                    "payableLocation": "",
                    "printLocation": "",
                    "beneEmailAddr1": "email@example.com",
                    "beneMobileNo": "9876543210",
                    "productCode": "",
                    "txnType": "VEND",
                    "invoiceDetails": [
                        {
                            "invoiceAmount": "1000.00",
                            "invoiceNumber": "INV-00001",
                            "invoiceDate": "2025-07-21",
                            "cashDiscount": "0.00",
                            "tax": "0.00",
                            "netAmount": "0.00",
                            "invoiceInfo1": "",
                            "invoiceInfo2": "",
                            "invoiceInfo3": "",
                            "invoiceInfo4": "",
                            "invoiceInfo5": ""
                        }
                    ],
                    "enrichment1": "",
                    "enrichment2": "",
                    "enrichment3": "",
                    "enrichment4": "",
                    "enrichment5": "",
                    "senderToReceiverInfo": f"{txnPaymode} TEST TRANSACTION"
                }
            ]
        }
        if overrides:
            for key, val in overrides.items():
                if key == "paymentDetails":
                    default["paymentDetails"][0].update(val)
                else:
                    default[key] = val
        return default

    def _generate_curl(self, url, payload: dict) -> str:
        body_str = json.dumps(payload, separators=(",", ":")).replace('"', '\\"')
        return f"""
        curl --tlsv1.2 \\
        --cert-type P12 \\
        --cert "{self.pkcs12_path}:{self.pkcs12_password}" \\
        --location \\
        --request POST '{url}' \\
        -H "x-ibm-client-id: {settings.AXIS_CLIENT_ID}" \\
        -H "x-ibm-client-secret: {settings.AXIS_CLIENT_SECRET}" \\
        -H "Content-Type: application/json" \\
        -d "{body_str}"
        """.strip()

    def _execute_curl(self, curl_command: str) -> dict:
        start = time.time()
        result = subprocess.run(curl_command, shell=True, capture_output=True, text=True)
        duration = time.time() - start
        print(f"[AxisBank] ⏱️ curl duration: {duration:.2f}s")
        if result.stderr:
            print("❌ curl stderr:", result.stderr)

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON from curl", "stdout": result.stdout, "stderr": result.stderr}

    def initiate_fund_transfer(self, txnPaymode: str, overrides: dict = None, uuid=None) -> dict:
        uuid = uuid or str(uuid4())
        body = self._default_payment_body(txnPaymode, overrides)
        encrypted_payload = prepare_encrypted_request(body)

        request_payload = {
            "TransferPaymentRequest": {
                "SubHeader": self._generate_subheader(uuid),
                "TransferPaymentRequestBodyEncrypted": encrypted_payload
            }
        }
        url = f"{self.base_url}txb/v1/payments/transfer-payment"
        curl_command = self._generate_curl(url, request_payload)
        return self._execute_curl(curl_command)

    def _generate_status_request_body(self, crn: str) -> dict:
        return {
            "channelId": settings.AXIS_CORP_CHANNEL_ID,
            "corpCode": self.dynamic_corp_code,
            "crn": crn
        }

    def check_fund_transfer_status(self, crn: str) -> dict:
        body = self._generate_status_request_body(crn)
        encrypted_payload = prepare_encrypted_request(body)
        print(body)
        request_payload = {
            "GetStatusRequest": {
                "SubHeader": self._generate_subheader(),
                "GetStatusRequestBodyEncrypted": encrypted_payload
            }
        }

        url = f"{self.base_url}txb/v1/acct-recon/get-status"
        curl_command = self._generate_curl(url, request_payload)
        print(curl_command)
        return self._execute_curl(curl_command)

    def _generate_balance_request_body(self) -> dict:
        return {
            "channelId": settings.AXIS_CORP_CHANNEL_ID,
            "corpAccNum": self.dynamic_corp_acc_num,
            "corpCode": self.dynamic_corp_code
        }

    def check_account_balance(self, uuid=None) -> dict:
        body = self._generate_balance_request_body()
        encrypted_payload = prepare_encrypted_request(body)
        request_payload = {
            "GetAccountBalanceRequest": {
                "SubHeader": self._generate_subheader(uuid),
                "GetAccountBalanceRequestBodyEncrypted": encrypted_payload
            }
        }
        url = f"{self.base_url}txb/v1/acct-recon/get-balance"
        curl_command = self._generate_curl(url, request_payload)
        return self._execute_curl(curl_command)
