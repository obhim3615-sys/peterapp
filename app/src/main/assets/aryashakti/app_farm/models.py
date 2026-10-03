from django.db import models
from django.contrib.gis.db import models as models2
from rest_framework.reverse import reverse as api_reverse
import uuid
import os
import re
from os import path
from binascii import hexlify
from django.contrib.auth.hashers import make_password

from django.contrib.gis.db import models
from django.contrib.postgres.fields import ArrayField
# from django.contrib.postgres.fields import JSONField
# django.db.models.JSONField
try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField
import jwt
from .utils.constants import GENDERS,USER_DESIGNATIONS
# from ckeditor.fields import RichTextField
from django_ckeditor_5.fields import CKEditor5Field
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.apps import apps
from django.utils import timezone
from django.utils.timezone import is_aware, make_naive

def createHash():
    """This function generate 10 character long hash"""
    return uuid.uuid4().hex[:30]

LAND_SIZE_UNIT_TELEGU = [("एकड़", "एकड़"),("हैक्टर", "हैक्टर")]
LAND_SIZE_UNIT = [("Acre", "Acre"),("Hectare", "Hectare")]
STATUS = [("Active", "Active"),("Inactive", "Inactive"),("Deleted", "Deleted")]
PRODUCT_CATEGORY = [("Chemical","Chemical"),("Seed","Seed"),("Nutrition","Nutrition"),("Machine","Machine")]
PRODUCT_SUBCATEGORY = [("Insecticide","Insecticide"),("Fungicide","Fungicide"),("Herbicide","Herbicide"),("Others","Others"),("FieldCrop","FieldCrop"),("Vegetable","vegetable"),("Fruits","Fruits"),("Promoter","Promoter"),("Regulator","Regulator"),("Micronutrient","Micronutrient"),("Tractor","Tractor"),("Sprayer","Sprayer"),("Electronics","Electronics")]
PAGES = [("Home","Home"),("Agrimart","Agrimart"),("Social","Social"),("MyFarm","MyFarm")]
ORDER_STATUS = [("Placed","Placed"),("In Transit","In Transit"),("Delivered","Delivered"),("Failed","Failed"),("Accepted","Accepted"),("Rejected","Rejected")]
PACKAGING_UNIT = [("ML","ML"),("KG","KG")]
MEDIA_TYPE = [("Image","Image"),("Video","Video"),("Youtube","Youtube")]
FARMER_TYPE = [("NO_AREA", "No Area"),("MARGINAL", "Marginal"),("SMALL", "Small"),("SEMI_MEDIUM", "Semi Medium"),("MEDIUM", "Medium"),("LARGE", "Large")]

class crop_master(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    crop_name = models.CharField(max_length=100)
    crop_name_telegu = models.CharField(max_length=100,null=True,blank=True)
    crop_unselected_icon_url = models.TextField(blank=True,null=True)
    crop_selected_icon_url = models.TextField(blank=True,null=True)

    def __unicode__(self):
        return self.id
    def __str__(self):
        return self.crop_name

class crop_variety_master(models.Model):
    id = models.AutoField(primary_key=True,unique=True)
    crop_id = models.ForeignKey(crop_master, on_delete=models.CASCADE)
    crop_variety = models.CharField(max_length=100)
    crop_variety_telugu = models.CharField(max_length=100,null=True,blank=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return str(self.crop_variety)

class user_roles(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    role_name = models.CharField(max_length=500)
    admin_rights = models.BooleanField(null=True,blank=True)
    description	= models.CharField(max_length=200,blank=True,null=True)
    image = models.ImageField(upload_to="user_role_icon",blank=True, null=True)
    permissions = models.ManyToManyField('core.Permission', related_name='role_permissions')
    countries = models.ManyToManyField('core.Country', related_name='role_countries')
    show_in_list = models.BooleanField(default=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.role_name
    
class OrgType(models.Model):
    name = models.CharField(max_length=200,unique=True)
    image = models.ImageField(max_length=400,null=True,blank=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.name

def get_initials(name, length=4):
        # Remove spaces and convert to uppercase
        name_no_spaces = name.replace(" ", "").upper()
        # Take the first `length` characters
        return name_no_spaces[:length]

class organizations(models.Model):
    id 	= models.AutoField(primary_key=True,unique=True)
    org_name = models.CharField(max_length=200,unique=True)
    org_type = models.CharField(max_length=200,blank=True,null=True)
    logo = models.CharField(max_length=200,blank=True,null=True)
    number_of_members	= models.IntegerField(blank=True,null=True)
    myplot_company_id = models.CharField(max_length=30,blank=True,null=True)
    company_id = models.CharField(max_length=30,unique=True)
    room_100ms = models.TextField(blank=True,null=True)
    room_hostcode = models.TextField(blank=True,null=True)
    room_guestcode = models.TextField(blank=True,null=True)
    map_layer = models.TextField(blank=True,null=True)
    latitude = models.DecimalField(decimal_places=8,max_digits=16,blank = True,null=True)
    longitude = models.DecimalField(decimal_places=8,max_digits=16,blank = True,null=True)
    zoom = models.DecimalField(decimal_places=4,max_digits=10,blank = True,null=True)
    carousel1 = models.TextField(blank=True,null=True)
    carousel2 = models.TextField(blank=True,null=True)
    carousel3 = models.TextField(blank=True,null=True)
    carousel4 = models.TextField(blank=True,null=True)
    members = models.IntegerField(blank=True,null=True)
    acres = models.DecimalField(decimal_places=4,max_digits=12,blank = True,null=True)
    crops = models.IntegerField(blank=True,null=True)
    cin = models.CharField(max_length=21,blank=True,null=True)
    is_verified = models.BooleanField(default=True)
    pincode = models.IntegerField(null=True,blank=True)
    country = models.TextField(null=True,blank=True)
    state = models.TextField(null=True,blank=True)
    district = models.TextField(null=True,blank=True)
    taluka = models.TextField(null=True,blank=True)
    village = models.TextField(null=True,blank=True)
    share_capital = models.DecimalField(decimal_places=4,max_digits=16,blank=True,null=True)
    paid_capital = models.DecimalField(decimal_places=4,max_digits=16,blank=True,null=True)
    status = models.CharField(max_length=10,choices=STATUS,blank=True,null=True)
    reviewed = models.BooleanField(default=True)
    manual_address = models.CharField(max_length=300,blank=True,null=True)
    fpo_contact_no = models.CharField(max_length=15,blank=True,null=True)
    geometry = models2.GeometryField(srid=4326, null=True, blank=True)
    type_of_org = models.ForeignKey(OrgType, on_delete=models.CASCADE,null=True,blank=True)
    crop_interest = ArrayField(models.CharField(max_length=120),null=True,blank=True)
    crops_interest = models.ManyToManyField(crop_master, related_name='crops_org',blank=True)
    description = models.CharField(max_length=300,blank=True,null=True)
    stress = models.DecimalField(decimal_places=4,max_digits=10,blank = True,null=True)
    damaged = models.DecimalField(decimal_places=4,max_digits=10,blank = True,null=True)
    health = models.DecimalField(decimal_places=4,max_digits=10,blank = True,null=True)
    relationship_manager_name = models.CharField(max_length=500,blank=True,null=True)
    relationship_manager_no = models.CharField(max_length=15,blank=True,null=True)
    turnover = models.IntegerField(blank=True,null=True)    
    active_date = models.DateField(blank=True,null=True)    
    member_associate = models.IntegerField(blank=True,null=True)    
    insurance_tenant_id=models.IntegerField(blank=True,null=True)
    insurance_token=models.TextField(blank=True,null=True)
    send_pop_notifications = models.BooleanField(default=False)
    name_of_bds= models.TextField(null=True,blank=True)
    # New fields for grouping
    group_org = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_organizations'
    )
    is_active = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True,verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True,db_index=True,verbose_name='updated at')


    def get_group_members(self):
        """Returns all orgs that share the same group_org"""
        if self.group_org:
            return self.group_org.child_organizations.all()
        return organizations.objects.none()
    
    
    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.org_name

    def generate_company_id(self):
        """
        Create abbreviation from org_name + ID
        Example: 'Arya Shakti Producer Org' → 'ASPO-00123'
        """
        name = self.org_name.strip()

        # Split into words
        words = re.split(r'\s+', name)

        if len(words) > 1:
            abbr = "".join([w[0].upper() for w in words if w])
        else:
            # If one word, take first 3 letters
            abbr = name[:3].upper()

        # Ensure object has ID first
        if not self.id:
            super().save()  # Saves to create ID

        unique_number = str(self.id).zfill(5)
    
        return f"{abbr}-{unique_number}"
    

    def save(self, *args, **kwargs):
        # Save initially to get ID (for new objects)
        if not self.pk:
            super().save(*args, **kwargs)

        # Generate company_id if not already present
        if not self.company_id:
            self.company_id = self.generate_company_id()

        super().save(*args, **kwargs)
    

    # def save(self, *args, **kwargs):
    #     super(organizations, self).save(*args, **kwargs)
    #     if not self.company_id :
    #         self.company_id= get_initials(self.org_name)+"_"+self.pk
    #         super(organizations, self).save(update_fields=['company_id'])
        



class language_master(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    name = models.CharField(max_length=100)
    google_translate_code = models.CharField(max_length=100,blank=True,null=True)

    def __unicode__(self):
        return self.id
    def __str__(self):
        return self.name

class userManager(models.Manager):
    def get_user_by_id(self,user_id):
        return self.filter(id=user_id).first()
    
    
    def get_all_admin(self,org_id):
        return list(self.filter(organization_id=org_id,user_role__role_name='Admin').values_list('id', flat=True))

    def get_user_by_role(self,role):
        return self.filter(user_role__role_name=role)
class user(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    organization = models.ForeignKey(organizations,related_name="organization",on_delete=models.CASCADE,null=True,blank=True)
    user_role = models.ForeignKey(user_roles, on_delete=models.CASCADE,default=1)
    language_selected = models.ForeignKey(language_master, on_delete=models.CASCADE,default=1)
    admin = models.BooleanField(default=False)
    is_cvrp = models.BooleanField(default=False)
    mobile_number = models.BigIntegerField(unique=True)
    otp_verfied = models.BooleanField(null=True,blank=True)
    full_name = models.TextField(max_length=100,null=True,blank=True)
    full_name_telugu = models.TextField(max_length=100,null=True,blank=True)
    land_size = models.CharField(max_length=100,null=True,blank=True)
    land_size_unit = models.CharField(max_length=100,choices=LAND_SIZE_UNIT,null=True,blank=True)
    land_size_unit_telugu = models.CharField(max_length=100,choices=LAND_SIZE_UNIT_TELEGU,null=True,blank=True)
    crop_interest = ArrayField(models.CharField(max_length=120),null=True,blank=True)
    crops_interest = models.ManyToManyField(crop_master, related_name='crops_user',blank=True)
    address_pincode = models.IntegerField(null=True,blank=True)
    address_country = models.TextField(null=True,blank=True)
    address_state = models.TextField(null=True,blank=True)
    address_district = models.TextField(null=True,blank=True)
    address_taluka = models.TextField(null=True,blank=True)
    address_village = models.TextField(null=True,blank=True)
    bio = models.TextField(null=True,blank=True)
    bio_telugu = models.TextField(null=True,blank=True)
    user_profile_img_file=models.ImageField(upload_to="profile_img",blank=True, null=True)
    user_profile_img = models.TextField(null=True,blank=True,default='https://datasciencesdiag.blob.core.windows.net/myplots/aryashakti/profilephoto/default-profile.jpg')
    installed_app = models.BooleanField(default=False)
    timestamp=models.DateTimeField(auto_now_add=True,blank=True, null=True)
    timestamp_login=models.DateTimeField(blank=True, null=True)
    timestamp_first_login=models.DateTimeField(blank=True, null=True)
    firebase_token = models.TextField(null=True,blank=True)
    email = models.CharField(max_length=100,blank=True,null=True)
    is_active = models.BooleanField(default=True)
    can_edit_org_details = models.BooleanField(default=False,help_text="Designates if the user can update organization details.")
    no_of_plots = models.IntegerField(null=True,blank=True)
    latitude = models.DecimalField(max_digits=16,decimal_places=8,default=0)
    longitude = models.DecimalField(max_digits=16,decimal_places=8,default=0)
    designation = models.CharField(max_length=100,choices=USER_DESIGNATIONS,default='Member')
    gender = models.CharField(max_length=15,choices=GENDERS,default='Male')
    added_by=models.ForeignKey(to="self",on_delete=models.CASCADE,null=True,blank=True,related_name="added_by_user")
    verified_by=models.ForeignKey(to="self",on_delete=models.CASCADE,null=True,blank=True,related_name="verified_by_user")
    description=CKEditor5Field(null=True, blank=True )
    org_name = models.CharField(max_length=200,null=True,blank=True)
    country = models.ForeignKey('core.Country',on_delete=models.CASCADE,default=1)
    is_deleted=models.BooleanField(default=False)
    is_director=models.BooleanField(default=False)
    is_allowed_group =models.BooleanField(default=False)
    google_auth_secret = models.CharField(max_length=32, null=True, blank=True)
    is_2fa_enabled = models.BooleanField(default=False)
    objects=userManager()

    def __unicode__(self):
        return self.id

    def __str__(self):
        return str(self.full_name)+" ("+str(self.mobile_number)+")" or ''
    
    def is_authenticated(self):
        if not self.is_deleted:
            return True
        return False
    
# Remove leading and trailing spaces from 'full_name' field from user table
@receiver(pre_save, sender=user)
def strip_whitespace(sender, instance, **kwargs):
    instance.full_name = instance.full_name.strip()
    
    
class SoilReport(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    farmer = models.OneToOneField(user,on_delete=models.CASCADE)
    soil_report = models.FileField(max_length=500)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True,verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True,db_index=True,verbose_name='updated at')

    def __unicode__(self):
        return self.id
    def __str__(self):
        return str(self.id)


class user_phonenumber_map(models.Model):
    phone_no = JSONField()
    


class carousel(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    user = models.ForeignKey(user, on_delete=models.CASCADE,null=True,blank=True)
    page = models.CharField(max_length=100,choices=PAGES,null=True,blank=True)
    index = models.IntegerField(null=True,blank=True)
    text= models.CharField(max_length=500,null=True,blank=True)
    text_telugu = models.CharField(max_length=500,null=True,blank=True)
    image=models.ImageField(upload_to="carousel",blank=True, null=True)
    image_url = models.CharField(max_length=500,null=True,blank=True)
    image_url_telugu = models.CharField(max_length=500,null=True,blank=True)
    redirect_to = models.CharField(max_length=100,choices=PAGES,null=True,blank=True)

    def __unicode__(self):
        return self.id







class agents(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    user_id = models.ForeignKey(user, on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)



class brand_master(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    name = models.TextField(null=True , blank=True)
    name_telugu = models.TextField(null=True , blank=True)
    notes = models.TextField(null=True , blank=True)
    logo = models.TextField(null=True , blank=True)
    #bio = models.TextField(null=True , blank=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.name

class offers(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    org_id = models.ForeignKey(organizations,on_delete=models.CASCADE)
    status = models.CharField(max_length=10,choices=STATUS)
    brand_id = models.ForeignKey(brand_master, on_delete=models.CASCADE)
    title = models.TextField()
    title_telugu = models.TextField(null=True , blank=True)
    desc = models.TextField()
    desc_telugu =  models.TextField(null=True , blank=True)
    criteria  = models.TextField()
    criteria_telugu = models.TextField(null=True , blank=True)
    duration = models.TextField()
    duration_telugu = models.TextField(null=True , blank=True)
    limit = models.TextField()
    limit_telugu = models.TextField(null=True , blank=True)
    availability = models.TextField(null=True,blank=True)
    availability_telugu = models.TextField(null=True , blank=True)
    image_file=models.ImageField(upload_to="offers",blank=True, null=True)
    image_url = models.TextField(null=True,blank=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.title

class training(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    org_id = models.ForeignKey(organizations,on_delete=models.CASCADE)
    status = models.CharField(max_length=10,choices=STATUS)
    brand_id = models.ForeignKey(brand_master, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    title_telugu =  models.CharField(max_length=500,null=True,blank=True)
    desc = models.TextField(null=True , blank=True)
    desc_telugu = models.TextField(null=True,blank=True)
    media_file=models.FileField(upload_to='advisory',null=True,blank=True)
    media_url = models.CharField(max_length=1000,null=True,blank=True)
    media_type = models.CharField(max_length=1000,null=True,blank=True,choices=MEDIA_TYPE)
    hashtag = ArrayField(models.TextField(blank=True, null=True))
    #hashtag_telugu = ArrayField(models.TextField(default=list,blank=True, null=True))
    timestamp = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    preview_url = models.TextField(blank=True, null=True)
    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.title

    # def video_tag(self):
    #         return mark_safe('<a href="%s"><video src="%s" width="150" height="150" ></video></a>' % (self.media_url,self.media_url))
    # video_tag.short_description = 'Video'

class product_master(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    name = models.CharField(max_length=1000,null=True,blank=True)
    title_telegu = models.CharField(max_length=1000,null=True,blank=True)
    status = models.CharField(max_length=10,choices=STATUS)
    type = models.CharField(max_length=1000,null=True,blank=True)
    category_a = models.CharField(max_length=120, blank=True, null=True,choices=PRODUCT_CATEGORY)
    sub_category = models.CharField(max_length=120, blank=True, null=True,choices=PRODUCT_SUBCATEGORY)
    #crop_id = ArrayField(models.CharField(max_length=50, blank=True, null=True))
    prod_desc = models.CharField(max_length=1000,null=True,blank=True)
    prod_desc_telegu = models.CharField(max_length=1000,null=True,blank=True)
    prod_info = models.TextField(null=True,blank=True)
    prod_info_telegu = models.TextField(null=True,blank=True)
    brand_id = models.ForeignKey(brand_master, on_delete=models.CASCADE)
    tag = models.CharField(max_length=50 , null=True, blank = True)
    usage = models.TextField(null=True , blank=True)
    notes = models.TextField(null=True, blank = True)
    display_price = models.IntegerField(blank = True)
    display_mrp = models.IntegerField(blank = True)
    display_url = models.TextField(blank = True)
    display_url1 = models.TextField(blank = True)
    display_quantity = models.IntegerField(blank = True)
    display_unit = models.TextField(blank = True)
    display_unit_telegu = models.TextField(blank = True)
    agent_price = models.DecimalField(decimal_places=2,max_digits=10,blank = True)
    popular=models.BooleanField(blank=True,null=True)
    crop=models.TextField(null=True,blank=True)
    hp=models.DecimalField(decimal_places=2,max_digits=5,blank = True,null=True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.name

class product_variants(models.Model):
    id	=models.AutoField(primary_key=True,unique=True)
    product_id = models.ForeignKey(product_master, on_delete=models.CASCADE,null=True,blank=True,related_name='variants')
    image_file=models.ImageField(upload_to="product_varients",blank=True, null=True)
    image_url = models.TextField(max_length=120, blank=True, null=True)
    in_stock = models.IntegerField(default=1, blank=True, null=True)
    packet_amount = models.DecimalField(max_digits=7,decimal_places=2,null=True,blank=True)
    packaging_unit = models.CharField(max_length=1000,null=True,blank=True,choices=PACKAGING_UNIT)
    price = models.DecimalField(max_digits=20,decimal_places=2, blank=True, null=True)
    mrp = models.DecimalField(max_digits=20,decimal_places=2,blank=True, null=True)
    info1_text = models.TextField(max_length=120, blank=True, null=True)
    info2_text = models.TextField(max_length=120, blank=True, null=True)
    info3_text = models.TextField(max_length=120, blank=True, null=True)
    info1_image_selected = models.TextField(max_length=120, blank=True, null=True)
    info2_image_selected = models.TextField(max_length=120, blank=True, null=True)
    info3_image_selected = models.TextField(max_length=120, blank=True, null=True)
    info1_image_unselected = models.TextField(max_length=120, blank=True, null=True)
    info2_image_unselected = models.TextField(max_length=120, blank=True, null=True)
    info3_image_unselected = models.TextField(max_length=120, blank=True, null=True)

    def __unicode__(self):
        return self.id

class offer_inquiry(models.Model):
    id	=models.AutoField(primary_key=True,unique=True)
    offer_id = models.ForeignKey(offers, on_delete=models.CASCADE,null=True,blank=True,related_name='inquiry')
    user_id = models.ForeignKey(user, on_delete=models.CASCADE)
    #selected_info = models.TextField(blank=True, null=True)
    #comments = models.TextField(blank=True, null=True)

class aryadhan_inquiry(models.Model):
    id	=models.AutoField(primary_key=True,unique=True)
    aryadhan_id = models.ForeignKey(product_master, on_delete=models.CASCADE,null=True,blank=True,related_name='inquiry')
    user_id = models.ForeignKey(user, on_delete=models.CASCADE)
    selected_info = models.TextField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

class farmManager(models.Manager):
    
    def get_user_by_role(self,role):
        return self.filter(user__user_role__role_name=role)
from django.utils import timezone
 
class farm(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    updated_by_id = models.ForeignKey(user, on_delete=models.CASCADE,null=True,blank=True)
    added_by = models.ForeignKey(user, on_delete=models.CASCADE,null=True,blank=True,related_name='created_by31')
    user = models.ForeignKey(user, on_delete=models.CASCADE,null=True,blank=True,related_name='created_by30')
    org_id = models.ForeignKey(organizations, on_delete=models.CASCADE,null=True,blank=True,related_name="organization_farm")
    name= models.CharField(max_length=100,null=True,blank=True)
    name_telugu =models.CharField(max_length=100,null=True,blank=True)
    stage= models.CharField(max_length=100,null=True,blank=True)
    stage_telugu= models.CharField(max_length=100,null=True,blank=True)
    total_area = models.DecimalField(max_digits=8,decimal_places=2,null=True,blank=True)
    area_unit= models.CharField(max_length=100,null=True,blank=True,choices=LAND_SIZE_UNIT)
    area_unit_telegu= models.CharField(max_length=100,null=True,blank=True,choices=LAND_SIZE_UNIT_TELEGU)
    crop_id = models.ForeignKey(crop_master, on_delete=models.CASCADE,null=True,blank=True)
    crop_variety_id = models.ForeignKey(crop_variety_master, on_delete=models.CASCADE,null=True,blank=True)
    khasra_no = models.CharField(max_length=300,null=True,blank=True)
    sowing_date = models.DateTimeField(null=True,blank=True)
    #crop_variety_id = models.ForeignKey(crop_variety_master, on_delete=models.CASCADE,null=True,blank=True)
    #farm_polygon = models.PolygonField(null=True,blank=True)
    farm_images = ArrayField(models.TextField(),null=True,blank=True)
    timestamp = models.DateTimeField(blank=True, null=True,auto_now_add=True)
    my_plot_id=models.TextField(blank=True,null=True)
    season_id = models.CharField(max_length=100,default="A2022")
    farm_img = models.TextField(blank=True,null=True)
    farmer_contact = models.CharField(max_length=100,blank=True,null=True)
    featured=models.BooleanField(blank=True,null=True)
    graph_image_url=models.TextField(blank=True,null=True)
    latitude = models.DecimalField(max_digits=16,decimal_places=8,null=True,blank=True)
    longitude = models.DecimalField(max_digits=16,decimal_places=8,null=True,blank=True)
    farm_country = models.CharField(max_length=100,default='India')
    farm_state = models.CharField(max_length=100,blank=True,null=True)
    farm_state_hindi = models.CharField(max_length=100,blank=True,null=True)
    farm_district = models.CharField(max_length=100,blank=True,null=True)
    farm_taluka = models.CharField(max_length=100,blank=True,null=True)
    farm_village = models.CharField(max_length=100,blank=True,null=True)
    farm_district_hindi = models.CharField(max_length=100,blank=True,null=True)
    farm_taluka_hindi = models.CharField(max_length=100,blank=True,null=True)
    farm_village_hindi = models.CharField(max_length=100,blank=True,null=True)
    is_location = models.BooleanField(blank=True,null=True)
    healthy = models.BooleanField(blank=True,null=True)
    stressed = models.BooleanField(blank=True,null=True)
    biotic_stress = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    abiotic_stress = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    nutrient_stress = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    moisture = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    stress = models.DecimalField(decimal_places=4,max_digits=10,blank = True,null=True)
    damaged = models.DecimalField(decimal_places=4,max_digits=10,blank = True,null=True)
    health = models.DecimalField(decimal_places=4,max_digits=10,blank = True,null=True)
    updated_on_timestamp = models.DateTimeField(auto_now=True,blank=True,null=True)
    geometry = models2.GeometryField(srid=4326, null=True, blank=True)
    user_survey = models.ForeignKey('survey.UserSurvey', on_delete=models.SET_NULL,null=True,blank=True,related_name='farm_user_survey')
    is_manual_updated = models.BooleanField(default=False)
    type_of_farming=models.CharField(null=True,blank=True,max_length=200)
    pop_group=models.ForeignKey(to='pop_manage.POPGroup',on_delete=models.CASCADE,null=True,blank=True,related_name="farm_pop_group")
    session = models.ForeignKey(to='pop_manage.Session', on_delete=models.SET_NULL, null=True, blank=True, related_name='farms')
    objects= farmManager()
    timestamp_lat_long = models.DateTimeField(null=True, blank=True)
    farmer_type = models.CharField(max_length=20,choices=FARMER_TYPE,null=True,blank=True,db_index=True)

    def __unicode__(self):
        return self.id
    
    def __str__(self):
        return f"{self.name}-({str(self.farmer_contact)})-{str(self.id)}" or ''
    
    def calculate_farmer_type(self):

        if not self.total_area:
            return "NO_AREA"

        try:
            area = float(self.total_area)
        except (TypeError, ValueError):
            return "NO_AREA"

        if area <= 0:
            return "NO_AREA"

        # Convert to hectares if unit is Acre
        if self.area_unit == "Acre" or self.area_unit_telegu == "एकड़":
            area = area / 2.47105

        if area <= 1:
            return "MARGINAL"
        elif area <= 2:
            return "SMALL"
        elif area <= 4:
            return "SEMI_MEDIUM"
        elif area <= 10:
            return "MEDIUM"
        else:
            return "LARGE"

    def generate_my_plot_id(self):
        """
        Generates a unique my_plot_id using:
        - Organization company_id (e.g., 'ARY123')
        - Farm id (after save)
        """
        if not self.org_id or not self.org_id.company_id:
            return None

        return f"{self.org_id.company_id}_{self.id}"
    

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        lat_long_changed = False

        if not is_new:
            try:
                old = farm.objects.only("latitude", "longitude").get(pk=self.pk)
                if old.latitude != self.latitude or old.longitude != self.longitude:
                    lat_long_changed = True
            except farm.DoesNotExist:
                pass

        if is_new and not self.session:
            try:
                CropSession = apps.get_model('pop_manage', 'CropSession')
                if self.crop_id and self.sowing_date:
                    month = self.sowing_date.month
                    cs = CropSession.objects.filter(crop=self.crop_id, from_month__lte=month, to_month__gte=month).order_by('id').first()
                    if cs:
                        self.session = cs.session
            except Exception:
                # avoid breaking save on unexpected issues
                pass
        # Auto assign farmer_type safely
        if is_new:
            self.farmer_type = self.calculate_farmer_type()
        else:
            try:
                old = farm.objects.only("total_area", "area_unit", "area_unit_telegu").get(pk=self.pk)
                if (old.total_area != self.total_area or old.area_unit != self.area_unit or old.area_unit_telegu != self.area_unit_telegu):
                    self.farmer_type = self.calculate_farmer_type()
            except farm.DoesNotExist:
                pass

        # Single save for create/update (session is already set when possible)
        super().save(*args, **kwargs)

        # `my_plot_id` depends on `self.id`, so set it after initial save for new objects.
        if is_new and not self.my_plot_id:
            try:
                self.my_plot_id = self.generate_my_plot_id()
                super().save(update_fields=["my_plot_id"])
            except Exception:
                pass

        # ✅ update timestamp_lat_long only if lat/long changed
        if lat_long_changed:
            farm.objects.filter(pk=self.pk).update(
                timestamp_lat_long=timezone.now()
            )


class farmCropMaster(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    farm = models.ForeignKey(to=farm, on_delete=models.CASCADE, related_name="farm_crop_master")
    crop = models.ForeignKey(to=crop_master, on_delete=models.CASCADE, related_name="crop_master_farm")
    created_at=models.DateTimeField(auto_now_add=True,db_index=True,verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True,db_index=True,verbose_name='updated at')

class stress_data(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    farm_id = models.ForeignKey(farm, on_delete=models.CASCADE,null=True,blank=True)
    date = models.DateField(null=True,blank=True)
    biotic_stress = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    abiotic_stress = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    nutrient_stress = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    moisture = models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)

    def __unicode__(self):
        return self.id


class FarmChangeLog(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    farm = models.ForeignKey(farm, on_delete=models.CASCADE, related_name='change_logs')
    changed_by = models.ForeignKey(user, on_delete=models.SET_NULL, null=True, blank=True)
    field_name = models.CharField(max_length=100)
    old_value = models.TextField(null=True, blank=True)
    new_value = models.TextField(null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f"Farm {self.farm_id} {self.field_name} @ {self.changed_at}"


def normalize_dt(dt):
    # Normalize aware datetimes to naive and remove microseconds
    if dt is None:
        return None
    try:
        if is_aware(dt):
            dt = make_naive(dt)
    except Exception:
        pass
    try:
        return dt.replace(microsecond=0)
    except Exception:
        return dt

@receiver(pre_save, sender=farm)
def log_farm_changes(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = farm.objects.get(pk=instance.pk)
    except farm.DoesNotExist:
        return

    base_fields = ['crop_id', 'crop_variety_id', 'session', 'sowing_date']
    update_fields = kwargs.get('update_fields')
    if update_fields is not None:
        # only log fields explicitly being updated in this save
        to_check_fields = [f for f in base_fields if f in update_fields]
    else:
        to_check_fields = base_fields

    def norm(val):
        # FK/model -> pk; datetime -> normalized; else as-is
        try:
            from django.db.models import Model as DjangoModel
            if isinstance(val, DjangoModel):
                return val.pk
        except Exception:
            pass
        from datetime import datetime as _dt
        if isinstance(val, _dt):
            return normalize_dt(val)
        return val

    for field_attr in to_check_fields:
        old_val = getattr(old, field_attr, None)
        new_val = getattr(instance, field_attr, None)

        # skip if equal after normalization (prevents false sowing_date logs)
        if norm(old_val) == norm(new_val):
            continue

        try:
            old_display = str(old_val) if old_val is not None else None
        except Exception:
            old_display = None
        try:
            new_display = str(new_val) if new_val is not None else None
        except Exception:
            new_display = None

        FarmChangeLog.objects.create(
            farm=instance,
            changed_by=getattr(instance, '_changed_by', None),
            field_name=field_attr,
            old_value=old_display,
            new_value=new_display,
        )

    #def __str__(self):
    #    return self.name

class machine_master(models.Model):
    id=models.AutoField(primary_key=True,unique=True)
    machine_name=models.CharField(max_length=200)
    machine_maker=models.CharField(max_length=200,null=True,blank=True)
    machine_model=models.CharField(max_length=200)
    machine_name_telugu=models.CharField(max_length=200)
    machine_maker_telugu=models.CharField(max_length=200,null=True,blank=True)
    machine_model_telugu=models.CharField(max_length=200)
    owned=models.BooleanField(default=False)
    notes=models.TextField(blank=True,null=True,)
    image_file=models.ImageField(upload_to="machine",blank=True, null=True)
    image_url=models.TextField(blank=True, null=True)
    user_id=models.ForeignKey(user,on_delete=models.CASCADE)

    def __str__(self):
        return self.machine_name

class implement_master(models.Model):
    id=models.AutoField(primary_key=True,unique=True)
    user_id=models.ForeignKey(user,on_delete=models.CASCADE)
    implement_name_telugu=models.CharField(max_length=200,null=True,blank=True)
    implement_maker_telugu=models.CharField(max_length=200,null=True,blank=True)
    implement_name=models.CharField(max_length=200)
    implement_maker=models.CharField(max_length=200,null=True,blank=True)
    implement_model=models.CharField(max_length=200,null=True,blank=True)
    implement_model_telugu=models.CharField(max_length=200,null=True,blank=True)
    owned=models.BooleanField(default=False)
    rented=models.BooleanField(default=False)
    notes=models.TextField(null=True,blank=True)
    image_file=models.ImageField(upload_to="implement",blank=True, null=True)
    image_url=models.TextField(blank=True, null=True)

    def __str__(self):
        return self.implement_name

class seed_master(models.Model):
    id=models.AutoField(primary_key=True,unique=True)
    seed_name=models.CharField(max_length=200)
    seed_maker=models.CharField(max_length=200,null=True,blank=True)
    user_id=models.ForeignKey(user,on_delete=models.CASCADE)
    seed_variety=models.IntegerField(null=True,blank=True)
    seed_quantity=models.IntegerField(null=True,blank=True)
    maturity_days=models.IntegerField(null=True,blank=True)
    yields=models.TextField(null=True,blank=True)
    noted=models.TextField(null=True,blank=True)
    image_file=models.ImageField(upload_to="implement",blank=True, null=True)
    image_url=models.TextField(blank=True, null=True)

    def __str__(self):
        return self.seed_name


class chemical_master(models.Model):
    id=models.AutoField(primary_key=True,unique=True)
    chemical_name=models.CharField(max_length=200,null=True,blank=True)
    chemical_maker=models.CharField(max_length=200,null=True,blank=True)
    chemical_type=models.TextField(null=True,blank=True)
    chemical_amount=models.DecimalField(max_digits=5,decimal_places=2,null=True,blank=True)
    noted=models.TextField(null=True,blank=True)
    image_file=models.ImageField(upload_to="chemical",blank=True, null=True)
    image_url=models.TextField(blank=True, null=True)
    user_id=models.ForeignKey(user,on_delete=models.CASCADE)

    def __str__(self):
        return self.chemical_name


class sell_crop(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    user_id = models.ForeignKey(user, on_delete=models.CASCADE)
    org_id = models.ForeignKey(organizations,on_delete=models.CASCADE,blank=True, null=True)
    crop_id = models.ForeignKey(crop_master, on_delete=models.CASCADE)
    farm_id = models.CharField(max_length=200,null=True,blank=True)
    crop_variety_id = models.ForeignKey(crop_variety_master, on_delete=models.CASCADE,null=True,blank=True)
    quantity_expected = models.DecimalField(max_digits=8,decimal_places=2)
    price_expected = models.DecimalField(max_digits=8,decimal_places=2)
    #availability_date1 = ArrayField(models.DateField(),null=True,blank=True)
    availability_date = models.TextField(null=True,blank=True)
    availability_days = models.IntegerField(null=True,blank=True)
    notes = models.TextField(blank=True, null=True)
    image_file=models.ImageField(upload_to="sell_crop",blank=True, null=True)
    image_url = models.TextField(null=True,blank=True)
    quantity_expected_unit = models.CharField(max_length=50,null=True,blank=True)
    quantity_expected_unit_telegu = models.CharField(max_length=50,null=True,blank=True)
    def __unicode__(self):
        return self.id



class notification(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    user_id = models.ForeignKey(user, on_delete=models.CASCADE)
    title = models.TextField(blank=True, null=True)
    title_telugu = models.TextField(blank=True, null=True)
    desc = models.TextField(blank=True, null=True)
    desc_telugu = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(blank=True, null=True,auto_now_add=True)
    notification_icon = models.TextField(blank=True, null=True)
    group = models.IntegerField(blank=True, null=True)

    def __unicode__(self):
        return self.id
from django.utils.html import mark_safe
from libraries.tag_social_post import TagSocialPost

class SocialPostTag(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    name= models.CharField(max_length=300)
    status= models.BooleanField(default=True)

class social_post(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    org_id = models.ForeignKey(organizations,on_delete=models.CASCADE)
    user_id =  models.ForeignKey(user, on_delete=models.CASCADE)
    status = models.CharField(max_length=50,choices=STATUS,default='Active')
    media_file = models.FileField(upload_to='social_post',null=True,blank=True)
    media_url=models.TextField(blank=True,null=True)
    media_type = models.TextField(blank=True, null=True,choices=MEDIA_TYPE)
    desc = models.TextField(blank=True, null=True)
    desc_telugu = models.TextField(blank=True, null=True)
    location_id = ArrayField(models.CharField(max_length=120),blank=True, null=True)
    short_desc_telugu = models.TextField(blank=True, null=True)
    friend_id = ArrayField(models.CharField(max_length=120),blank=True, null=True)
    hashtag_id = ArrayField(models.CharField(max_length=120),blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    approved = models.BooleanField(default=True)
    tag= models.CharField(max_length=300, null=True,blank=True)
    # full_name = models.TextField(max_length=100,blank=True,null=True)
    # email1 = models.CharField(max_length=250,blank=True,null=True)
    # mobile_number = models.IntegerField(blank=True,null=True)
    # # location = models.CharField(max_length=100,blank=True,null=True)



    #spam = models.BooleanField(default=False)
    #inappropriate = models.BooleanField(default=False)

    def __unicode__(self):
        return self.id
    
    def save(self, *args, **kwargs):
        tag_social_post= TagSocialPost()
        tag= tag_social_post.gettag(self.desc)
        # print("here is the tag update in social post")
        # print(tag)
        if tag and 'prediction' in tag.keys():
            self.tag= tag['prediction']
            tags= SocialPostTag.objects.filter(status=False).values_list('name')
            if tag['prediction'] in tags:
                self.status="Inactive"
            else:
                self.status="Active"
            # print("tag added")
        # return super().save()
        return super(social_post, self).save(*args, **kwargs)
        



class community_post_reporting(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    user_id = models.ForeignKey(user, on_delete=models.CASCADE)
    post_id = models.ForeignKey(social_post, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True,null=True , blank=True)
    spam = models.BooleanField(blank=True, null=True)
    inappropriate = models.BooleanField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.id

class comment_reporting(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    user_id = models.ForeignKey(user, on_delete=models.CASCADE,related_name='a3',null=True , blank=True)
    post_id = models.ForeignKey(social_post, on_delete=models.CASCADE,null=True , blank=True)
    comment_id = models.CharField(max_length=50,null=True , blank=True)
    comment_content = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True,null=True , blank=True)
    report = models.BooleanField(blank=True, null=True)
    block = models.BooleanField(blank=True, null=True)
    reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.id

class user_reporting(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    user_id = models.ForeignKey(user, on_delete=models.CASCADE,related_name='a1',blank=True, null=True)
    blocked_by_user = models.ForeignKey(user, on_delete=models.CASCADE,related_name='a2',blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True,null=True , blank=True)
    report = models.BooleanField(blank=True, null=True)
    block = models.BooleanField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return self.id


    def image_tag(self):
            return mark_safe('<a href="%s"><img src="%s" width="150" height="150" /></a>' % (self.media_url,self.media_url))
    image_tag.short_description = 'Image'

class hashtag_master(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    tag = models.CharField(max_length=50,null=True , blank = True)
    title = models.CharField(max_length=100,null=True , blank = True)

    def __unicode__(self):
        return self.id

    def __str__(self):
        return self.tag

class location_master(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    location_name = models.CharField(max_length=100)

    def __str__(self):
        return self.location_name

class friends_master(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    user_id = models.ForeignKey(user, on_delete=models.CASCADE,related_name='created_by29')
    friend_user_id = models.ForeignKey(user, on_delete=models.CASCADE,related_name='created_by28')

class OTPValidation(models.Model):
    otp_value = models.CharField(max_length=120)
    phone_number = models.CharField(('phoneNumber'), max_length=20, blank=True)
    status= models.IntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True,verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True,db_index=True,verbose_name='updated at')

    def __str__(self):
        return self.phone_number

class tb_application_access(models.Model):
    id = models.AutoField(primary_key=True,unique=True)
    #api_id=models.IntegerField(unique=True)
    key = models.CharField(max_length=36,default=uuid.uuid4)
    application_name = models.CharField(max_length=100)
    #count=models.IntegerField(default=10,blank=True,null=True)

    def __str__(self):
        return self.application_name

class delivery_address(models.Model):
    id = models.AutoField(primary_key=True,unique=True)
    user_id = models.ForeignKey(user, on_delete=models.CASCADE)
    delivery_pincode = models.IntegerField(null=True,blank=True)
    location = models.TextField(null=True,blank=True)
    location1= models.TextField(null=True,blank=True)
    house = models.TextField(null=True,blank=True)
    landmark = models.TextField(null=True,blank=True)
    notes = models.TextField(null=True,blank=True)

    def __str__(self):
        return self.location

class news(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    org_id = models.ForeignKey(organizations, on_delete=models.CASCADE,null=True,blank=True)
    status = models.CharField(max_length=50,null=True , blank=True,choices=STATUS)
    rank = models.IntegerField(null=True , blank=True)
    title = models.TextField(null=True , blank=True)
    title_telugu = models.TextField(null=True , blank=True)
    source = models.TextField(null=True , blank=True)
    source_telugu = models.TextField(null=True , blank=True)
    timestamp = models.DateTimeField(auto_now_add=True,null=True , blank=True)
    desc = models.TextField(null=True , blank=True)
    desc_telugu = models.TextField(null=True , blank=True)
    notes = models.TextField(null=True , blank=True)
    url_telugu = models.TextField(null=True , blank=True)
    image_file=models.ImageField(upload_to="news",blank=True, null=True)
    image_url=models.TextField(null=True , blank=True)
    thumbnail_image=models.ImageField(upload_to="news/thumbnail",blank=True, null=True)
    thumbnail_url=models.TextField(null=True , blank=True)
    #delivery_address

    def __str__(self):
        return self.title

class order(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    user_id = models.ForeignKey(user, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=7,decimal_places=2,blank=True, null=True)
    status = models.CharField(max_length=50,choices=ORDER_STATUS)
    transaction_id = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    delivery_address_id = models.ForeignKey(delivery_address,on_delete=models.CASCADE,null=True, blank=True)
    payment_method = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True,null=True, blank=True)

    def __unicode__(self):
        return self.id
    def __str__(self):
        return str(self.id)

class order_details(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    order_id = models.ForeignKey(order, on_delete=models.CASCADE)
    product_id = models.ForeignKey(product_master, on_delete=models.CASCADE)
    quantity = models.IntegerField(null=True , blank=True)
    amount = models.DecimalField(max_digits=7,decimal_places=2,blank=True, null=True)

    def __unicode__(self):
        return self.id
    def __str__(self):
        return str(self.id)

class tracking(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    order_id = models.ForeignKey(order, on_delete=models.CASCADE)
    packaged_date = models.DateTimeField(null=True , blank = True)
    dispatched_date = models.DateTimeField(null=True , blank = True)
    dispatched = models.BooleanField(default=False)
    packaged = models.BooleanField(default=False)
    packed_details = models.TextField(null=True , blank = True)
    dispatched_details = models.TextField(null=True , blank = True)
    out_for_delivery_details = models.TextField(null=True , blank = True)
    delivered_details = models.TextField(null=True , blank = True)
    delivered = models.BooleanField(default=False)
    out_for_delivery = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)
    notes = models.TextField(null=True , blank = True)
    def __unicode__(self):
        return self.id

    # def __str__(self):
    #    return str(self.id)
class partner_type_master(models.Model):
    id=models.AutoField(primary_key=True,unique=True)
    partner_type=models.TextField(null=True,blank=True)
    icon_url = models.TextField(null=True,blank=True)

from django.contrib.gis.geos import Point

class partner_list(models.Model):
    id=models.AutoField(primary_key=True,unique=True)
    partner_name=models.TextField(null=True,blank=True)
    latitude=models.DecimalField(max_digits=16,decimal_places=8,null=True,blank=True)
    longitude=models.DecimalField(max_digits=16,decimal_places=8,null=True,blank=True)
    whatsapp_number=models.BigIntegerField(null=True,blank=True)
    contact_number=models.BigIntegerField(null=True,blank=True)
    partner_type=models.ForeignKey(partner_type_master,on_delete=models.CASCADE)

class coupon_details(models.Model):
    id=models.AutoField(primary_key=True,unique=True)
    display_name=models.TextField(null=True,)
    coupon_code=models.CharField(max_length=36,default=uuid.uuid4)
    minimum_amount=models.IntegerField(null=True,blank=True)
    minimum_quantity=models.IntegerField(null=True,blank=True)
    discount_value=models.IntegerField(null=True,blank=True)
    discount_percentage=models.TextField(null=True,blank=True)
    maximum_applicable=models.IntegerField(null=True,blank=True)
    valid_from=models.DateTimeField(blank=True, null=True)
    valid_to=models.DateTimeField(blank=True, null=True)
    applicable_brand_id=models.ForeignKey(brand_master,on_delete=models.CASCADE)
    applicable_product_id=models.ForeignKey(product_master,on_delete=models.CASCADE)

class activity_master(models.Model):#get and Post api
    id  = models.AutoField(primary_key=True,unique=True)
    activity_name = models.CharField(max_length=100,blank=True, null=True)
    activity_name_telugu = models.CharField(max_length=100,blank=True, null=True)
    activity_icon=models.ImageField(upload_to="activity_icon",blank=True, null=True)
    activity_icon_url=models.TextField(blank=True, null=True)
    plot_id=models.CharField(max_length=100,blank=True , null=True)

class activity(models.Model):
    id  = models.AutoField(primary_key=True,unique=True)
    user_id = models.ForeignKey(user, on_delete=models.CASCADE)
    org_id = models.ForeignKey(organizations, on_delete=models.CASCADE,null=True,blank=True)
    activity_name = models.TextField(null=True,blank=True)
    activity_name_telugu = models.TextField(null=True,blank=True)
    activity_id= models.ForeignKey(activity_master, on_delete=models.CASCADE)
    start_timestamp = models.DateTimeField(auto_now_add=True,null=True,blank=True)
    end_timestamp = models.DateTimeField(null=True,blank=True)
    total_hours = models.DecimalField(max_digits=8,decimal_places=2,null=True,blank=True,default=0.5)
    total_area = models.DecimalField(max_digits=8,decimal_places=2,null=True,blank=True,default=2.0)
    area_unit = models.CharField(max_length=100,choices=LAND_SIZE_UNIT)
    chemical_used=models.TextField(null=True,blank=True)
    chemical_used_telugu=models.TextField(null=True,blank=True)
    seed_used=models.TextField(null=True,blank=True)
    seed_used_telugu=models.TextField(null=True,blank=True)
    machine_used=models.TextField(null=True,blank=True)
    machine_used_telugu=models.TextField(null=True,blank=True)
    implement_used=models.TextField(null=True,blank=True)
    implement_used_telugu=models.TextField(null=True,blank=True)
    notes=models.CharField(blank=True,null=True,max_length=100)
    image_urls=models.TextField(null=True,blank=True)
    plot_id=models.CharField(blank=True,null=True,max_length=100)
    plot_id_telugu=models.CharField(blank=True,null=True,max_length=100)
    image1=models.ImageField(upload_to="activity",blank=True, null=True)
    image2=models.ImageField(upload_to="activity",blank=True, null=True)
    image3=models.ImageField(upload_to="activity",blank=True, null=True)
    image4=models.ImageField(upload_to="activity",blank=True, null=True)
    image5=models.ImageField(upload_to="activity",blank=True, null=True)
    trajectory = models.TextField(null=True,blank=True)

    def __unicode__(self):
        return self.id

class agenda(models.Model):
    id  = models.AutoField(primary_key=True,unique=True)
    img_url=models.ImageField(null=True,blank=True)
    text = models.CharField(blank=True,null=True,max_length=500)
    status=models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.text
    
    def __unicode__(self):
        return self.id

class live_feed(models.Model):
    id  = models.AutoField(primary_key=True,unique=True)
    started_by_user_id = models.ForeignKey(user, on_delete=models.CASCADE)
    org_id = models.ForeignKey(organizations, on_delete=models.CASCADE)
    start_timestamp = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    end_timestamp = models.DateTimeField(null=True,blank=True)
    url=models.CharField(blank=True,null=True,max_length=500)
    notes=models.CharField(blank=True,null=True,max_length=100)
    status = models.CharField(max_length=10,choices=STATUS,default='Active')
    agenda = models.ForeignKey(agenda, on_delete=models.CASCADE,blank=True, null=True)
    number_of_attendees = models.IntegerField(blank=True,null=True)
    screenshot_recording = models.CharField(max_length=500,null=True,blank=True)
    video_recording = models.CharField(max_length=500,null=True,blank=True)
    
    def __unicode__(self):
        return self.id

class compliance(models.Model):
    id  = models.AutoField(primary_key=True,unique=True)
    status = models.CharField(max_length=500,choices=STATUS,default='Active')
    user_id = models.ForeignKey(user, on_delete=models.CASCADE)
    timestamp = models.DateField(auto_now_add=True,blank=True, null=True)
    updated_at =models.DateField(blank=True, null=True)
    document_type = models.CharField(blank=True,null=True,max_length=500)
    document_name = models.CharField(blank=True,null=True,max_length=500)
    file_type = models.CharField(blank=True,null=True,max_length=500)
    file_url1 = models.CharField(blank=True,null=True,max_length=500)
    file_url2 = models.CharField(blank=True,null=True,max_length=500)
    file_url3 = models.CharField(blank=True,null=True,max_length=500)
    file_url4 = models.CharField(blank=True,null=True,max_length=500)
    file_url5 = models.CharField(blank=True,null=True,max_length=500)

    def __unicode__(self):
        return self.id

class product_category(models.Model):
    id  = models.AutoField(primary_key=True,unique=True)
    status = models.CharField(blank=True,null=True,max_length=500,choices=STATUS)
    categoty_name = models.CharField(blank=True,null=True,max_length=500)
    categoty_name_hindi = models.CharField(blank=True,null=True,max_length=500)

    def __unicode__(self):
        return self.id

class input_catalogue(models.Model):
    id  = models.AutoField(primary_key=True,unique=True)
    status = models.CharField(blank=True,null=True,max_length=500,choices=STATUS,default='Active')
    added_by_user_id = models.ForeignKey(user, on_delete=models.CASCADE)
    contact_number = models.CharField(blank=True,null=True,max_length=15)
    org_id = models.ForeignKey(organizations,on_delete=models.CASCADE)
    timestamp=models.DateField(auto_now_add=True,blank=True, null=True)
    updated_at =models.DateField(blank=True, null=True)
    name = models.CharField(blank=True,null=True,max_length=500)
    name_hindi = models.CharField(blank=True,null=True,max_length=500)
    brand = models.CharField(blank=True,null=True,max_length=500)
    brand_hindi = models.CharField(blank=True,null=True,max_length=500)
    product_category = models.CharField(blank=True,null=True,max_length=500)
    sizes_available = ArrayField(models.IntegerField(),null=True,blank=True)
    product_images = ArrayField(models.CharField(max_length=500),null=True,blank=True)
    size_unit = models.CharField(blank=True,null=True,max_length=500)
    size_unit_hindi = models.CharField(blank=True,null=True,max_length=500)
    short_description = models.CharField(blank=True,null=True,max_length=500)
    long_description = models.TextField(blank=True,null=True)
    short_description_hindi = models.CharField(blank=True,null=True,max_length=500)
    long_description_hindi = models.TextField(blank=True,null=True)
    mrp = models.DecimalField(max_digits=8,decimal_places=2,null=True,blank=True,default=2.0)
    price = models.DecimalField(max_digits=8,decimal_places=2,null=True,blank=True,default=2.0)
    discount_percentage = models.DecimalField(max_digits=8,decimal_places=2,null=True,blank=True,default=2.0)
    quantity_available = models.IntegerField(null=True,blank=True)
    quantity_updated_at = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True,null=True)
    notes_hindi = models.TextField(blank=True,null=True)

    def __unicode__(self):
        return self.id

class SellRecords(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    date_time=models.DateTimeField()
    user_added = models.ForeignKey(to=user, on_delete=models.CASCADE,related_name="sale_record_added_by")
    selected_user = models.ForeignKey(to=user, on_delete=models.CASCADE,related_name="sale_record_selected_user")
    product = models.ForeignKey(to=input_catalogue, on_delete=models.CASCADE)
    qty = models.IntegerField(default=0)
    rate = models.IntegerField(default=0)
    amount = models.IntegerField(default=0)
    remarks = models.TextField(null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True,verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True,db_index=True,verbose_name='updated at')


class ChangeOrgRole(models.Model):
    id	= models.AutoField(primary_key=True,unique=True)
    user= models.ForeignKey(to=user,on_delete=models.CASCADE,related_name="user_change_role_org")
    created_at=models.DateTimeField(auto_now_add=True,db_index=True,verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True,db_index=True,verbose_name='updated at')



class farmer_request(models.Model):
    id  = models.AutoField(primary_key=True,unique=True)
    status = models.CharField(blank=True,null=True,max_length=500,choices=ORDER_STATUS,default='Placed')
    org_id = models.ForeignKey(organizations, on_delete=models.CASCADE,null=True,blank=True)
    user_id = models.ForeignKey(user, on_delete=models.CASCADE,null=True,blank=True)
    product_id = models.ForeignKey(input_catalogue,blank=True,null=True,on_delete=models.CASCADE)
    affected_images = ArrayField(models.CharField(max_length=500),null=True,blank=True)
    description = models.CharField(blank=True,null=True,max_length=500)

    def __unicode__(self):
        return self.id

class app_configuration(models.Model):
    id  = models.AutoField(primary_key=True,unique=True)
    minimum_compatible_version = models.IntegerField(blank=True,null=True)
    status = models.BooleanField(blank=True,null=True,default=True)
    def __unicode__(self):
        return self.id

class AuthenticationToken(models.Model):
    """
    The default authorization token model.
    """
    key = models.CharField('Key', max_length=1000, primary_key=True)

    user = models.OneToOneField(
        user, related_name='auth_token',
        on_delete=models.CASCADE, verbose_name="user"
    )
    created = models.DateTimeField('Created', auto_now_add=True)

    class Meta:
        verbose_name = "Token"
        verbose_name_plural = "Tokens"

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(AuthenticationToken, self).save(*args, **kwargs)

    def generate_key(self):        
        signing_key = 'ARYA_SHAKTI_APP'
       
        compact_jws=jwt.encode({"id":self.user.id,
                                "is_active":True,
                                "mobile_number":self.user.mobile_number,
                                "full_name":self.user.full_name},str(self.user.id),'HS256')
       
        return compact_jws

    def __str__(self):
        return self.key

class DeviceData(models.Model):
    id  = models.AutoField(primary_key=True,unique=True)
    device_name=models.CharField(max_length=500)

    def __str__(self):
        return self.device_name # this 'name' field must be exist in your model.


class UserDevice(models.Model):
    id  = models.AutoField(primary_key=True,unique=True)
    user = models.ForeignKey(
        user, related_name='user',
        on_delete=models.CASCADE, verbose_name="user"
    )
    device = models.ForeignKey(
        DeviceData, related_name='device',
        on_delete=models.CASCADE, verbose_name="device"
    )


class UserDeviceManagement(models.Model):
    
    id = models.AutoField(primary_key=True, unique=True)
    user = models.ForeignKey(
        user, related_name='device_management',
        on_delete=models.CASCADE, verbose_name="user"
    )
    device_id = models.CharField(max_length=200, blank=True, null=True, db_index=True)
    device_name = models.CharField(max_length=200, blank=True, null=True)
    device_type = models.CharField(max_length=100, blank=True, null=True)   # e.g. "mobile", "tablet"
    device_os = models.CharField(max_length=200, blank=True, null=True)     # e.g. "android 15", "iOS 18.1"
    device_model = models.CharField(max_length=200, blank=True, null=True)  # e.g. "Samsung Galaxy S24"
    is_active = models.BooleanField(default=True)
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    
    def __str__(self):
        return f"{self.user.full_name} - {self.device_name}"
    
    class Meta:
        ordering = ['-last_used']
        verbose_name = 'User Device Management'
        verbose_name_plural = 'User Device Management'
        unique_together = ('user', 'device_id')

class OrganizationDoc(models.Model):
    id = models.AutoField(primary_key=True,unique=True)   
    user= models.ForeignKey(to=user,on_delete=models.CASCADE,related_name='organization_doc_user')
    organization= models.ForeignKey(to=organizations,on_delete=models.CASCADE,related_name='organization_doc')
    doc_url=models.CharField(max_length=200)
    status= models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True,verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True,db_index=True,verbose_name='updated at')
    
class TagType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    is_active = models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True,verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True,db_index=True,verbose_name='updated at')

    class Meta:
        ordering = ('category', 'name')
        unique_together = ('name', 'category')

    def normalize_category(self, value):
        return str(value).strip().upper().replace(" ", "_")

    def save(self, *args, **kwargs):
        if self.category:
            self.category = self.normalize_category(self.category)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.category})"

class Tag(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    name = models.CharField(max_length=200)
    image = models.ImageField(blank=True, null=True)
    type = models.ForeignKey(TagType,on_delete=models.SET_NULL,blank=True,null=True,related_name="tags")
    color = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return f"{self.name} ({self.type})"

class TagOrganization(models.Model):
    id = models.AutoField(primary_key=True,unique=True)  
    organization= models.ForeignKey(to=organizations,on_delete=models.CASCADE,related_name="tag_organization")
    tag= models.ForeignKey(to=Tag,on_delete=models.CASCADE,related_name="organization_tag")
    tag_assigned_date = models.DateTimeField(null=True, blank=True, db_index=True)
    tag_unassigned_date = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True,verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True,db_index=True,verbose_name='updated at')

    class Meta:
        unique_together = ('organization', 'tag')
        ordering = ('-created_at',)

    def __str__(self):
        return f"{self.organization} - {self.tag}"
 
class TagFarms(models.Model):
    id = models.AutoField(primary_key=True,unique=True)  
    farm= models.ForeignKey(to=farm,on_delete=models.CASCADE,related_name="tag_farm")
    tag= models.ForeignKey(to=Tag,on_delete=models.CASCADE,related_name="farm_tag")
    created_at=models.DateTimeField(auto_now_add=True,db_index=True,verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True,db_index=True,verbose_name='updated at')

class LivefeedUser(models.Model):
    id = models.AutoField(primary_key=True,unique=True)  
    user=models.ForeignKey(to=user,on_delete=models.CASCADE,related_name="livefeed_user")
    live_feed=models.ForeignKey(to=live_feed,on_delete=models.CASCADE,related_name="user_livefeed")
    data=JSONField(null=True,blank=True)
    status=models.IntegerField(default=0)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True,verbose_name='created at')
    updated_at = models.DateTimeField(auto_now=True,db_index=True,verbose_name='updated at')


class IndiaVillages(models.Model):
    id = models.CharField(max_length=255, primary_key=True)
    village = models.CharField(max_length=255, null=True, blank=True)
    subdistrict = models.CharField(max_length=255, null=True, blank=True)
    district = models.CharField(max_length=255, null=True, blank=True)
    state = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    geometry = models.GeometryField(null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)


    class Meta:
        db_table = "indiavillages"
        managed = False   # Table already exists, Django will not manage it

    def __str__(self):
        return f"{self.village}, {self.district}, {self.state}"