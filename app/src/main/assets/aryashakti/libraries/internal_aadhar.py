import requests

class ExtractAPIClient:
    BASE_URL = "http://10.21.0.231:8082"
    ENDPOINT = "/extract"

    @staticmethod
    def get_headers():
        return {"accept": "application/json"}

    def extract_from_file_objects(self, front_file, back_file):
        url = f"{self.BASE_URL}{self.ENDPOINT}"

        files = {
            "front_image": ("front.jpg", front_file, front_file.content_type),
            "back_image": ("back.jpg", back_file, back_file.content_type),
        }

        try:
            response = requests.post(url, headers=self.get_headers(), files=files)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
