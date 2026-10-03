import requests
from django.conf import settings
class Fyllo:
    BASE_URL = settings.FYLLO_URL
    

    def __init__(self):
        self.user_id = settings.FYLLO_USER_NAME
        self.password = settings.FYLLO_USER_PASSWORD
        self.access_token = None

    def get_base_url(self) -> str:
        return self.BASE_URL

    def get_headers(self, include_auth=True) -> dict:
        headers = {
            "accept": "application/json",
            "Content-Type": "application/json",
        }
        if include_auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def authenticate(self) -> bool:
        """
        Authenticates the user and stores the access token.
        Returns True if successful, False otherwise.
        """
        url = f"{self.BASE_URL}/farm-users/login"
        payload = {
            "farmUserId": self.user_id,
            "otp": self.password
        }

        try:
            response = requests.post(url, json=payload, headers=self.get_headers(include_auth=False))
            response.raise_for_status()
            data = response.json()
            # print(data['access_token'])
            self.access_token = data.get("access_token")
            return self.access_token is not None
        except requests.RequestException as e:
            print(f"Authentication failed: {e}")
            return False
    
    def get_live_data(self, plot_id: str="smartfarmcentrehethgowa") -> dict:
        """
        Fetches live data for a given plot ID.
        Returns the response JSON or an error message.
        """
        if not self.access_token:
            raise ValueError("Authentication required. Please call authenticate() first.")

        url = f"{self.BASE_URL}/plots/{plot_id}/live-data"
        try:
            response = requests.get(url, headers=self.get_headers())

            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Failed to fetch live data for plot {plot_id}: {e}")
            return {"error": str(e)}

    