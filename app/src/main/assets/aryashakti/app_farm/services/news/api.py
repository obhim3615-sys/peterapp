from rest_framework.views import APIView
from app_farm import models
from app_farm.utils import constants,helper,response as res
from app_farm import serializers
from rest_framework.response import Response
from rest_framework import status
import math 

class news_list(APIView):
    @classmethod
    def get_extra_actions(cls):
        return []
    def get(self,request):
        try:
            page_number = request.GET.get("page_number")
            key = request.GET.get("secret_key")

            fields = ['id','title','title_telugu','source','source_telugu','timestamp','notes','url_telugu','thumbnail_url']

            qs = models.tb_application_access.objects.filter(key=key)
            serializer = serializers.key_serializer(qs, many=True)

            if len(serializer.data) != 0:
                result = res.SuccPageRes()
                result['records_per_page'] = constants.DEFAULT_PAGE_RECORDS
                
                start, end, current_page = helper.get_pagination_start_end(page_number, result['records_per_page'])

                data = models.news.objects.filter(status='Active').order_by('-timestamp').values(*fields)[start:end]
                tot = models.news.objects.filter(status='Active').values('id').count()

                result['records'] = len(data)
                result['current_page'] = current_page
                if result['records'] > 0:
                    tot=math.ceil(tot/(result['records_per_page']))
                    result['total_pages'] = tot
                    result['message'] = constants.SUCCESS
                    result['data'] = data
                else:
                    result['status_code'] =status.HTTP_202_ACCEPTED
                    result['status'] = False
                    result['message'] = constants.NO_CONTENT 
                    result['data'] = []                   
                return Response(result, status=result['status_code'])
            else:
                result = res.ErrRes()
                result['status_code'] =status.HTTP_400_BAD_REQUEST
                result['message'] = constants.INVALID_KEY
                result['error_code'] = "AFSNA-NLGET-01"
                return Response(result, status=result['status_code'])
        except:
            result = res.ErrRes()
            result['status_code'] =status.HTTP_500_INTERNAL_SERVER_ERROR
            result['message'] = constants.ERROR
            result['error_code'] = "AFSNA-NLGET-02"
            return Response(result, status=result['status_code'])