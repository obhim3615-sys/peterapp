from django.shortcuts import render
from rest_framework.views import APIView
from app_farm.authentication import CustomTokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from . import validator
from app_farm.utils import constants,response as res
from rest_framework import status
import json
from .models import *
from .serializer import *
from .validator import *
from app_farm.models import user
from cms.models import Setting
from app_farm.utils import helper
from app_farm.utils.response import req_response
from app_farm.serializers import FarmerSerializer

# import matplotlib as mpl

# # mpl.rcParams['text.color'] = "#fff"
# mpl.rcParams['xtick.color'] = "#fff"

# Create your views here.


class GetAllCertification(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
        data= Certification.objects.order_by('order_value').all()
        if data:
            data = CertificationSerializer(data,many=True)
            if data:
                data=data.data

        result= res.SuccRes()
        result['data']=data
        
        return Response(result,result['status_code'])


class AddCeritfication(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request):
        data= request.POST

        validator=FarmerCertificationSerializer(data=data)
        if not validator.is_valid():
            result = res.ErrRes()
            result['message'] = constants.INVALID_BODY
            result['error_code'] = "RAV-CADP-03"
            result['data'] = validator.errors
            return Response(result, status=result['status_code'])
        try:
            farmer= user.objects.filter(id=data['farmer_id']).get()
        except user.DoesNotExist:
            response= res.ErrRes()
            response['status_code']=status.HTTP_404_NOT_FOUND
            response['message']="Farmer not found"
            response['error_code']="RAV-CADP-02"
            return Response(response,status=response['status_code'])
        
        try:
            certification= Certification.objects.filter(id=data['certification_id']).get()
        except user.DoesNotExist:
            response= res.ErrRes()
            response['status_code']=status.HTTP_404_NOT_FOUND
            response['message']="Farmer not found"
            response['error_code']="RAV-CADP-02"
            return Response(response,status=response['status_code'])
        

        file= request.FILES.get('file')
        if(file):
            file_url=helper.image_upload(file)
        else:
            result = res.ErrRes()
            result['message'] = "File not found "
            result['error_code'] = "RAV-CADP-03"
            result['data'] ={}
            return Response(result,result['status_code'])
        
        FarmerCertification.objects.create(
            farmer=farmer,
            certification=certification,
            issued_date=data['issued_date'],
            expiry_date=data['expiry_date'],
            file_url=file_url,
            authority_name=data['authority_name'],
            authority_logo=data['authority_logo'],
        )

        response=res.SuccRes()
        response['status_code']=status.HTTP_201_CREATED
        response['message']="Certification Added"

        return Response(response,response['status_code'])
        
        
        

class GetCertificationOfFarmer(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request,farmerid):
        data=Certification.objects.filter(certification_data__farmer_id=farmerid,status=True).order_by('order_value').all()
        
        if data:        
            data=CertificationSerializer(data,many=True,context={"farmerid":farmerid,'request':request})
            if data:
                data=data.data
        response=res.SuccRes()
        response['data']=data
        return Response(response,response['status_code'])
    



class GetUserBadge(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request,farmerid):
        farmer=user.objects.filter(id=farmerid).get()
        
        data=FarmerBadge.objects.filter(farmer_id=farmerid).all()
        if data:
            data=FarmerBadgeSerializer(data,many=True)
            if data:
                data=data.data
        
        farmer=FarmerSerializer(farmer).data
        url=Setting.objects.getKey('BASE_URL')
        response=res.SuccRes()
        response['data']={"badge":data,"farmer_data":farmer,"user_url":url.value+str(farmer['mobile_number'])+"/"}
        return Response(response,response['status_code'])
    

# class GetGraph(APIView):
#     def get(self,request,farmid,certificateid):
#         value=ValueType.objects.filter(certificate=certificateid).all()
#         graphic=[]
#         flag=0
#         for type_data in value:
#             typeid=type_data.id
#             enddate = date.today()
#             startdate = enddate - timedelta(days=120)
#             data=GraphHistory.objects.filter(farm_id=farmid,type_id=typeid,date__range=[startdate, enddate]).all()
            
#             if data:
#                 data=GraphHistorySerializer(data,many=True)
#                 if data:     
#                     flag=1               
#                     data=data.data                   
#                     x=[]
#                     y=[]
#                     for i in data:
#                         x.append(i['date'])
#                         y.append(round(float(i['value']),2))
                   
#                     #sns.set_style("whitegrid")
#                     plt.plot(x, y,color=type_data.color,lw=3,label=type_data.name)
            
#         if flag:
#             plt.xticks(rotation=45,fontsize='xx-small')
#             ax =plt.gca()
#             ax.spines['bottom'].set_color('#fff')
#             ax.spines['top'].set_color('#fff')
#             ax.spines['left'].set_color('#fff')
#             ax.spines['right'].set_color('#fff')
#             ax.tick_params(colors='#fff', which='both') 
#             buffer = BytesIO()
#             plt.legend()
#             plt.savefig(buffer, format='png', transparent=True)
#             buffer.seek(0)
#             image_png = buffer.getvalue()
#             buffer.truncate(0)
#             buffer.close()
#             graphic.append(base64.b64encode(image_png).decode('utf-8'))
#             plt.clf()
#         return render(request, 'graphic.html',{'graphic':graphic})
        #return req_response("Chart data",True,'',status.HTTP_200_OK,data)


class UploadCSVGraph(APIView):
    def get(self,request):
        data={}
        finaldata={}

        for i in range(208,208+208):
            data= GraphHistory.objects.filter(id=i).get()
            data.type_id=7
            data.save()
        # opening the CSV file
        # with open('static/Prakshepdata/Abiotic Damage.csv', mode ='r')as file:
        
        # # reading the CSV file
        #     csvFile = csv.reader(file)
        
        #     # displaying the contents of the CSV file
        #     count=0
        #     for i in csvFile:
        #         count=count+1
        #         if count>1:
        #             print(type(i[1]))
        #             data={
        #                 "farm_id":898,
        #                 "type_id":5,
        #                 "value":round(float(i[1]),2),
        #                 "date":i[0].split(" ")[0]
        #             }
        #             print(data)

        #             GraphHistory.objects.create(
        #                 farm_id=898,
        #                 type_id=5,
        #                 value=i[1],
        #                 date=i[0].split(" ")[0]
        #             )
            

        
        # with open('static/Prakshepdata/Abiotic Stress.csv', mode ='r')as file:
        
        # # reading the CSV file
        #     csvFile = csv.reader(file)
        #     count=0
        #     # displaying the contents of the CSV file
        #     for i in csvFile:
        #         count=count+1
        #         if count>1:
        #             data={
        #                 "farm_id":898,
        #                 "type_id":5,
        #                 "value":round(float(i[1]),2),
        #                 "date":i[0].split(" ")[0]
        #             }
        #             print(data)
        #             GraphHistory.objects.create(
        #                 farm_id=898,
        #                 type_id=5,
        #                 value=i[1],
        #                 date=i[0].split(" ")[0]
        #             )
            

        
        # with open('static/Prakshepdata/Biotic stress.csv', mode ='r')as file:
        
        # # reading the CSV file
        #     csvFile = csv.reader(file)
        #     count=0
        #     # displaying the contents of the CSV file
        #     for i in csvFile:
        #         count=count+1
        #         if count>1:
        #             data={
        #                 "farm_id":898,
        #                 "type_id":6,
        #                 "value":round(float(i[1]),2),
        #                 "date":i[0].split(" ")[0]
        #             }
        #             print(data)
        #             GraphHistory.objects.create(
        #                 farm_id=898,
        #                 type_id=6,
        #                 value=i[1],
        #                 date=i[0].split(" ")[0]
        #             )

        
        # with open('static/Prakshepdata/Nutrient Data.csv', mode ='r')as file:
        
        # # reading the CSV file
        #     csvFile = csv.reader(file)
        #     count=0

        #     # displaying the contents of the CSV file
        #     for i in csvFile:
        #         count=count+1
        #         if count>1:
        #             data={
        #                 "farm_id":898,
        #                 "type_id":3,
        #                 "value":round(float(i[1]),2),
        #                 "date":i[0].split(" ")[0]
        #             }
        #             print(data)
        #             GraphHistory.objects.create(
        #                 farm_id=898,
        #                 type_id=4,
        #                 value=i[1],
        #                 date=i[0].split(" ")[0]
        #             )



        return Response({},200)


class ComingSoon(APIView):
    def get(self,request,phonenumber):
        return render(request, 'comingsoon.html')
