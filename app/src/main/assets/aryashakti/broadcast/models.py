from django.db import models

from core.models import BaseModel
from app_farm.models import language_master,organizations,user
from app_farm.utils.constants import SMS_TEMPLATE_FIELDS_TYPES

# Create your models here.
class SmsTemplate(BaseModel):
    name = models.CharField(max_length=200)
    image = models.ImageField(null=True,blank=True)
    emoji = models.CharField(max_length=10, null=True, blank=True)
    order = models.IntegerField(default=99)
    template_id = models.CharField(max_length=25)
    msg = models.TextField(max_length=500)
    description = models.TextField(max_length=500, blank=True, default='')
    language = models.ForeignKey(language_master,on_delete=models.CASCADE,default=1)
    doms_id =models.IntegerField(null=True,blank=True)
    def __str__(self) -> str:
        return self.name + '-' + self.language.name
    

class SmsTemplateField(BaseModel):
    sms_template = models.ForeignKey(to=SmsTemplate,on_delete=models.CASCADE,related_name='template_fields')
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=200,choices=SMS_TEMPLATE_FIELDS_TYPES,null=True,blank=True)
    field_possible_value = models.TextField(null=True,blank=True)
    is_required = models.BooleanField(default=True)
    status = models.BooleanField(default=True)
    order = models.IntegerField(default=99)
    key = models.CharField(max_length=200,null=True,blank=True)

    def __str__(self) -> str:
        return self.sms_template.name+" / "+self.name

class CommunitiesShare(BaseModel):
    image=models.ImageField(max_length=300)
    organization=models.ForeignKey(to=organizations,on_delete=models.CASCADE,related_name='community_organization',null=True,blank=True)
    status=models.BooleanField(default=True)



class NotificationLog(BaseModel):
    """
    Tracks SMS and Firebase push notifications sent through the system.
    """
    

    sender = models.ForeignKey(
        user,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_notifications"
    )
    receiver = models.ForeignKey(
        user,
        on_delete=models.SET_NULL,
        null=True,
        related_name="received_notifications"
    )
    sms_template = models.ForeignKey(to=SmsTemplate,related_name="smstemplate_notificationlog",on_delete=models.SET_NULL,null=True)
    org_name = models.ForeignKey(to=organizations,related_name="organization_templatelog",on_delete=models.SET_NULL,null=True,blank=True)
    receiver_phone=models.CharField(max_length=20)
    status = models.CharField(max_length=50, default="pending")  # success, failed, pending
    response = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.sms_template.name.upper()} → {self.receiver_phone or self.receiver} ({self.status})"