from django.db import models
from django.utils.text import slugify

from app_farm.utils.constants import CUSTOM_FORM_TYPES, CUSTOM_FORM_FIELDS_TYPES

# Create your models here.
class BaseModel(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True,verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True,db_index=True,verbose_name='updated at')

    class Meta:
        abstract = True


class Permission(BaseModel):
    name = models.CharField(max_length=200,unique=True)
    slug=models.SlugField(editable=False,unique=True)
    description = models.CharField(max_length=500,blank=True,null=True)
    api = models.CharField(max_length=300,blank=True,null=True)

    def save(self, *args, **kwargs):
        slug = self.name

        # Append the API type(GET/POST) in slug
        if self.api != None and self.api != '':
            temp = self.api.split('##')
            if len(temp) == 2:
                slug = slug + '-' + temp[1]

        self.slug = slugify(slug)
        super(Permission, self).save(*args, **kwargs)


    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.name
    
class Country(BaseModel):
    name = models.CharField(max_length=200,unique=True)
    code = models.CharField(max_length=5,unique=True)
    mobile_code = models.CharField(max_length=5,unique=True)
    phone_len = models.IntegerField(default=10)
    image = models.ImageField(null=True,blank=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.name
    
class WhiteListedMobile(BaseModel):
    name = models.CharField(max_length=200,null=True,blank=True)
    phone = models.BigIntegerField(unique=True)
    country = models.ForeignKey(Country,on_delete=models.CASCADE,default=1)
    otp = models.IntegerField(default=123456)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return str(self.phone)
    
class CustomForm(BaseModel):
    """
    Custom Form model to make a centralized dynamic forms:
    1) name: Char type field to store the Form name.
    2) type: Enum type field to store value to determine that this form belongs to which module.
    """
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=100,choices=CUSTOM_FORM_TYPES,blank=True)
    image_url = models.ImageField(max_length=300,null=True,blank=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return str(self.name)
    
class CustomFormField(BaseModel):
    """
    Custom Form Fields model to make a centralized dynamic forms fields:
    1) custom_form: ForeignKey type field to Form-Id to which this field belongs.
    2) name: Char type field to store the Field name.
    3) type: Enum type field to store value to determine that this field is of which type.
    4) field_possible_value: Text type field to store the option values if field type is optional.
    5) is_required: Boolean, Store whether the field is required.
    6) status: Boolean, Whther this field is being used or not.
    7) order: Int, Determines the order of fields in list.
    """
    custom_form = models.ForeignKey(to=CustomForm,on_delete=models.CASCADE,related_name='custom_form_fields')
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=200,choices=CUSTOM_FORM_FIELDS_TYPES,blank=True)
    field_possible_value = models.TextField(blank=True,null=True)
    is_required = models.BooleanField(default=True,null=True)
    status = models.BooleanField(default=True)
    order = models.IntegerField(default=99)
    
    def __str__(self) -> str:
        return self.name+ ' - ' +self.custom_form.name

    def __unicode__(self):
        return self.id


class CustomFormParent(BaseModel):
    custom_form_parent= models.ForeignKey(to=CustomForm, on_delete=models.CASCADE,related_name="custom_form_custom_parent")
    custom_form_child=models.ForeignKey(to=CustomForm,on_delete=models.CASCADE,related_name='custom_form_custom_child')
    
    