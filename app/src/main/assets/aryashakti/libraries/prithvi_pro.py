import subprocess
import json
from django.conf import settings


class PrithviProLibrary:
    BASE_URL = settings.PRITHVI_PRO_URL

    def get_requirement(self, crop_id=None, variety_id=None, page=None, token=None):
        """
        Calls Prithvi Pro Requirements List API with optional pagination
        Example:
            /api/auth/requirements/list/?crop_id=3&variety_id=2&page=1
        """
        url = f"{self.BASE_URL}auth/requirements/list/"
        params = []
        if crop_id:
            params.append(f"crop_id={crop_id}")
        if variety_id:
            params.append(f"variety_id={variety_id}")
        if page:
            params.append(f"page={page}")
        if params:
            url += "?" + "&".join(params)

        cmd = [
            "curl", "-s", "-X", "GET", url,
            "-H", f"Content-Type: application/json",
            "--data", ""   # matches your original curl
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            response_text = result.stdout.strip()
            print(response_text)
            return json.loads(response_text) if response_text else {
                "success": False,
                "message": "Empty response"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": "Failed to call Prithvi Pro API",
                "error": e.stderr
            }
        except json.JSONDecodeError:
            return {
                "success": False,
                "message": "Invalid JSON response",
                "raw": result.stdout
            }


    def accept_requorement(self,requirement_id,fpo_id):
        url = f"{self.BASE_URL}auth/requirements/accept/"


        payload=json.dumps({"requirement_id":requirement_id,"fpo_id":fpo_id})

        cmd = [
            "curl", "-s", "-X", "POST", url,
            "-H", f"Content-Type: application/json",
            "--data", payload
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            response_text = result.stdout.strip()
            print(response_text)
            return json.loads(response_text) if response_text else {
                "success": False,
                "message": "Empty response"
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "message": "Failed to call Prithvi Pro API",
                "error": e.stderr
            }