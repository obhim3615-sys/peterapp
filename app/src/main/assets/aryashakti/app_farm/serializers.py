# Created by --hameed-- on 14/03/19 at 1:33 PM
from rest_framework import serializers
from django.db.models import Q
from . import models
from app_farm.utils import helper

from rest_framework.serializers import Serializer, FileField
from certification_card.models import ScoreGeneralFarmer
from core.models import Country

# Serializers define the API representation.
class UploadSerializer(Serializer):
    file_uploaded = FileField()
    class Meta:
        fields = ['file_uploaded']

class signuperializer(serializers.ModelSerializer):
    class Meta:
        model = models.user
        #fields = '__all__'
        fields = ('id','user_role','organization','language_selected','admin','mobile_number','otp_verfied','full_name','full_name_telugu','land_size','land_size_unit','land_size_unit_telugu','crop_interest','address_pincode','address_country','address_state','address_district','address_taluka','address_village','bio','bio_telugu','user_profile_img_file','user_profile_img','installed_app','timestamp','firebase_token')
        #depth = 1

class mobserializer(serializers.ModelSerializer):
    class Meta:
        model = models.user
        fields = ('id','mobile_number','firebase_token')


class notificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.notification
        fields = ('id','user_id','title','title_telugu','desc','desc_telugu','timestamp','notification_icon','group')

class orderSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.order
        fields = ('id','total_amount','status','user_id')

class myplotSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.farm
        fields = ('id','my_plot_id')

class stressfarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.farm
        fields = ('id','user_id','stress')
        depth=1

class addorderlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.order
        fields = '__all__'


class addorderdetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.order_details
        fields = '__all__'

class community_post_reportingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.community_post_reporting
        fields = '__all__'

class comment_reportingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.comment_reporting
        fields = '__all__'

class user_reportingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.user_reporting
        fields = '__all__'
        depth=1

class adduser_reportingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.user_reporting
        fields = '__all__'

class croplistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.crop_master
        fields = '__all__'

class croplistorgSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.organizations
        fields = ('crops')
        depth=1

class varietylistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.crop_variety_master
        fields = '__all__'
        depth=1

class existinguserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.user
        fields = ('id','mobile_number','organization','admin','firebase_token')

class farmaddSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.farm
        fields = '__all__'

class farmlistSerializer(serializers.ModelSerializer):
    kyc_documents= serializers.SerializerMethodField('get_kyc_documents')
    country_code = serializers.SerializerMethodField('get_country_code')
    user_full_name = serializers.SerializerMethodField('get_user_full_name')
    user_mobile_number = serializers.SerializerMethodField('get_user_mobile_number')
    gender = serializers.SerializerMethodField('get_user_gender')
    crop_variety = serializers.SerializerMethodField('get_crop_variety_name')
    session_name = serializers.SerializerMethodField('get_session_name')
    session_id = serializers.SerializerMethodField('get_session_id')
    farmer_img = serializers.SerializerMethodField('get_farmer_img')

    def get_kyc_documents(self,obj):
        if not obj or not obj.user:
            return []
        docs = list(obj.user.document_user.filter(status=1).values_list('type', flat=True))
        if obj.user.otp_verfied:
            docs.append('otp_verified')
        return docs
    
    def get_country_code(self,obj):
        if not obj or not obj.user or not obj.user.country:
            return ""
        return obj.user.country.mobile_code
    
    def get_user_full_name(self,obj):
        if obj and obj.user:
            return obj.user.full_name or ""
        return ""
    
    def get_user_mobile_number(self,obj):
        if obj and obj.user:
            return obj.user.mobile_number or ""
        return ""
    
    def get_user_gender(self,obj):
        if obj and obj.user:
            return obj.user.gender or ""
        return ""
    
    def get_crop_variety_name(self, obj):
        if obj and obj.crop_variety_id:
            return obj.crop_variety_id.crop_variety  # from crop_variety_master
        return ""
    
    def get_session_name(self, obj):
        try:
            return obj.session.name if obj and obj.session else ""
        except Exception:
            return ""

    def get_session_id(self, obj):
        try:
            return obj.session.id if obj and obj.session else None
        except Exception:
            return None

    def get_farmer_img(self, obj):
        if not obj or not obj.user:
            return ""

        path = obj.user.user_profile_img
        if not path:
            return ""

        if isinstance(path, str) and path.startswith("http"):
            return path

        return self.signed_map.get(path)

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        objs = args[0] if args else []
        paths = []

        for obj in objs:
            if obj.user and obj.user.user_profile_img:
                path = obj.user.user_profile_img
                if isinstance(path, str) and path.startswith("http"):
                    continue
                paths.append(path)

        if paths:
            self.signed_map = helper.generate_multiple_signed_urls(
                list(set(paths)), 
                expiration_minutes=1440
            )
        else:
            self.signed_map = {}

    class Meta:
        model = models.farm
        fields = ('id','user_full_name','user_mobile_number','gender','kyc_documents','country_code','user_id','graph_image_url','name','name_telugu','stage','stage_telugu','area_unit_telegu','total_area','area_unit','crop_id','my_plot_id','season_id','farm_img','farmer_contact','is_location','farm_img','latitude','longitude','healthy','stressed','featured','biotic_stress','abiotic_stress','nutrient_stress','moisture','farm_state','farm_district','farm_taluka','farm_village','khasra_no','type_of_farming','sowing_date','crop_variety','session_name','session_id','farmer_img')
        depth=1

class loclistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.farm
        fields = ('farm_state','farm_district','farm_taluka','farm_village','farm_state_hindi','farm_district_hindi','farm_taluka_hindi','farm_village_hindi')
        depth=1

class loclistSerializerstate(serializers.ModelSerializer):
    class Meta:
        model = models.farm
        fields = ('farm_state','farm_state_hindi')
        depth=1

class loclistSerializerdistrict(serializers.ModelSerializer):
    class Meta:
        model = models.farm
        fields = ('farm_district','farm_district_hindi')
        depth=1

class loclistSerializertaluka(serializers.ModelSerializer):
    class Meta:
        model = models.farm
        fields = ('farm_taluka','farm_taluka_hindi')
        depth=1

class loclistSerializervillage(serializers.ModelSerializer):
    class Meta:
        model = models.farm
        fields = ('farm_village','farm_village_hindi')
        depth=1

class sellcropaddSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.sell_crop
        fields = '__all__'

class sell_croplistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.sell_crop
        fields = ('id','user_id','org_id','farm_id','crop_id','crop_variety_id','quantity_expected','price_expected','quantity_expected_unit','quantity_expected_unit_telegu','image_url')
        depth=2

class offerlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.offers
        fields = ('id','brand_id','title','title_telugu','image_url')
        depth=1


class offerdetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.offers
        fields = ('id','brand_id','title','title_telugu','desc','desc_telugu','criteria','criteria_telugu','duration','duration_telugu','limit','limit_telugu','availability','image_url','availability_telugu')
        depth=1

class traininglistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.training
        fields = ('id','org_id','brand_id','title','preview_url','title_telugu','desc_telugu','timestamp')
        depth=1

class trainingdetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.training
        fields = ('id','org_id','brand_id','title','title_telugu','desc','desc_telugu','media_url','media_type','hashtag','timestamp','preview_url')
        depth=1

class productlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.product_master
        fields = '__all__'
        depth=2

class productdetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.product_variants
        fields = '__all__'
        depth=2

class adddeliveryaddress(serializers.ModelSerializer):
    class Meta:
        model = models.delivery_address
        fields = '__all__'

class deliveryaddresslist(serializers.ModelSerializer):
    class Meta:
        model = models.delivery_address
        fields = '__all__'
        depth=1

class newslistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.news
        fields = ('id','status','org_id','rank','title','source','timestamp','desc','title_telugu','source_telugu','desc_telugu','notes','thumbnail_url','timestamp','url_telugu')
        depth=1

class newsdetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.news
        fields = '__all__'

class trackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.tracking
        fields = '__all__'

class orderDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.order_details
        fields = '__all__'
        depth = 2

class productvariantlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.product_variants
        fields = ('id','product_id')

class carousellistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.carousel
        fields = '__all__'

class carousellistAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.organizations
        fields = ('carousel1','carousel2','carousel3','carousel4')

class orgSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.organizations
        fields = '__all__'


class OrganizationTagSerializer(serializers.ModelSerializer):
    tag_name = serializers.CharField(source='tag.name', read_only=True)
    tag_type = serializers.CharField(source='tag.type.name', read_only=True)
    tag_category = serializers.CharField(source='tag.type.category', read_only=True)
    organization_name = serializers.CharField(source='organization.org_name', read_only=True)

    class Meta:
        model = models.TagOrganization
        fields = (
            'id',
            'organization',
            'organization_name',
            'tag',
            'tag_name',
            'tag_type',
            'tag_category',
            'tag_assigned_date',
            'tag_unassigned_date',
            'created_at',
            'updated_at',
        )


class OrganizationWithTagsSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField()
    cadre = serializers.SerializerMethodField()
    state = serializers.SerializerMethodField()

    class Meta:
        model = models.organizations
        fields = '__all__'

    def _latest_tag_by_category(self, obj, category_name):
        return obj.tag_organization.select_related('tag', 'tag__type').filter(
            tag__type__category__iexact=category_name
        ).order_by('-created_at', '-id').first()

    def get_project(self, obj):
        try:
            project_tags = obj.tag_organization.select_related('tag', 'tag__type').filter(
                tag__type__category__iexact='PROJECT'
            ).order_by('tag__name', 'id')
            return list(project_tags.values_list('tag__name', flat=True).distinct())
        except Exception:
            return []

    def get_cadre(self, obj):
        try:
            latest = self._latest_tag_by_category(obj, 'CADRE')
            return latest.tag.name if latest and latest.tag else None
        except Exception:
            return None

    def get_state(self, obj):
        try:
            latest = self._latest_tag_by_category(obj, 'STATE')
            return latest.tag.name if latest and latest.tag else None
        except Exception:
            return None

class OrgDetailSerializer(serializers.ModelSerializer):
    healthy_farms = serializers.IntegerField()
    stressed_farms = serializers.IntegerField()
    damaged_farms = serializers.IntegerField()
    stressed_farms_acres = serializers.DecimalField(max_digits=12,decimal_places=6)
    healthy_farms_acres = serializers.DecimalField(max_digits=12,decimal_places=6)
    damaged_farms_acres = serializers.DecimalField(max_digits=12,decimal_places=6)
    group_members = serializers.SerializerMethodField()  # ← New field
    total_farms = serializers.SerializerMethodField()


    class Meta:
        model = models.organizations
        fields = ('id','acres','stressed_farms_acres','healthy_farms_acres','damaged_farms_acres','members','crops','healthy_farms','stressed_farms','damaged_farms',
            'group_members','total_farms')
    
    def get_total_farms(self, obj):
        return models.farm.objects.filter(org_id=obj.id).count()

    def get_group_members(self, obj):
        
        if obj.group_org:
            # Org is a member → return all members of its group
            members = obj.group_org.child_organizations.all()
        else:
            return []

        # Return list of dicts with basic info (customize as needed)
        return [
            {
                "id": member.id,
                "org_name": member.org_name,
                "acres": member.acres,
                "members": member.members
            }
            for member in members
        ]
class sociallistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.social_post
        fields = '__all__'
        depth=1

    def create(self, validated_data):
        instance = models.social_post.objects.create(**validated_data)
        instance.save()

class SocialPostTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SocialPostTag
        fields = '__all__'
      

class userblocklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.user_reporting
        fields = '__all__'
        depth=1

class adduserblocklistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.user_reporting
        fields = '__all__'


class addsocialSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.social_post
        fields = '__all__'

    def create(self, validated_data):
        instance = models.social_post.objects.create(**validated_data)
        instance.save()
        return instance
class hastaglistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.hashtag_master
        fields = '__all__'

class friendslistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.friends_master
        fields = '__all__'

class locationlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.location_master
        fields = '__all__'

class hashtab_imageslistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.social_post
        fields = '__all__'
        depth=1
    def create(self, validated_data):
        instance = models.social_post.objects.create(**validated_data)
        instance.save()
        return instance
    
    
class agentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.agents
        fields = '__all__'

class addagentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.agents
        fields = '__all__'

class userpincodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.user
        fields = ('id','pincode')

class key_serializer(serializers.ModelSerializer):
    class Meta:
        model=models.tb_application_access
        fields='__all__'

class agent_summary_filter(serializers.ModelSerializer):
    class Meta:
        model=models.user
        fields='__all__'

class orderDetailsSerializerbyId(serializers.ModelSerializer):
    class Meta:
        model = models.order_details
        fields = '__all__'
        depth = 1

class brandlistfilterSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.brand_master
        fields='__all__'

class brandlistSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.brand_master
        fields="__all__"

class addnotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.notification
        fields="__all__"

class partnerlistSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.partner_list
        fields="__all__"
        depth=1

class ModifyaddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.delivery_address
        fields = "__all__" # ('user_id','delivery_pincode','location','location1','house','landmark','notes')

class HomePageFarmSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.farm
        fields = ('id','my_plot_id','season_id','crop_id')

class CropsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.crop_master
        fields = ('id','crop_name','crop_selected_icon_url')

class FullOrgDetailSerializer(serializers.ModelSerializer):
    crop_list= serializers.SerializerMethodField('get_crops')
    group_members = serializers.SerializerMethodField()  # ← New field


    def get_crops(self,obj):
        return CropsListSerializer(obj.crops_interest,many=True).data
    
    def get_group_members(self, obj):
        if obj.group_org:
            # Org is a member → return all members of its group
            members = obj.group_org.child_organizations.all()
        else:
            return []

        # Return list of dicts with basic info (customize as needed)
        return [
            {
                "id": member.id,
                "org_name": member.org_name,
                "acres": member.acres,
                "members": member.members
            }
            for member in members
        ]
    
    class Meta:
        model = models.organizations
        fields = ('id','org_name','org_type','logo','number_of_members',
            'group_members','myplot_company_id','company_id','room_100ms','map_layer','latitude','longitude','zoom','carousel1','carousel2','carousel3','carousel4','members','acres','crops','cin','is_verified','pincode','country','state','district','taluka','village','share_capital','paid_capital','status','reviewed','manual_address','fpo_contact_no','geometry','type_of_org','crop_list','description','stress','damaged','health','relationship_manager_name','relationship_manager_no','turnover','active_date','member_associate','room_hostcode','room_guestcode')

class UserRoleSerializer(serializers.ModelSerializer):
    permissions= serializers.SerializerMethodField('get_permissions')

    def get_permissions(self,obj):
        return list(obj.permissions.filter(Q(api__isnull=True)|Q(api__exact='')).values_list('slug', flat=True))
    
    class Meta:
        model = models.user_roles
        fields = ('id','role_name','permissions',)

class GetCountriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('id','name','code','mobile_code','phone_len')


class SocialprofileSerializer(serializers.ModelSerializer):
    farm= serializers.SerializerMethodField('get_farm')
    organization= serializers.SerializerMethodField('get_organization')
    crop_list= serializers.SerializerMethodField('get_crops')
    user_role= serializers.SerializerMethodField('get_user_role')
    country= serializers.SerializerMethodField('get_country')
    edit_org_role= serializers.SerializerMethodField('get_edit_org_role')

    def get_farm(self,obj):
        if not obj or not obj.created_by30.exists():
            return None
        return HomePageFarmSerializer(obj.created_by30.first(),many=False).data
    
    def get_organization(self,obj):
        if not obj or not obj.organization:
            return None
        return FullOrgDetailSerializer(obj.organization,many=False).data
    
    def get_crops(self,obj):
        if not obj or not obj.crops_interest:
            return None
        return CropsListSerializer(obj.crops_interest,many=True).data
    
    def get_user_role(self,obj):
        if not obj or not obj.user_role:
            return None
        return UserRoleSerializer(obj.user_role,many=False).data
    
    def get_country(self,obj):
        if not obj or not obj.country:
            return None
        return GetCountriesSerializer(obj.country,many=False).data
    
    def get_edit_org_role(self,obj):
        return obj.user_change_role_org.count()
    
    class Meta:
        model=models.user
        fields=('full_name','edit_org_role','full_name_telugu','mobile_number','is_allowed_group','country','bio','bio_telugu','user_profile_img','firebase_token','organization','admin','can_edit_org_details','user_role','email','farm','land_size','address_pincode','address_country','address_state','address_district','address_taluka','address_village','crop_list','description','is_2fa_enabled','google_auth_secret')
        depth = 1

class EditSocialprofileSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.user
        fields = ('id','organization','user_role','language_selected','admin','mobile_number','otp_verfied','full_name','full_name_telugu','land_size','land_size_unit','land_size_unit_telugu','crop_interest','address_pincode','address_country','address_state','address_district','address_taluka','address_village','bio','bio_telugu','user_profile_img_file','user_profile_img','installed_app','timestamp')
        depth = 1

class productfiltercrop(serializers.ModelSerializer):
    class Meta:
        model=models.product_master
        exclude=('hp',)

class productfiltermachine(serializers.ModelSerializer):
    class Meta:
        model=models.product_master
        exclude=('crop',)

class productsecondfilter(serializers.ModelSerializer):
    class Meta:
        model=models.product_master
        fields='__all__'

class Crop_list_filterSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.product_master
        fields=('crop',)

class Hp_list_filterSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.product_master
        fields=("hp",)



class Productlist_with_variantlistSerializer(serializers.ModelSerializer):
    variants = productvariantlistSerializer(many=True)
    class Meta:
        model = models.product_master
        fields = '__all__'

class Valid_Coupon_Serializer(serializers.ModelSerializer):
    class Meta:
        model=models.coupon_details
        fields=("id","display_name",'coupon_code',"applicable_product_id","applicable_brand_id")

class Coupon_Details_Serializer(serializers.ModelSerializer):
    class Meta:
        model=models.coupon_details
        fields="__all__"

class chemicalSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.chemical_master
        fields='__all__'

class seedSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.seed_master
        fields='__all__'

class implementSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.implement_master
        fields='__all__'

class machineSerializer(serializers.ModelSerializer):
    class Meta:
        model=models.machine_master
        fields='__all__'

class Productlist_with_variantlistSerializer(serializers.ModelSerializer):
    variants = productvariantlistSerializer(many=True)
    class Meta:
        model = models.product_master
        fields = '__all__'

class Valid_Coupon_Serializer(serializers.ModelSerializer):
    class Meta:
        model=models.coupon_details
        fields=("id","display_name",'coupon_code',"applicable_product_id","applicable_brand_id")

class Coupon_Details_Serializer(serializers.ModelSerializer):
    class Meta:
        model=models.coupon_details
        fields="__all__"


class activityaddSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.activity
        fields = '__all__'

class activitylistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.activity
        fields = ('id','activity_name','activity_name_telugu','plot_id','plot_id_telugu','activity_id','start_timestamp','end_timestamp','total_hours','total_area','area_unit')
        depth=1

class activity_masteraddSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.activity_master
        fields = '__all__'

class activity_masterlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.activity_master
        fields = ('id','user_id','activity_name','activity_name_telugu')
        depth=1

class aryadhan_inquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.aryadhan_inquiry
        fields = '__all__'

class offer_inquirySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.offer_inquiry
        fields = '__all__'

class addlivefeedSerializer(serializers.ModelSerializer):

    room_guestcode= serializers.SerializerMethodField('get_room_guestcode')
    room_hostcode= serializers.SerializerMethodField('get_room_hostcode')
    room_100ms= serializers.SerializerMethodField('get_room_100ms')

    def get_room_guestcode(self,obj):
        return obj.org_id.room_guestcode
    
    def get_room_hostcode(self,obj):
        return obj.org_id.room_hostcode
    
    def get_room_100ms(self,obj):
        return obj.org_id.room_100ms

    class Meta:
        model = models.live_feed
        fields = ["id","start_timestamp","room_guestcode","room_hostcode","room_100ms", "end_timestamp","url","notes","number_of_attendees", "screenshot_recording", "video_recording","started_by_user_id","org_id","agenda","status"]

class livefeedSerializer(serializers.ModelSerializer):
    room_guestcode= serializers.SerializerMethodField('get_room_guestcode')
    room_hostcode= serializers.SerializerMethodField('get_room_hostcode')
    room_100ms= serializers.SerializerMethodField('get_room_100ms')

    def get_room_guestcode(self,obj):
        return obj.org_id.room_guestcode
    
    def get_room_hostcode(self,obj):
        return obj.org_id.room_hostcode
    
    def get_room_100ms(self,obj):
        return obj.org_id.room_100ms
    class Meta:
        model = models.live_feed
        fields = ["id","start_timestamp","room_guestcode","room_hostcode","room_100ms", "end_timestamp","url","notes","number_of_attendees", "screenshot_recording", "video_recording","started_by_user_id","org_id","agenda","status"]

class org_member_listSerializer(serializers.ModelSerializer):
    kyc_documents= serializers.SerializerMethodField('get_kyc_documents')

    def get_kyc_documents(self,obj):
        docs = list(obj.document_user.filter(status=1).values_list('type', flat=True))
        if obj.otp_verfied:
            docs.append('otp_verified')
        return docs
    
    class Meta:
        model = models.user
        fields = ('id','organization','kyc_documents','address_state','address_district','address_taluka','address_village','full_name','mobile_number','language_selected')


class AdminManagedUserListSerializer(serializers.ModelSerializer):
    role_name = serializers.SerializerMethodField()
    organization_name = serializers.SerializerMethodField()

    def get_role_name(self, obj):
        if obj.user_role:
            return obj.user_role.role_name
        return None

    def get_organization_name(self, obj):
        if obj.organization:
            return obj.organization.org_name
        return None

    class Meta:
        model = models.user
        fields = (
            'id',
            'full_name',
            'mobile_number',
            'email',
            'is_active',
            'admin',
            'is_cvrp',
            'can_edit_org_details',
            'user_role',
            'role_name',
            'organization',
            'organization_name',
            'installed_app',
            'timestamp',
        )


class UserActiveStatusUpdateSerializer(serializers.Serializer):
    is_active = serializers.BooleanField(required=True)


class UserCVRPStatusUpdateSerializer(serializers.Serializer):
    is_cvrp = serializers.BooleanField(required=True)


class OrganizationManagementUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.organizations
        fields = (
            'org_name',
            'org_type',
            'logo',
            'number_of_members',
            'manual_address',
            'fpo_contact_no',
            'pincode',
            'country',
            'state',
            'district',
            'taluka',
            'village',
            'description',
            'relationship_manager_name',
            'relationship_manager_no',
            'name_of_bds',
            'status',
            'is_active',
        )

class complianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.compliance
        fields = '__all__'

class addinputcatalogueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.input_catalogue
        fields = '__all__'

class inputcatalogueSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.input_catalogue
        fields = '__all__'
        depth=1

class product_categorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.product_category
        fields = '__all__'

class addfarmer_requestSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.farmer_request
        fields = '__all__'


class farmer_requestSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.farmer_request
        fields = '__all__'
        depth=1

class app_configurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.app_configuration
        fields = '__all__'
# This is the new change we have made
class update_user_profile(serializers.ModelSerializer):
    class Meta:
        model = models.user
        fields = ['email','full_name',' mobile_number','full_name_telugu']

class UserWithTaskCountSerializer(serializers.ModelSerializer):
    task_count = serializers.IntegerField()
    class Meta:
        model = models.user
        fields = ['id','email','full_name','mobile_number','task_count']

class update_image_profile(serializers.ModelSerializer):
    class Meta:
        model = models.user
        fields = ['user_profile_img']

class phonenumber_exist(serializers.ModelSerializer):
  class Meta:
      model = models.user_phonenumber_map
      fields = '__all__'


class ScoreGeneralFarmerSerializer(serializers.ModelSerializer):
    class Meta:
        model= ScoreGeneralFarmer
        fields="__all__"
    

class FarmerSerializer(serializers.ModelSerializer):
    farmer_general_data=serializers.SerializerMethodField('get_farmer_general_data')
    crop_list= serializers.SerializerMethodField('get_crops')

    def get_farmer_general_data(self,obj):
        if not obj or not obj.score_general_farmer.exists():
            return []
        return ScoreGeneralFarmerSerializer(obj.score_general_farmer.all(),many=True).data

    def get_crops(self,obj):
        if not obj or not obj.crops_interest:
            return []
        return CropsListSerializer(obj.crops_interest,many=True).data

    class Meta:
      model = models.user
      fields = ['id','full_name','mobile_number','latitude','longitude','crop_list','land_size','land_size_unit','address_district','address_state','address_taluka','address_country','user_profile_img','user_profile_img_file','farmer_general_data']



class FarmSerializerVikshep(serializers.ModelSerializer):
    farmer_name = serializers.CharField(source='name')
    farm_area = serializers.DecimalField(source='total_area', max_digits=8, decimal_places=2)
    farm_addition_date = serializers.DateField()
    farmer_mobile_number = serializers.CharField(source='farmer_contact')
    farm_latitude = serializers.DecimalField(source='latitude', max_digits=16, decimal_places=8)
    farm_longitude = serializers.DecimalField(source='longitude', max_digits=16, decimal_places=8)
    
    farm_crop = serializers.SerializerMethodField('get_farm_crop')
    def get_farm_crop(self,obj):
        return obj.farm_crop
    company_id = serializers.SerializerMethodField('get_company_id')
    def get_company_id(self,obj):
        return obj.company_id
    org_name = serializers.SerializerMethodField('get_company_name')
    def get_company_name(self,obj):
        return obj.org_name
    farm_id = serializers.CharField()
    prakshep_id = serializers.CharField()

    class Meta:
        model = models.farm
        fields = (
            'farmer_name', 'farm_area', 'area_unit', 'farm_addition_date', 'farmer_mobile_number',
            'farm_latitude', 'farm_longitude', 'farm_country', 'farm_state', 'farm_district', 'farm_taluka',
            'farm_village', 'farm_crop', 'company_id', 'org_name', 'farm_id', 'prakshep_id','season_id'
        )


class SellRecordsSerializer(serializers.ModelSerializer):
    selected_user_name=serializers.SerializerMethodField('get_selected_user_name')
    product_name= serializers.SerializerMethodField('get_product_name')

    def get_selected_user_name(self,obj):
        return obj.selected_user.full_name

    def get_product_name(self,obj):
        return obj.product.name
    class Meta:
        model = models.SellRecords
        fields = ['id',"date_time","selected_user_name","product_name","qty","rate","amount","remarks","created_at","updated_at","user_added","selected_user","product"]


class DeviceDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.DeviceData
        fields = '__all__'


class UserDeviceSerializer(serializers.ModelSerializer):
    device_name = serializers.CharField(source='device.device_name', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = models.UserDevice
        fields = ['id', 'user', 'user_name', 'device', 'device_name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class UserDeviceManagementSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = models.UserDeviceManagement
        fields = ['id', 'user', 'user_name', 'device_id', 'device_name', 'device_type', 'device_os', 
                  'device_model', 'is_active', 'last_used', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']


class DeviceActionSerializer(serializers.Serializer):
    """Serializer for device management actions (login, logout)"""
    action = serializers.ChoiceField(choices=['login', 'logout'])
    user_id = serializers.IntegerField()
    device_id = serializers.CharField(max_length=255)
    device_type = serializers.CharField(max_length=20, required=False)
    model = serializers.CharField(max_length=255, required=False)
    os = serializers.CharField(max_length=255, required=False)
    device_name = serializers.CharField(max_length=200, required=False)

    def validate_device_id(self, value):
        value = str(value or '').strip()
        if not value:
            raise serializers.ValidationError('This field may not be blank.')
        return value
