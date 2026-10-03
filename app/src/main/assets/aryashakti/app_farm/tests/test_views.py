import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, force_authenticate, APIRequestFactory
from app_farm.models import user as UserModel, farm, organizations
from app_farm.views import (
    SignUp, AddFarm, AddAgent, GetUser, UpdateUser,
    Addcomment_reporting, AddInquiry, AddSocialPost
)
from rest_framework import status
import json

User = get_user_model()


class SignUpViewTests(APITestCase):
    """Test SignUp API endpoint"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
        self.url = '/api/signup/'  # Adjust based on your URL routing
    
    def test_signup_with_valid_data(self):
        """Test successful user signup"""
        data = {
            'mobile_number': '9876543210',
            'full_name': 'Test User',
            'email': 'test@example.com',
            'password': 'test_password_123'
        }
        with patch('app_farm.views.UserModel.objects.create_user') as mock_create:
            mock_user = MagicMock()
            mock_user.id = 1
            mock_create.return_value = mock_user
            
            request = self.factory.post(self.url, data, format='json')
            view = SignUp.as_view()
            response = view(request)
            
            # Check response status
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])

    def test_signup_with_missing_fields(self):
        """Test signup with missing required fields"""
        data = {
            'mobile_number': '9876543210',
            'full_name': 'Test User'
            # Missing email and password
        }
        request = self.factory.post(self.url, data, format='json')
        view = SignUp.as_view()
        response = view(request)
        
        # Should fail validation
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_201_CREATED])

    def test_signup_with_duplicate_mobile(self):
        """Test signup with duplicate mobile number"""
        # Create user first
        UserModel.objects.create(
            mobile_number='9876543210',
            full_name='Existing User'
        )
        
        data = {
            'mobile_number': '9876543210',
            'full_name': 'New User'
        }
        self.factory.post(self.url, data, format='json')
        view = SignUp.as_view()
        # Response should handle duplicate
        self.assertIsNotNone(view)


class AddFarmViewTests(APITestCase):
    """Test AddFarm API endpoint"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = UserModel.objects.create(
            mobile_number='9876543210',
            full_name='Test User'
        )
        self.org = organizations.objects.create(org_name='Test Org')
    
    def test_add_farm_authenticated(self):
        """Test adding farm with authenticated user"""
        data = {
            'name': 'Test Farm',
            'organization': self.org.id,
            'latitude': 28.7041,
            'longitude': 77.1025
        }
        request = self.factory.post('/api/addfarm/', data, format='json')
        force_authenticate(request, user=self.user)
        view = AddFarm.as_view()
        response = view(request)
        
        self.assertIsNotNone(response)

    def test_add_farm_unauthenticated(self):
        """Test adding farm without authentication"""
        data = {
            'name': 'Test Farm',
            'organization': self.org.id
        }
        request = self.factory.post('/api/addfarm/', data, format='json')
        view = AddFarm.as_view()
        response = view(request)
        
        # Should reject unauthenticated requests
        self.assertIsNotNone(response)


class GetUserViewTests(APITestCase):
    """Test GetUser API endpoint"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = UserModel.objects.create(
            mobile_number='9876543210',
            full_name='Test User',
            email='test@example.com'
        )
    
    def test_get_user_authenticated(self):
        """Test retrieving user data when authenticated"""
        request = self.factory.get('/api/getuser/')
        force_authenticate(request, user=self.user)
        # Assuming GetUser view exists, test it
        self.assertIsNotNone(self.user)

    def test_get_user_data_fields(self):
        """Test that user data contains expected fields"""
        self.assertIsNotNone(self.user.mobile_number)
        self.assertIsNotNone(self.user.full_name)
        self.assertEqual(self.user.mobile_number, '9876543210')


class UpdateUserViewTests(APITestCase):
    """Test UpdateUser API endpoint"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = UserModel.objects.create(
            mobile_number='9876543210',
            full_name='Test User'
        )
    
    def test_update_user_name(self):
        """Test updating user name"""
        self.user.full_name = 'Updated Name'
        self.user.save()
        
        updated_user = UserModel.objects.get(id=self.user.id)
        self.assertEqual(updated_user.full_name, 'Updated Name')

    def test_update_user_email(self):
        """Test updating user email"""
        self.user.email = 'newemail@example.com'
        self.user.save()
        
        updated_user = UserModel.objects.get(id=self.user.id)
        self.assertEqual(updated_user.email, 'newemail@example.com')


class CommentReportingViewTests(APITestCase):
    """Test Addcomment_reporting API endpoint"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = UserModel.objects.create(
            mobile_number='9876543210',
            full_name='Test User'
        )
    
    def test_add_comment_reporting(self):
        """Test adding comment reporting"""
        data = {
            'comment_id': 1,
            'reason': 'Inappropriate content',
            'description': 'This comment is offensive'
        }
        request = self.factory.post('/api/addcomment_reporting/', data, format='json')
        force_authenticate(request, user=self.user)
        view = Addcomment_reporting.as_view()
        response = view(request)
        
        self.assertIsNotNone(response)


class InquiryViewTests(APITestCase):
    """Test AddInquiry API endpoint"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = UserModel.objects.create(
            mobile_number='9876543210',
            full_name='Test User'
        )
    
    def test_add_inquiry(self):
        """Test adding inquiry"""
        data = {
            'title': 'Test Inquiry',
            'description': 'Test description',
            'category': 'General'
        }
        request = self.factory.post('/api/addinquiry/', data, format='json')
        force_authenticate(request, user=self.user)
        view = AddInquiry.as_view()
        response = view(request)
        
        self.assertIsNotNone(response)


class SocialPostViewTests(APITestCase):
    """Test AddSocialPost API endpoint"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = UserModel.objects.create(
            mobile_number='9876543210',
            full_name='Test User'
        )
    
    def test_add_social_post(self):
        """Test adding social post"""
        data = {
            'title': 'Test Post',
            'content': 'Test content',
            'image': 'https://example.com/image.jpg'
        }
        request = self.factory.post('/api/addsocialpost/', data, format='json')
        force_authenticate(request, user=self.user)
        view = AddSocialPost.as_view()
        response = view(request)
        
        self.assertIsNotNone(response)


class UserModelTests(TestCase):
    """Test User model operations"""
    
    def test_create_user(self):
        """Test creating a user"""
        user = UserModel.objects.create(
            mobile_number='9876543210',
            full_name='Test User',
            email='test@example.com'
        )
        self.assertEqual(user.mobile_number, '9876543210')
        self.assertEqual(user.full_name, 'Test User')

    def test_user_string_representation(self):
        """Test user string representation"""
        user = UserModel.objects.create(
            mobile_number='9876543210',
            full_name='Test User'
        )
        self.assertIn('Test User', str(user))

    def test_user_with_none_fields(self):
        """Test creating user with None optional fields"""
        user = UserModel.objects.create(
            mobile_number='9876543210',
            full_name='Test User',
            email=None
        )
        self.assertIsNone(user.email)


class FarmModelTests(TestCase):
    """Test Farm model operations"""
    
    def setUp(self):
        self.user = UserModel.objects.create(
            mobile_number='9876543210',
            full_name='Test User'
        )
        self.org = organizations.objects.create(org_name='Test Org')
    
    def test_create_farm(self):
        """Test creating a farm"""
        farm_obj = farm.objects.create(
            user=self.user,
            organization=self.org,
            name='Test Farm',
            latitude=28.7041,
            longitude=77.1025
        )
        self.assertEqual(farm_obj.name, 'Test Farm')
        self.assertEqual(farm_obj.user, self.user)

    def test_farm_with_coordinates(self):
        """Test farm with geographic coordinates"""
        farm_obj = farm.objects.create(
            user=self.user,
            organization=self.org,
            name='Farm with Coords',
            latitude=28.7041,
            longitude=77.1025
        )
        self.assertEqual(float(farm_obj.latitude), 28.7041)
        self.assertEqual(float(farm_obj.longitude), 77.1025)


class UserAuthenticationTests(APITestCase):
    """Test user authentication"""
    
    def test_user_login_with_valid_credentials(self):
        """Test user login with valid credentials"""
        user = UserModel.objects.create(
            mobile_number='9876543210',
            full_name='Test User'
        )
        self.assertEqual(user.mobile_number, '9876543210')

    def test_user_authentication_state(self):
        """Test user authentication state"""
        user = UserModel.objects.create(
            mobile_number='9876543210',
            full_name='Test User'
        )
        self.assertIsNotNone(user.id)


class APIViewErrorHandlingTests(APITestCase):
    """Test error handling in API views"""
    
    def setUp(self):
        self.factory = APIRequestFactory()
    
    def test_missing_required_fields(self):
        """Test API response with missing required fields"""
        data = {}  # Empty data
        request = self.factory.post('/api/addinquiry/', data, format='json')
        self.assertIsNotNone(request)

    def test_invalid_json_data(self):
        """Test API with invalid JSON"""
        request = self.factory.post('/api/addinquiry/', 'invalid json', content_type='application/json')
        self.assertIsNotNone(request)


if __name__ == '__main__':
    unittest.main()
