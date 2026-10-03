from rest_framework import status
from rest_framework.response import Response
import time, logging

def ErrRes():
    return {
        "status_code": status.HTTP_400_BAD_REQUEST,
        "status": False,        
        "message": "",
        "error_code": "",
        "request_id": "",
    }

def SuccRes():
    return {        
        "status_code": status.HTTP_200_OK,
        "status": True,
        "message": "",
    }

def SuccPageRes():
    return {
        "status_code": status.HTTP_200_OK,
        "status": True,
        "total_pages": 0,
        "current_page": 0,
        "records": 0,
        "records_per_page": 0,
    }

def req_response(msg, status, err_code, status_code, data=None, err_msg='', page=False):
    """
    Function to get standard response object.
    (msg, status, err_code, status_code, data, err_msg)
    """
    response = {
        "status_code": status_code,
        "status": status,
        "message": msg
    }
    if not status:
        response['error_code'] = err_code
        response['request_id'] = str(int(time.time()*1000))
        response['error_msg'] = str(err_msg)
        #logging.error('Exception: ' + str(err_msg))

    if data is not None:
        response['data'] = data

    return Response(response, status = status_code)
