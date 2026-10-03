import requests
from django.conf import settings

class NeoPerkAPI:
    base_url = settings.NEOPERK_URL
    
    def __init__(self, access_token):
        self.access_token = access_token

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "x-access-token": self.access_token
        }

    def post(self, endpoint, data):
        """
        Send POST request to given endpoint with required headers and token in body.
        """
        url = f"{self.base_url}{endpoint}"
        # Ensure token is also included in the request body
        data["token"] = self.access_token

        response = requests.post(url, headers=self.get_headers(), json=data)
        
        return self.handle_response(response)

    def handle_response(self, response):
        """
        Handle success and error response formats.
        """
        if response.status_code == 200:
            return response.json()
        else:
            try:
                return {
                    "error": response.json().get("error", "Unknown error"),
                    "details": response.json().get("details", ""),
                    "status_code": response.status_code
                }
            except Exception:
                return {
                    "error": "Unexpected error format",
                    "status_code": response.status_code,
                    "raw": response.text
                }

    def add_soil_test_plot_data(self, data: dict):
        """
        Accepts full or partial soil test data and sends it to the external API.
        """
        endpoint = "ext-add-soiltest-plotdata"
        return self.post(endpoint, data)
    
