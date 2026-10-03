from django.db import models
from verification.models import BaseModel
from app_farm.models import user

# Create your models here.
class OnemoneyConsent(BaseModel):
    user = models.ForeignKey(to=user, on_delete=models.CASCADE)
    status = models.CharField(max_length=200)
    consent_handle = models.CharField(max_length=200)
    consent_id = models.CharField(max_length=200, null=True,blank=True)
    vua = models.CharField(max_length=200, null=True,blank=True)
    timestamp = models.DateTimeField(null=True,blank=True)
    
    def __unicode__(self):
        return self.id
    
    def __str__(self):
        return str(self.consent_handle) + ' ' + str(self.user)

class BankStatementVerifcation(BaseModel):
    consent = models.ForeignKey(to=OnemoneyConsent, on_delete=models.CASCADE, null=True,blank=True)
    linkReferenceNumber = models.CharField(max_length=200,null=True,blank=True)
    maskedAccountNumber = models.CharField(max_length=20)
    fiType = models.CharField(max_length=20)
    bank = models.CharField(max_length=200)
    startDate = models.DateField()
    endDate = models.DateField()
    bank_statement = models.TextField()
