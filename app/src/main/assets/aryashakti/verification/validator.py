from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

class PANVerification(serializers.Serializer):
    pan_number = serializers.ListField(child=serializers.CharField(), required=True)

class EadharVerification(serializers.Serializer):
    req_id=serializers.CharField(required=True)
    verification_id=serializers.IntegerField(required=True)

    
class PANSaveVerification(serializers.Serializer):
    service= serializers.CharField(required=True)
    itemId= serializers.CharField(required=True)
    task= serializers.CharField(required=True)
    essentials= serializers.JSONField(required=True)
    accessToken= serializers.CharField(required=True)
    id= serializers.CharField(required=True)
    response= serializers.JSONField(required=True)

    '''
    {
        "service": "Identity",
        "itemId": "642560b959affed4b6518e4f",
        "task": "fetch",
        "essentials": {
            "name": "Nitin Tiwari",
            "number": "BFYPT4747R",
            "fuzzy": "true",
            "instance": {}
        },
        "accessToken": "yx7b0om6qyi7vm339kzapll29v4d569",
        "id": "642560b959affed4b6518e51",
        "response": {
            "number": "BFYPT4747R",
            "id": 104,
            "name": "Nitin Tiwari",
            "fuzzy": "true",
            "instance": {
                "id": "642560b959affed4b6518e4f",
                "callbackUrl": "https://www.w3schools.com"
            },
            "result": {
                "number": "BFYPT4747R",
                "name": "NITIN TIWARI",
                "fatherName": "JITENDRA TIWARI",
                "dob": ""
            }
        }
    }
    '''


class GSTSaveVerification(serializers.Serializer):
    gstin=serializers.CharField(required=True)
    verification_id=serializers.IntegerField(required=True)


class AdharOTPVerification(serializers.Serializer):
    adhar_number=serializers.CharField(required=True)

class AdharOTPValidationVerification(serializers.Serializer):
    otp=serializers.CharField(required=True)
    request_id=serializers.CharField(required=True)

    
class AdharImageValidationVerification(serializers.Serializer):
    front_aadhaar = serializers.ImageField(allow_empty_file=False)
    back_aadhaar = serializers.ImageField(allow_empty_file=False)
