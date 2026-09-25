"""Product API tests."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.test_utils import auth_staff, create_customer, create_staff_user
from products.models import Brand, Category, Product


class ProductAPITestCase(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(name='测试分类')
        self.brand = Brand.objects.create(name='测试品牌')
        self.on_sale_product = Product.objects.create(
            name='上架商品',
            category=self.category,
            brand=self.brand,
            price='99.00',
            stock=10,
            status=Product.STATUS_ON_SALE,
            is_active=True,
        )
        self.off_sale_product = Product.objects.create(
            name='下架商品',
            category=self.category,
            brand=self.brand,
            price='49.00',
            stock=0,
            status=Product.STATUS_OFF_SALE,
            is_active=True,
        )
        self.admin = create_staff_user('product_admin', role_code='super_admin')
        self.list_url = reverse('product-list')
        self.detail_url = lambda pk: reverse('product-detail', args=[pk])

    def test_product_list_public(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['data']['results']
        ids = {item['id'] for item in results}
        self.assertIn(self.on_sale_product.id, ids)
        self.assertNotIn(self.off_sale_product.id, ids)

    def test_product_list_pagination(self):
        response = self.client.get(self.list_url, {'page': 1, 'page_size': 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['results']), 1)

    def test_product_list_filter_category(self):
        response = self.client.get(self.list_url, {'category': self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for item in response.data['data']['results']:
            self.assertEqual(item['category'], self.category.id)

    def test_product_detail_exists(self):
        response = self.client.get(self.detail_url(self.on_sale_product.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['name'], '上架商品')

    def test_product_detail_not_found(self):
        response = self.client.get(self.detail_url(999999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_product_create_requires_auth(self):
        payload = {
            'name': '新商品',
            'category': self.category.id,
            'brand': self.brand.id,
            'price': '10.00',
            'stock': 5,
            'status': Product.STATUS_DRAFT,
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_product_create_by_admin(self):
        auth_staff(self.client, self.admin)
        payload = {
            'name': '管理员创建商品',
            'category': self.category.id,
            'brand': self.brand.id,
            'price': '19.90',
            'stock': 8,
            'status': Product.STATUS_DRAFT,
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 0)
        self.assertTrue(Product.objects.filter(name='管理员创建商品').exists())

    def test_product_create_denied_for_customer_principal(self):
        customer = create_customer()
        from common.test_utils import auth_customer

        auth_customer(self.client, customer)
        payload = {
            'name': '用户创建商品',
            'category': self.category.id,
            'brand': self.brand.id,
            'price': '9.90',
            'stock': 1,
            'status': Product.STATUS_DRAFT,
        }
        response = self.client.post(self.list_url, payload, format='json')
        self.assertIn(response.status_code, {status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED})
