from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import status
from unittest.mock import patch
import json
import uuid

from app_farm.models import user as UserModel, organizations, user_roles
from .models import Requests
from .views import (
    CreateFpoRequest,
    CreateFarmerToFpoRequest,
    RequestsList,
    RequestsUpdate,
)


class RequestsModelTests(TestCase):
    """Test cases for Requests model"""

    @classmethod
    def setUpClass(cls):
        """Create required fixtures"""
        super().setUpClass()
        user_roles.objects.get_or_create(id=1, defaults={'role_name': 'Farmer'})

    def setUp(self):
        """Set up test data"""
        self.user_obj = UserModel.objects.create(
            mobile_number=9876543210,
            full_name='Test User'
        )
        self.organization = organizations.objects.create(
            org_name='Test Organization',
            company_id='test_' + str(uuid.uuid4())[:8]
        )

    def test_requests_model_creation(self):
        """Test creating a Requests object"""
        request_obj = Requests.objects.create(
            type='New FPO Request',
            user=self.user_obj,
            organization=self.organization,
            status=2,
            org_name='Test FPO',
            org_no='12345'
        )
        self.assertEqual(request_obj.type, 'New FPO Request')
        self.assertEqual(request_obj.org_name, 'Test FPO')

    def test_requests_str_method(self):
        """Test __str__ method"""
        request_obj = Requests.objects.create(
            type='New FPO Request',
            user=self.user_obj,
            status=2
        )
        result = str(request_obj)
        self.assertIn(str(request_obj.id), result)

    def test_requests_with_farmer_to_fpo_type(self):
        """Test Farmer to FPO request type"""
        request_obj = Requests.objects.create(
            type='Farmer to FPO Request',
            user=self.user_obj,
            organization=self.organization,
            status=2
        )
        self.assertEqual(request_obj.type, 'Farmer to FPO Request')

    def test_requests_status_default(self):
        """Test default status value"""
        request_obj = Requests.objects.create(
            type='New FPO Request',
            user=self.user_obj
        )
        self.assertEqual(request_obj.status, 2)

    def test_requests_organization_nullable(self):
        """Test that organization can be null"""
        request_obj = Requests.objects.create(
            type='New FPO Request',
            user=self.user_obj,
            status=2,
            org_name='Test FPO'
        )
        self.assertIsNone(request_obj.organization)

    def test_requests_blank_fields(self):
        """Test blank fields can be empty"""
        request_obj = Requests.objects.create(
            type='New FPO Request',
            user=self.user_obj
        )
        self.assertEqual(request_obj.org_name, '')
        self.assertEqual(request_obj.org_no, '')

    def test_requests_type_choices(self):
        """Test type field choices"""
        choices = [choice[0] for choice in Requests._meta.get_field('type').choices]
        self.assertIn('New FPO Request', choices)
        self.assertIn('Farmer to FPO Request', choices)

    def test_requests_manager_exists(self):
        """Test that RequestsManager exists"""
        self.assertEqual(type(Requests.objects).__name__, 'RequestsManager')


class CreateFpoRequestViewTests(TestCase):
    """Test cases for CreateFpoRequest view"""

    @classmethod
    def setUpClass(cls):
        """Create required fixtures"""
        super().setUpClass()
        user_roles.objects.get_or_create(id=1, defaults={'role_name': 'Farmer'})

    def setUp(self):
        """Set up test data"""
        self.factory = APIRequestFactory()
        self.user_obj = UserModel.objects.create(
            mobile_number=9876543211,
            full_name='Test User'
        )
        self.view = CreateFpoRequest.as_view()

    @patch('all_requests.views.CustomTokenAuthentication.authenticate')
    def test_create_fpo_request_success(self, mock_auth):
        """Test successful FPO request creation"""
        mock_auth.return_value = (self.user_obj, None)
        
        data = {'name': 'New FPO', 'phone': 9876543210}
        request = self.factory.post('/create-fpo-request/', data, format='json')
        request.user = self.user_obj
        request.auth = None
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('all_requests.views.CustomTokenAuthentication.authenticate')
    def test_create_fpo_request_empty_body(self, mock_auth):
        """Test FPO request with empty body"""
        mock_auth.return_value = (self.user_obj, None)
        request = self.factory.post('/create-fpo-request/', None, format='json')
        request.user = self.user_obj
        request.auth = None
        request.data = None
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('all_requests.views.CustomTokenAuthentication.authenticate')
    def test_create_fpo_request_invalid_data(self, mock_auth):
        """Test FPO request with invalid data"""
        mock_auth.return_value = (self.user_obj, None)
        data = {'name': 'FPO'}
        request = self.factory.post('/create-fpo-request/', data, format='json')
        request.user = self.user_obj
        request.auth = None
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('all_requests.views.CustomTokenAuthentication.authenticate')
    def test_get_extra_actions(self, mock_auth):
        """Test get_extra_actions method"""
        result = CreateFpoRequest.get_extra_actions()
        self.assertEqual(result, [])


class CreateFarmerToFpoRequestViewTests(TestCase):
    """Test cases for CreateFarmerToFpoRequest view"""

    @classmethod
    def setUpClass(cls):
        """Create required fixtures"""
        super().setUpClass()
        user_roles.objects.get_or_create(id=1, defaults={'role_name': 'Farmer'})

    def setUp(self):
        """Set up test data"""
        self.factory = APIRequestFactory()
        self.user_obj = UserModel.objects.create(
            mobile_number=9876543212,
            full_name='Test User'
        )
        self.organization = organizations.objects.create(
            org_name='Test FPO',
            company_id='test_' + str(uuid.uuid4())[:8]
        )
        self.view = CreateFarmerToFpoRequest.as_view()

    @patch('all_requests.views.CustomTokenAuthentication.authenticate')
    def test_create_farmer_to_fpo_success(self, mock_auth):
        """Test successful Farmer to FPO request"""
        mock_auth.return_value = (self.user_obj, None)
        data = {'org_id': self.organization.id}
        request = self.factory.post('/create-farmer-to-fpo/', data, format='json')
        request.user = self.user_obj
        request.auth = None
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('all_requests.views.CustomTokenAuthentication.authenticate')
    def test_create_farmer_to_fpo_empty_body(self, mock_auth):
        """Test with empty body"""
        mock_auth.return_value = (self.user_obj, None)
        request = self.factory.post('/create-farmer-to-fpo/', None, format='json')
        request.user = self.user_obj
        request.auth = None
        request.data = None
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('all_requests.views.CustomTokenAuthentication.authenticate')
    def test_get_extra_actions(self, mock_auth):
        """Test get_extra_actions method"""
        result = CreateFarmerToFpoRequest.get_extra_actions()
        self.assertEqual(result, [])


class RequestsListViewTests(TestCase):
    """Test cases for RequestsList view"""

    @classmethod
    def setUpClass(cls):
        """Create required fixtures"""
        super().setUpClass()
        user_roles.objects.get_or_create(id=1, defaults={'role_name': 'Farmer'})

    def setUp(self):
        """Set up test data"""
        self.factory = APIRequestFactory()
        self.user_obj = UserModel.objects.create(
            mobile_number=9876543213,
            full_name='Test User'
        )
        self.organization = organizations.objects.create(
            org_name='Test FPO List',
            company_id='test_' + str(uuid.uuid4())[:8]
        )
        self.view = RequestsList.as_view()

    @patch('all_requests.views.CustomTokenAuthentication.authenticate')
    def test_requests_list_success(self, mock_auth):
        """Test successful list retrieval"""
        mock_auth.return_value = (self.user_obj, None)
        data = {'org_id': self.organization.id, 'status': 2}
        request = self.factory.post('/requests-list/', data, format='json')
        request.user = self.user_obj
        request.auth = None
        response = self.view(request)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT])

    @patch('all_requests.views.CustomTokenAuthentication.authenticate')
    def test_requests_list_empty_body(self, mock_auth):
        """Test with empty body"""
        mock_auth.return_value = (self.user_obj, None)
        request = self.factory.post('/requests-list/', None, format='json')
        request.user = self.user_obj
        request.auth = None
        request.data = None
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('all_requests.views.CustomTokenAuthentication.authenticate')
    def test_get_extra_actions(self, mock_auth):
        """Test get_extra_actions method"""
        result = RequestsList.get_extra_actions()
        self.assertEqual(result, [])


class RequestsUpdateViewTests(TestCase):
    """Test cases for RequestsUpdate view"""

    @classmethod
    def setUpClass(cls):
        """Create required fixtures"""
        super().setUpClass()
        user_roles.objects.get_or_create(id=1, defaults={'role_name': 'Farmer'})

    def setUp(self):
        """Set up test data"""
        self.factory = APIRequestFactory()
        self.user_obj = UserModel.objects.create(
            mobile_number=9876543214,
            full_name='Test User'
        )
        self.organization = organizations.objects.create(
            org_name='Test FPO Update',
            company_id='test_' + str(uuid.uuid4())[:8]
        )
        self.request_obj = Requests.objects.create(
            type='Farmer to FPO Request',
            user=self.user_obj,
            organization=self.organization,
            status=2
        )
        self.view = RequestsUpdate.as_view()

    @patch('all_requests.views.CustomTokenAuthentication.authenticate')
    def test_update_request_success(self, mock_auth):
        """Test successful request update"""
        mock_auth.return_value = (self.user_obj, None)
        data = {'req_id': self.request_obj.id, 'status': 1}
        request = self.factory.post('/requests-update/', data, format='json')
        request.user = self.user_obj
        request.auth = None
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('all_requests.views.CustomTokenAuthentication.authenticate')
    def test_update_request_empty_body(self, mock_auth):
        """Test with empty body"""
        mock_auth.return_value = (self.user_obj, None)
        request = self.factory.post('/requests-update/', None, format='json')
        request.user = self.user_obj
        request.auth = None
        request.data = None
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('all_requests.views.CustomTokenAuthentication.authenticate')
    def test_update_request_invalid_data(self, mock_auth):
        """Test with invalid data"""
        mock_auth.return_value = (self.user_obj, None)
        data = {'req_id': self.request_obj.id}
        request = self.factory.post('/requests-update/', data, format='json')
        request.user = self.user_obj
        request.auth = None
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('all_requests.views.CustomTokenAuthentication.authenticate')
    def test_get_extra_actions(self, mock_auth):
        """Test get_extra_actions method"""
        result = RequestsUpdate.get_extra_actions()
        self.assertEqual(result, [])
