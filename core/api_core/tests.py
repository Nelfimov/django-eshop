"""API core testing"""
import json

from django.contrib.auth.models import User
from django.urls import reverse
from django.test import RequestFactory
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import CategoryItem, Item


class CoreAPITestCase(APITestCase):
    """Testing API for core app"""

    def setUp(self):
        self.sign_up_dict = {
            "login": "test1_username",
            "password": "testing123",
        }
        self.user = User.objects.create(
            username=self.sign_up_dict["login"], password=self.sign_up_dict["password"]
        )
        self.admin = User.objects.create_superuser(username="admin")
        self.category = CategoryItem.objects.create(name="Toys")
        Item.objects.create(
            title="Toy",
            price=100,
            category=CategoryItem.objects.get(name="Toys"),
            description="this is our new toy",
        )
        self.valid_input = {
            "title": "Doll",
            "price": 1000,
            "delivery_price": 5,
            "discount": 1,
            "stock": 1,
            "description": "this is our new doll",
        }
        self.factory = RequestFactory()
        return super().setUp()

    def tearDown(self):
        Item.objects.all().delete()
        CategoryItem.objects.all().delete()
        User.objects.all().delete()
        return super().tearDown()

    def test_login(self):
        """Testing login with admin credentials"""
        self.client.login(
            username=self.sign_up_dict["login"], password=self.sign_up_dict["password"]
        )
        user = User.objects.get(username=self.sign_up_dict["login"])
        self.assertEqual(self.sign_up_dict["login"], user.username)

    def test_get_items(self):
        """Get item list"""
        self.assertEqual(Item.objects.all().count(), 1)

    def test_post_add_items_by_anon(self):
        """Testing to post item by anon/auth"""
        response = self.client.post(
            reverse("item-list"),
            content_type="application/json",
            data=json.dumps(self.valid_input),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(1, Item.objects.all().count())
        self.client.force_login(user=self.user)
        response = self.client.post(
            reverse("item-list"),
            content_type="application/json",
            data=json.dumps(self.valid_input),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(1, Item.objects.all().count())

    def test_post_add_items_by_admin(self):
        """Testing to post item by admin"""
        self.client.force_login(user=self.admin)
        response = self.client.post(
            reverse("item-list"),
            content_type="application/json",
            data=json.dumps(self.valid_input),
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(2, Item.objects.all().count())
        self.assertEqual(self.valid_input["title"], "Doll")

    def test_post_delete_items_by_anon(self):
        """Testing to post delete item by anon/auth"""
        response = self.client.delete(reverse("item-detail", args=[1]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(1, Item.objects.all().count())
        self.client.force_login(user=self.user)
        response = self.client.delete(reverse("item-detail", args=[1]))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(1, Item.objects.all().count())

    def test_post_delete_items_by_admin(self):
        """Testing to post delete item by admin"""
        self.client.force_login(user=self.admin)
        response = self.client.delete(reverse("item-detail", args=[1]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(0, Item.objects.all().count())
