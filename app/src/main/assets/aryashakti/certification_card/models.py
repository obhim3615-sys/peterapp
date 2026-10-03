from django.db import models
from verification.models import BaseModel
from app_farm.models import user,farm
try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField
# Create your models here.
# Create your models here.

class Certification(BaseModel): #Card
    name=models.CharField(max_length=200)
    color=models.CharField(max_length=100,null=True,blank=True)
    background=models.ImageField(blank=True,null=True)
    status=models.BooleanField(default=True)
    order_value=models.IntegerField(default=99)

    def __str__(self) -> str:
        return self.name

class FarmerCertification(BaseModel):
    farmer=models.ForeignKey(to=user, on_delete=models.CASCADE, related_name='farmer_cerrtification')
    certification=models.ForeignKey(to=Certification,on_delete=models.CASCADE,related_name='certification_data')
    file_url=models.ImageField()
    authority_name=models.CharField(max_length=200,null=True,blank=True)
    authority_logo=models.CharField(max_length=200,null=True,blank=True)
    expiry_date=models.DateField()
    issued_date=models.DateField()
    is_approved=models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.farmer.full_name+" / "+self.certification.name



class Score(BaseModel):
    name=models.CharField(max_length=200)
    icon=models.ImageField(null=True,blank=True)
    information=models.CharField(max_length=200,null=True,blank=True)
    status=models.BooleanField(default=True)    

    def __str__(self) -> str:
        return self.name
    

def getdefault():
    return {"big":"","small":""}
class ScoreFarmer(BaseModel):
    farmer=models.ForeignKey(to=user,on_delete=models.CASCADE,related_name='score_farmer')
    farmer_certification=models.ForeignKey(to=FarmerCertification,on_delete=models.CASCADE,related_name="certification_farmer_score")
    score=models.ForeignKey(to=Score,on_delete=models.CASCADE,related_name='score_data')
    value=JSONField(default=getdefault)
    
    def __str__(self) -> str:
        return self.farmer.full_name+" / "+self.score.name+" / "+self.farmer_certification.certification.name


class ScoreGeneralFarmer(BaseModel):
    farmer=models.ForeignKey(to=user,on_delete=models.CASCADE,related_name='score_general_farmer')
    value=JSONField(default=getdefault)
    
    def __str__(self) -> str:
        return self.farmer.full_name


class Badge(BaseModel):
    name=models.CharField(max_length=200)
    icon=models.ImageField()
    staus= models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

class FarmerBadge(BaseModel):
    farmer=models.ForeignKey(to=user,on_delete=models.CASCADE,related_name='farmer_for_badge')
    badge=models.ForeignKey(to=Badge,on_delete=models.CASCADE,related_name='farmer_badge')

    def __str__(self) -> str:
        return self.farmer.full_name+" / "+self.badge.name


class ValueType(BaseModel):
    name=models.CharField(max_length=200)
    color=models.CharField(max_length=10,blank=True,null=True)
    certificate= models.ForeignKey(to=Certification,on_delete=models.CASCADE,related_name="value_type_certificate")

    def __str__(self) -> str:
        return self.name

class GraphHistory(BaseModel):
    farm= models.ForeignKey(to=farm,on_delete=models.CASCADE,related_name="farm_graph_history")
    type=models.ForeignKey(to=ValueType,on_delete=models.CASCADE,related_name="type_graph_history")
    value=models.DecimalField(max_digits=10,decimal_places=4)
    date=models.DateField()

    def __str__(self) -> str:
        return self.farm.user.full_name+" / "+self.type.name
    
    

