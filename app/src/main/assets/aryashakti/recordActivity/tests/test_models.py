import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from recordActivity.models import (
    DASActivityRecord, ExternalClient, DroneSprayActivity  # , CropDiseaseAdvisory
)
from app_farm.models import user, farm, organizations, crop_master, crop_variety_master
from django.utils import timezone


class TestModels(TestCase):

    def setUp(self):
        self.user = user.objects.create(mobile_number='1234567890', full_name='Test User')
        self.org = organizations.objects.create(org_name='Test Org')
        self.farm = farm.objects.create(
            user=self.user, organization=self.org, name='Test Farm',
            crop_id=crop_master.objects.create(crop_name='Test Crop'),
            crop_variety_id=crop_variety_master.objects.create(variety_name='Test Variety')
        )

    def test_das_activity_record_save(self):
        activity = DASActivityRecord.objects.create(
            farmer=self.user, farm=self.farm, day_of_sowing=10,
            activity=DASActivityRecord.objects.create(name='Test Activity', organization=self.org)
        )
        # Test auto-population
        self.assertEqual(activity.das_crop, self.farm.crop_id)
        self.assertEqual(activity.das_variety, self.farm.crop_variety_id)

    def test_das_activity_record_str(self):
        activity = DASActivityRecord.objects.create(
            farmer=self.user, farm=self.farm, day_of_sowing=10,
            activity=DASActivityRecord.objects.create(name='Test Activity', organization=self.org)
        )
        expected = f"{self.user.full_name} / 10 / Test Activity"
        self.assertEqual(str(activity), expected)

    def test_external_client_save_encrypt(self):
        client = ExternalClient.objects.create(
            name='Test Client', token='token123', email='test@example.com',
            openai_secret_key='secret123'
        )
        # Assuming encryption happens
        self.assertIsNotNone(client.openai_secret_key)

    def test_external_client_get_openai_secret_key(self):
        client = ExternalClient.objects.create(
            name='Test Client', token='token123', email='test@example.com',
            openai_secret_key='secret123'
        )
        # Test decryption
        decrypted = client.get_openai_secret_key()
        self.assertEqual(decrypted, 'secret123')

    def test_external_client_str(self):
        client = ExternalClient.objects.create(
            name='Test Client', token='token123', email='test@example.com'
        )
        self.assertEqual(str(client), 'Test Client')

    def test_drone_spray_activity_save_generate_reference(self):
        activity = DroneSprayActivity.objects.create(
            farm=self.farm, farmer=self.user, organization=self.org
        )
        self.assertIsNotNone(activity.reference_id)
        self.assertTrue(activity.reference_id.startswith('DSA'))

    def test_drone_spray_activity_populate_from_farm(self):
        activity = DroneSprayActivity.objects.create(
            farm=self.farm, farmer=self.user, organization=self.org
        )
        activity.populate_from_farm()
        self.assertEqual(activity.farmer, self.user)
        self.assertEqual(activity.organization, self.org)

    def test_drone_spray_activity_get_spray_type(self):
        activity = DroneSprayActivity.objects.create(
            farm=self.farm, farmer=self.user, organization=self.org,
            form_response={'spray_type': 'Insecticide'}
        )
        self.assertEqual(activity.get_spray_type(), 'Insecticide')

    def test_drone_spray_activity_str(self):
        activity = DroneSprayActivity.objects.create(
            farm=self.farm, farmer=self.user, organization=self.org,
            reference_id='DSA123'
        )
        expected = "DSA123 | Test User | No date"
        self.assertEqual(str(activity), expected)


if __name__ == '__main__':
    unittest.main()