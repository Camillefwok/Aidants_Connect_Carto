from django.test import TestCase
from django.urls import reverse

from aidants_connect_carto.apps.core.models import DataSource, DataSet, Place, Service


class ApiTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.data_source_1 = DataSource.objects.create(name="Region Test", type="region")
        cls.data_set_1 = DataSet.objects.create(
            name="Lieux EPN 2019", data_source_id=cls.data_source_1.id
        )
        cls.place_1 = Place.objects.create(
            name="Lieu Test 1",
            address_region_name="Auvergne-Rhône-Alpes",
            data_set_id=cls.data_set_1.id,
        )
        cls.service_1 = Service.objects.create(
            name="Stockage numérique sécurisé", place_id=cls.place_1.id
        )

    def test_get_root_api(self):
        response = self.client.get(reverse("api:root"), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, dict)

    def test_get_data_source_list(self):
        response = self.client.get(reverse("api:data-source-list"), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)

    def test_get_data_source_detail(self):
        response = self.client.get(
            reverse("api:data-source-detail", args=[self.data_source_1.id]), secure=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data["name"], "Region Test")

    def test_get_data_set_list(self):
        response = self.client.get(
            reverse("api:data-source-data-set-list", args=[self.data_source_1.id]),
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)

    def test_get_data_set_detail(self):
        response = self.client.get(
            reverse(
                "api:data-source-data-set-detail",
                args=[self.data_source_1.id, self.data_set_1.id],
            ),
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data["name"], "Lieux EPN 2019")

    def test_get_place_list(self):
        response = self.client.get(reverse("api:place-list"), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)

    def test_get_place_detail(self):
        response = self.client.get(
            reverse("api:place-detail", args=[self.place_1.id]), secure=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data["name"], "Lieu Test 1")

    def test_get_service_list(self):
        response = self.client.get(
            reverse("api:place-service-list", args=[self.place_1.id]), secure=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), 1)

    def test_get_service_detail(self):
        response = self.client.get(
            reverse(
                "api:place-service-detail", args=[self.place_1.id, self.service_1.id]
            ),
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, dict)
        self.assertEqual(response.data["name"], "Stockage numérique sécurisé")
