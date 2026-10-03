# libraries/gemini.py

import json

from google import genai
from google.genai import types


class GeminiResponsesClient:

    def __init__(self, api_key):
        
        self.client = genai.Client(api_key=api_key)

    def diagnose_crop(
        self,
        image_url,
        crop_name=None
    ):

        given_crop = (
            f"8. The crop in the image is given as {crop_name}"
            if crop_name
            else ""
        )

        prompt = f"""
            You are an Agronomic AI assistant developed by Aryashakti.

            You help farmers diagnose crop diseases using the provided image.

            Follow strict rules:

            1. Identify crop.
            2. Analyze symptoms.
            3. Diagnose disease.
            4. Provide advisory.
            5. Respond ONLY in valid JSON.
            6. Use English for all values.
            7. Keep crop_name and disease_name in standard agricultural English.
            8. Do NOT include text outside JSON.

            {given_crop}

            Format:

            {{
                "crop_name": "<crop name>",
                "diagnosis": "<analysis>",
                "disease_name": "<disease>",
                "type": "EOC",
                "advisory": "<advisory>"
            }}
            """

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                prompt,
                types.Part.from_uri(
                    file_uri=image_url,
                    mime_type="image/jpeg"
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        return json.loads(response.text)

    def translate_json(
        self,
        data,
        target_language_code="hi"
    ):

        prompt = f"""
            Translate all farmer-facing text into language code {target_language_code}.

            Rules:

            1. Return ONLY valid JSON.
            2. Preserve exact JSON structure.
            3. Do not remove keys.
            4. Do not add keys.
            5. Keep crop_name in English.
            6. Keep disease_name in English.
            7. Keep scientific names unchanged.
            8. Translate diagnosis and advisory only.

            JSON:

            {json.dumps(data, ensure_ascii=False)}
            """

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        return json.loads(response.text)




