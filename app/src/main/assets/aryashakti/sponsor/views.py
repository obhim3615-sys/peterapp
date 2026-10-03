from django.shortcuts import render
from rest_framework.views import APIView
from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from app_farm.serializers import FarmerSerializer,orgSerializer,farmlistSerializer
from app_farm.utils import constants,response as res
from rest_framework import status
from app_farm.models import user as userModel,organizations,farm
from rest_framework.pagination import PageNumberPagination

# Create your views here.


class GetSponsoredFarmer(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 
    # number of items per page by default
    page_size = 50
    # max number of items per page
    max_page_size = 100
    model=farm 

    def get_queryset(self):
        queryset = farm.objects.get_user_by_role("Farmer").filter(user__user_subscription__sponsored_by_id=self.request.user.id)
        return queryset


    def get(self,request):
        queryset = self.get_queryset()
        page =  self.paginate_queryset(queryset,request)
        sponsored=None
        if page:            
            sponsored=farmlistSerializer(page,many=True).data
            sponsored=self.get_paginated_response(sponsored).data

        return res.req_response("Data found",True,"",status.HTTP_200_OK,sponsored)


class GetOrganizationFarmer(APIView,PageNumberPagination):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated] 
    # number of items per page by default
    page_size = 50
    # max number of items per page
    max_page_size = 100
    model=organizations 

    def get_queryset(self):
        queryset =  organizations.objects.filter(
            organization__user_subscription__sponsored_by_id=self.request.user.id
        ).distinct()
        return queryset


    def get(self,request):
        queryset = self.get_queryset()
        sponsored =None
        page=self.paginate_queryset(queryset,request)

        if page:
            sponsored=orgSerializer(page,many=True).data
            sponsored=self.get_paginated_response(sponsored).data
        return res.req_response("Data found",True,"",status.HTTP_200_OK,sponsored)


