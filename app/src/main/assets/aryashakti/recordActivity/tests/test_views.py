import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from recordActivity.views import GetAllActivity, GetActivityFields
from app_farm.models import user, organizations, farm
from recordActivity.models import ActivityRecord
from django.contrib.auth import get_user_model


class TestViews(APITestCase):

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            mobile_number='1234567890', password='password'
        )
        self.org = organizations.objects.create(org_name='Test Org')
        self.user.organization = self.org
        self.user.save()
        self.farm = farm.objects.create(
            user=self.user, organization=self.org, name='Test Farm'
        )
        self.activity = ActivityRecord.objects.create(
            name='Test Activity', organization=self.org
        )
        self.client.force_authenticate(user=self.user)

    def test_get_all_activity(self):
        url = reverse('get_all_activity')  # Assuming you have URL names
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)

    def test_get_activity_fields_success(self):
        url = reverse('get_activity_fields', args=[self.farm.id, self.activity.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_activity_fields_farm_not_found(self):
        url = reverse('get_activity_fields', args=[999, self.activity.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)  # Assuming error code

    # Add more view tests as needed for other endpoints

    @patch('recordActivity.views.insert_into_remote_db')
    @patch('recordActivity.views.OpenAIAPIIntegration')
    def test_some_view_with_mocks(self, mock_openai, mock_insert):
        # Example for views that use external services
        mock_openai.return_value = MagicMock()
        mock_insert.return_value = None
        # Test the view


if __name__ == '__main__':
    unittest.main()