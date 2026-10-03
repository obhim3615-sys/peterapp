# services/openai_service.py

# import openai
from django.conf import settings

import requests
import json
import os

class OpenAIAPIIntegration:
    def __init__(self,openai_secret_key=None):
        if openai_secret_key:
            self.api_key=openai_secret_key
        else:
            self.api_key = settings.OPENAI_SECRET
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "assistants=v2"
        }

    def get_response_from_prompt(self, prompt):
        url = f"{self.base_url}/chat/completions"
        data = {
            "model": "gpt-4o-mini",  # You can change the model as required
           
            "messages":[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content":prompt},
            ],
            "max_tokens": 300,  # Adjust max tokens as required
            "temperature": 0.7  # Adjust temperature as required
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        response_json = response.json()
        
        if response.status_code == 200:
            return response_json.get('choices', [])[0].get('message').get('content')
        else:
            raise Exception(f"OpenAI API error: {response_json.get('error', {}).get('message')}")

    def create_prompt(self):
        return """
        I need you to identify a disease in a crop based on an image. Follow a structured approach as outlined below:

        1. Confirm the crop type based on the provided image.
        2. Identify the disease by examining the symptoms visible on the crop.
        3. Request additional details to refine the diagnosis.

        Here is an example workflow:

        Step 1: Confirm the crop type
        Observe the leaf shape, color, and any other notable features.
        Confirm the crop type based on these observations.

        Step 2: Identify the disease:
        Describe the symptoms visible on the crop, such as spots, lesions, discoloration, etc.
        Identify potential diseases based on these symptoms.
        Provide the most likely disease and its causal agents.

        Step 3: Request additional details
        Ask specific questions to refine the diagnosis, such as:
        - Are the spots primarily on older leaves or new growth? (Options: older leaves, new growth, both)
        - Have there been recent periods of high humidity or rainfall? (Options: yes, no)
        - Are there any other symptoms on the plant, such as wilting, leaf drop, or stem lesions? (Options: wilting, leaf drop, stem lesions, none)

        Ensure to follow this structured approach and respond in a conversational manner.

        Example Workflow:
        1-
        {  
            "question": "Confirm the crop:<crop_name>"
            type:"yes_no",
            response:"Based on the leaf shape and the presence of certain features, it looks like the crop might be cotton. Can you confirm this?"
        }
        2. Identify the Disease:
       
        { 
            type:"yes_no",
            response: "Now that we've identified the crop as cotton, I see small, reddish-brown spots on the leaves. This could be a sign of Cotton Leaf Spot disease, which is often caused by fungi like Cercospora, Alternaria, or Corynespora."
        }
        3. Additional Details:
         {
         "question": "To refine this diagnosis, I need a bit more information:
          "type" you can chose,
          "response":<responses>

         }
         #----you can take more json values from below---#
                    - Are the spots primarily on older leaves or new growth? 
                    - Have there been recent periods of high humidity or rainfall?
                    - Are there any other symptoms on the plant, such as wilting, leaf drop, or stem lesions?"
        
        And follow up with more questions if you need, in input define what type of input you need from frontend and then your response as text.

        And when you finally get the answer in type send eoc (End of conversation).
        Please follow this structure to guide the user through the disease identification process in a clear and systematic way. Keep it conversational in a way that proceeding to the next step requires a confirmation from the user (if needed). Keep conversation in Hindi.
        also just reply json in value
        """

    def create_assistant(self, assistant_name):
        url = f"{self.base_url}/assistants"
       
        payload = {
            "name": assistant_name,
            "instructions": self.create_prompt(),
            "tools": [{"type": "code_interpreter"}],
            "model": "gpt-4o"
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()
    

    def update_assistant(self,id,prompt):
        url = f"{self.base_url}/assistants/"+id
       
        payload = {
            #"name": assistant_name,
            "instructions": prompt,
            #"tools": [{"type": "code_interpreter"}],
            "model": "gpt-4o"
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()

    def create_thread(self,):
        url = f"{self.base_url}/threads"
        
        response = requests.post(url, headers=self.headers)
        return response.json()



    def send_image_with_thread(self, thread_id, textinput=None,image_url=None):
        url = f"{self.base_url}/threads/{thread_id}/messages"
       
        messages = []


        if textinput:
            messages.append({"type":"text","text": textinput})

        if image_url:
            messages.append({
                    "type": "image_url",
                    "image_url": {"url": image_url}
              
            })

       

        if not messages and not textinput:
            raise ValueError("At least one of image_url or textinput must be provided")

        payload = {
            "role":"user",
            "content":messages,
            # "attachments":[]
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()

    def run_thread(self,thread_id,assistant_id):
        url = f"{self.base_url}/threads/{thread_id}/runs"
       
      
        payload = {
            "assistant_id":assistant_id,
            "model":"gpt-4o",   
            #"response_format":{"type": "json_object"}
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()


    def get_run(self,thread_id,run_id):
        url = f"{self.base_url}/threads/{thread_id}/runs/"+run_id 
        response = requests.get(url, headers=self.headers)
        return response.json()


    def list_runs(self,thread_id):
        url = f"{self.base_url}/threads/{thread_id}/runs"
       
        response = requests.get(url, headers=self.headers)
        return response.json()
    

    def get_thread_messages(self, thread_id):
        url = f"{self.base_url}/threads/{thread_id}/messages"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()



class OpenAIResponsesClient:

    def __init__(self, api_key):
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def _send_openai_error_email(self, error_message):
        try:
            from app_farm.utils import helper

            helper.send_email_notification(
                subject="🚨 OpenAI API Error Alert",
                text_content=error_message,
                html_content=f"<p>{error_message}</p>",
                recipients_key='OPENAI_ERROR_EMAIL_RECIPIENTS'
            )
        except Exception:
            # Do not break API flow if email sending fails
            pass

    def diagnose_crop(self, image_url, language="English",crop_name=None):

        given_crop= "8. The crop in the image is given as "+crop_name  if crop_name else ""
        system_prompt = f"""
            You are an Agronomic AI assistant developed by Aryashakti.
            You help farmers diagnose crop diseases using the provided image.

            Follow strict rules:
            1. Identify crop.
            2. Analyze symptoms.
            3. Diagnose disease.
            4. Provide advisory.
            5. Respond ONLY in valid JSON.
            6. Use English for all values.
            7. Keep crop_name and disease_name in standard English agricultural terminology.
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

        payload = {
            "model": "gpt-4.1",
            "text": {
                "format": {
                    "type": "json_object"
                }
                },
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": system_prompt
                        },
                        {
                            "type": "input_image",
                            "image_url": image_url
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            f"{self.base_url}/responses",
            headers=self.headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            error_message = None
            try:
                error_data = response.json()
                error_message = (
                    f"OpenAI Error ({response.status_code}): "
                    f"{error_data.get('error', {}).get('message')}"
                )
                self._send_openai_error_email(error_message)
            except Exception:
                
                error_message = (
                    f"OpenAI Error ({response.status_code}): {response.text}"
                )
                self._send_openai_error_email(error_message)
                raise Exception(error_message)
                
        return response.json()


    def translate_json(
        self,
        data: dict,
        target_language_code: str = "hi"
    ):
        """
        Translate a structured JSON object into a regional language.

        Keeps JSON structure intact.
        Returns translated JSON.
        """

        prompt = f"""
        You are an agricultural translation assistant.

        Translate all farmer-facing text into language code: {target_language_code}.

        Rules:
        1. Return ONLY valid JSON.
        2. Preserve the exact JSON structure.
        3. Do NOT remove or add keys.
        4. Keep scientific names unchanged.
        5. Keep disease_name and crop_name in English.
        6. Translate diagnosis and advisory fields.
        7. If a value is not translatable, leave it unchanged.

        JSON:
        {json.dumps(data, ensure_ascii=False)}
        """

        payload = {
            "model": "gpt-4.1-mini",
            "text": {
                "format": {
                    "type": "json_object"
                }
            },
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            f"{self.base_url}/responses",
            headers=self.headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            try:
                error = response.json()
                raise Exception(
                    error.get("error", {}).get("message")
                )
            except:
                raise Exception(response.text)

        result = response.json()

        output_text = result["output"][0]["content"][0]["text"]

        return json.loads(output_text)
            
