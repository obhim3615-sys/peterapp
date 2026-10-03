from django.db import models
try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField

from verification.models import BaseModel
from app_farm.models import language_master
from app_farm.utils.constants import SUB_SECTION_TYPES,VALUE_TYPES

class PageManager(models.Manager):
    pass

# Create your models here.
class Page(BaseModel):
    objects = PageManager()

    name = models.CharField(max_length=100)
    order = models.IntegerField()
    language = models.ForeignKey(language_master, on_delete=models.CASCADE,default=1)
    
    def __unicode__(self):
        return self.id
    
    def __str__(self):
        return str(self.name) + ' - ' + str(self.language)
    

class SectionManager(models.Manager):
    pass

class Section(BaseModel):
    objects = SectionManager()

    name = models.CharField(max_length=100)
    order = models.IntegerField()
    type = models.CharField(max_length=50,choices=SUB_SECTION_TYPES,default='Grid')
    page = models.ForeignKey(to=Page, on_delete=models.CASCADE, related_name='sections')
    countries = models.ManyToManyField(to='core.Country',related_name='section_countries')
    
    def __unicode__(self):
        return self.id
    
    def __str__(self):
        return str(self.name) + ' - ' + str(self.page)
    

class SubSectionManager(models.Manager):
    pass

class SubSection(BaseModel):
    objects = SubSectionManager()

    name = models.CharField(max_length=300)
    image_url = models.ImageField(null=True,blank=True)
    image_text = models.CharField(max_length=300,null=True,blank=True)
    is_iframe = models.BooleanField(default=False)
    order = models.IntegerField()
    url = models.CharField(max_length=300,null=True,blank=True)
    section = models.ForeignKey(to=Section, on_delete=models.CASCADE, related_name='sub_sections')
    countries = models.ManyToManyField(to='core.Country',related_name='subsection_countries')
    
    def __unicode__(self):
        return self.id
    
    def __str__(self):
        return str(self.name)

class LanguageContentsManager(models.Manager):
    pass

class LanguageContent(BaseModel):
    objects = LanguageContentsManager()

    language = models.OneToOneField(language_master, on_delete=models.CASCADE)
    content = JSONField()
    crop_content = JSONField()
    
    def __unicode__(self):
        return self.id
    
    def __str__(self):
        return str(self.language)

class SettingManager(models.Manager):
    def getKey(self,key):
        return  self.filter(key=key).get()

class Setting(models.Model):
    id = models.AutoField(primary_key=True,unique=True) 
    key=models.CharField(max_length=200) 
    value=models.CharField(max_length=1000)
    type=models.CharField(max_length=200,choices=VALUE_TYPES,default='String')
    country = models.ManyToManyField(to='core.Country',related_name='countries',blank=True)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True,verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True,db_index=True,verbose_name='updated at')
    objects=SettingManager()

    def __str__(self) -> str:
        return self.key+" : "+self.value