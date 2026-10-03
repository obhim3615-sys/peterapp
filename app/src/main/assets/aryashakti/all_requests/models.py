from django.db import models
from verification.models import BaseModel
from app_farm.models import user, organizations

TYPES = [("New FPO Request", "New FPO Request"),("Farmer to FPO Request", "Farmer to FPO Request")]

class RequestsManager(models.Manager):
    pass

# Create your models here.
class Requests(BaseModel):
    objects = RequestsManager()

    type = models.CharField(max_length=50,choices=TYPES,blank=True,null=True)
    user = models.ForeignKey(to=user, on_delete=models.CASCADE)
    organization = models.ForeignKey(to=organizations, on_delete=models.CASCADE,null=True)
    status = models.IntegerField(default=2)
    org_name = models.CharField(max_length=200,blank=True,null=True)
    org_no = models.CharField(max_length=15,blank=True,null=True)
    
    def __unicode__(self):
        return self.id
    
    def __str__(self):
        return str(self.id) + ' ' + str(self.user)
    