from django.db import models
from verification.models import BaseModel
from app_farm.models import user as userModel,organizations
from app_farm.utils.constants import SURVEY_STATUS,SURVEY_STATUS_USER
from django.db.models import Q, Count, F, Subquery,OuterRef,Exists,IntegerField,ExpressionWrapper

# from ckeditor.fields import RichTextField
from django_ckeditor_5.fields import CKEditor5Field
try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField

from django.db.models.functions import Cast
# Create your models here.

# Create your models here.



    
class SurveyType(BaseModel):
    name=models.CharField(max_length=200)

    def __str__(self) -> str:
        return self.name

class SurveyManager(models.Manager):
    def get_survey_organization(self, organization):
        self.queryset= self.filter(organization_survey__id=organization)
        return self
    
    def get_available_survey(self, user_id,organization):
        # Here, print the IDs that should be excluded
        exclusion_ids = UserSurvey.objects.filter(user_id=user_id, status='accepted').values('survey_id')


        # Your completed_counts subquery
        completed_counts_subquery = UserSurvey.objects.filter(
             survey=OuterRef('pk'),status='accepted'
        ).values('survey').annotate(
            completed_count=Count('id')
        ).values('completed_count')[:1]

        # Check if there are any records in UserSurvey for the survey
        user_survey_exists = UserSurvey.objects.filter(survey=OuterRef('pk')).values('id')[:1]

        queryset = self.filter(
            Q(is_multiple_allowed=True) | ~Q(id__in=exclusion_ids),            
            Q( total_allowed__gt=ExpressionWrapper(
                Subquery(completed_counts_subquery),
                output_field=IntegerField()
            ))| ~Q(id__in=Subquery(user_survey_exists)),
             organization_survey__id=organization,
            status='active',
        ).distinct()
        
        return queryset

class Survey(BaseModel):
    name= models.CharField(max_length=200, )
    color= models.CharField(max_length=200, null=True,blank=True )
    link_form=models.CharField(max_length=200,null=True,blank=True)
    created_by= models.CharField(max_length=200)
    price=models.DecimalField(max_digits=10,decimal_places=2,default=0.0)
    type=models.ForeignKey(to=SurveyType,on_delete=models.CASCADE,related_name="survey_type",blank=True,null=True)
    started_at=models.DateField()
    valid_till= models.DateField()
    total_allowed=models.IntegerField(default=0)
    description=CKEditor5Field(null=True, blank=True )
    status=models.CharField(max_length=200,choices=SURVEY_STATUS,default='active')
    video_link=models.CharField(max_length=200,blank=True,null=True)
    is_multiple_allowed=models.BooleanField(default=False)
    organization_survey = models.ManyToManyField(organizations, related_name='survey_organization')
    objects=SurveyManager()

    def __str__(self) -> str:
        return self.name


class SurveyFields(BaseModel):
    survey=models.ForeignKey(to=Survey,on_delete=models.CASCADE,related_name="survey_surveyfields")
    question=models.CharField(max_length=500)
    name=models.CharField(max_length=200)
    type=models.CharField(max_length=200,choices=[("string","String"),("int","Integer"),("file","File"),("optional","Optional"),("date","Date")])
    field_possible_value=models.TextField(null=True,blank=True)
    is_required=models.BooleanField(default=True)
    status= models.BooleanField(default=True)

    def field_possible_value_split(self):
        return self.field_possible_value.split(',')

class UserSurveyManager(models.Manager):
    def get_user_surveys(self,user_id):
        return self.filter(user_id=user_id)
    


class UserSurvey(BaseModel):
    user=models.ForeignKey(to=userModel,on_delete=models.CASCADE,related_name='user_survey')
    survey=models.ForeignKey(to=Survey,on_delete=models.CASCADE,related_name='survey_user')
    response=JSONField(null=True,blank=True)
    status=models.CharField(max_length=200,choices=SURVEY_STATUS_USER,default='pending')
    latitude = models.DecimalField(decimal_places=8,max_digits=16,blank = True,null=True)
    longitude = models.DecimalField(decimal_places=8,max_digits=16,blank = True,null=True)
    objects=UserSurveyManager()
    def __str__(self) -> str:
        return self.user.full_name+" / "+self.survey.name
