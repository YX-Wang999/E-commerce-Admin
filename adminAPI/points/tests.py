"""Points API tests."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.test_utils import auth_customer, create_customer
from points.models import PointsRule, PointsTransaction


class PointsAPITestCase(APITestCase):
    def setUp(self):
        self.customer = create_customer(phone='+8613822200001')
        self.sign_in_url = reverse('points-sign-in')
        self.transactions_url = reverse('points-mall-transactions')
        PointsRule.objects.update_or_create(
            code='sign_in',
            defaults={
                'name': '每日签到',
                'description': '测试签到',
                'rule_type': PointsRule.RULE_EARN,
                'current_value': 10,
                'is_active': True,
            },
        )

    def test_sign_in_first_time_success(self):
        auth_customer(self.client, self.customer)
        response = self.client.post(self.sign_in_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 0)
        self.assertGreater(response.data['data']['points_earned'], 0)
        self.assertTrue(
            PointsTransaction.objects.filter(
                customer=self.customer,
                source__startswith='sign_in:',
            ).exists(),
        )

    def test_sign_in_duplicate_same_day(self):
        auth_customer(self.client, self.customer)
        first = self.client.post(self.sign_in_url, format='json')
        self.assertEqual(first.data['code'], 0)
        second = self.client.post(self.sign_in_url, format='json')
        self.assertNotEqual(second.data['code'], 0)
        self.assertIn('今日已签到', second.data['message'])

    def test_transactions_paginated_for_customer(self):
        auth_customer(self.client, self.customer)
        self.client.post(self.sign_in_url, format='json')
        response = self.client.get(self.transactions_url, {'page': 1, 'page_size': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['data']['count'], 1)
        for item in response.data['data']['results']:
            self.assertEqual(item['customer'], self.customer.id)

    def test_sign_in_requires_login(self):
        response = self.client.post(self.sign_in_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
