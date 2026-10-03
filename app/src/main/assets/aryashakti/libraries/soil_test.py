import json
import requests
from django.conf import settings

class NeoPerk:
    def __init__(self):
        self.api_endpoint = settings.NEOPERK_BASE_URL  # Should be: "https://us-central1-neoperkproduction.cloudfunctions.net/"
        self.access_token = settings.NEOPERK_ACCESS_TOKEN  # Store token securely in settings

    def _headers(self):
        return {
            'Content-Type': 'application/json',
            'x-access-token': self.access_token
        }

    def add_soil_test_plot_data(self, payload: dict):
        """
        Adds soil test plot data using NeoPerk API.

        Required fields:
        - upcoming_crop_cycle, district, farmer_name, operator_note, mobile_number
        """

        # Validate mandatory fields
        required_fields = [
            "upcoming_crop_cycle", "district", "farmer_name",
            "operator_note", "mobile_number"
        ]
        missing_fields = [field for field in required_fields if field not in payload or not payload[field]]
        if missing_fields:
            return {
                "error": f"Missing mandatory fields: {', '.join(missing_fields)}"
            }

        url = f"{self.api_endpoint}ext-add-soiltest-plotdata"
        headers = self._headers()

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            return {
                "error": "HTTP error",
                "details": str(e),
                "response": response.text
            }
        except Exception as e:
            return {
                "error": "Unexpected error",
                "details": str(e)
            }



    def add_soil_test_plot_data(self, payload: dict):
        """
        Adds soil test plot data using NeoPerk API.

        Required fields:
        - upcoming_crop_cycle, district, farmer_name, operator_note, mobile_number
        """
        required_fields = [
            "upcoming_crop_cycle", "district", "farmer_name",
            "operator_note", "mobile_number"
        ]
        missing_fields = [field for field in required_fields if field not in payload or not payload[field]]
        if missing_fields:
            return {
                "error": f"Missing mandatory fields: {', '.join(missing_fields)}"
            }

        url = f"{self.api_endpoint}ext-add-soiltest-plotdata"
        headers = self._headers()

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            return {
                "error": "HTTP error",
                "details": str(e),
                "response": response.text
            }
        except Exception as e:
            return {
                "error": "Unexpected error",
                "details": str(e)
            }

    def fetch_merged_data(self, sample_id: str):
        """
        Fetch merged soil test data using sample ID.

        Parameters:
        - sample_id (str): The sample ID for which data is to be fetched.

        Returns:
        - dict: API response data or error.
        """
        if not sample_id:
            return {"error": "sample_id is required"}

        url = f"{self.api_endpoint}ext-get-merged-data?sample_id={sample_id}"
        headers = {'x-access-token': self.access_token}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            return {
                "error": "HTTP error",
                "details": str(e),
                "response": response.text
            }
        except Exception as e:
            return {
                "error": "Unexpected error",
                "details": str(e)
            }
