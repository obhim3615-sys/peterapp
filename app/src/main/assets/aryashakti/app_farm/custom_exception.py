from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        if 'detail' in response.data.keys():
            response.data['message']=response.data['detail']
            del response.data['detail']
        response.data['status'] = False
        response.data['status_code']= response.status_code
        response.data['error_code']= 'ACECEH01'


    return response