"""Order API tests."""

from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from addresses.models import Address
from cart.models import Cart, CartItem
from common.test_utils import auth_customer, create_customer
from orders.models import Order, OrderItem
from products.models import Brand, Category, Product
from tenants.models import Tenant


class OrderAPITestCase(APITestCase):
    def setUp(self):
        self.customer = create_customer(phone='+8613811100001')
        self.other_customer = create_customer(phone='+8613811100002')
        self.tenant = Tenant.objects.create(
            name='测试店铺',
            code='test-shop',
            contact_name='店主',
            contact_phone='13900000099',
            status=Tenant.STATUS_ACTIVE,
            is_active=True,
        )
        self.category = Category.objects.create(name='订单分类')
        self.brand = Brand.objects.create(name='订单品牌')
        self.product = Product.objects.create(
            name='订单商品',
            category=self.category,
            brand=self.brand,
            tenant=self.tenant,
            price='50.00',
            stock=5,
            status=Product.STATUS_ON_SALE,
            is_active=True,
        )
        self.zero_stock_product = Product.objects.create(
            name='无库存商品',
            category=self.category,
            brand=self.brand,
            tenant=self.tenant,
            price='30.00',
            stock=0,
            status=Product.STATUS_ON_SALE,
            is_active=True,
        )
        self.address = Address.objects.create(
            customer=self.customer,
            name='张三',
            phone='13811100001',
            province='广东省',
            city='深圳市',
            district='南山区',
            detail='科技园',
            is_default=True,
        )
        self.cart = Cart.objects.create(customer=self.customer)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1,
            selected=True,
        )
        self.list_url = reverse('order-list')

    def _checkout_payload(self, cart_item=None, quantity=1):
        cart_item = cart_item or self.cart_item
        return {
            'address_id': self.address.id,
            'items': [{'cart_item_id': cart_item.id, 'quantity': quantity}],
        }

    def test_create_order_success(self):
        auth_customer(self.client, self.customer)
        response = self.client.post(self.list_url, self._checkout_payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 0)
        order_id = response.data['data']['id']
        order = Order.objects.get(pk=order_id)
        self.assertEqual(order.customer_id, self.customer.id)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 4)

    def test_create_order_insufficient_stock(self):
        auth_customer(self.client, self.customer)
        out_item = CartItem.objects.create(
            cart=self.cart,
            product=self.zero_stock_product,
            quantity=1,
            selected=True,
        )
        response = self.client.post(
            self.list_url,
            self._checkout_payload(cart_item=out_item),
            format='json',
        )
        self.assertNotEqual(response.data['code'], 0)
        self.assertIn('库存不足', response.data['message'])

    def test_order_list_only_own_orders(self):
        Order.objects.create(
            customer=self.customer,
            tenant=self.tenant,
            order_no='ORD-SELF-001',
            total_amount=Decimal('50.00'),
            status=Order.STATUS_PENDING,
        )
        Order.objects.create(
            customer=self.other_customer,
            tenant=self.tenant,
            order_no='ORD-OTHER-001',
            total_amount=Decimal('50.00'),
            status=Order.STATUS_PENDING,
        )
        auth_customer(self.client, self.customer)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order_nos = {item['order_no'] for item in response.data['data']['results']}
        self.assertIn('ORD-SELF-001', order_nos)
        self.assertNotIn('ORD-OTHER-001', order_nos)

    def test_cancel_pending_order(self):
        order = Order.objects.create(
            customer=self.customer,
            tenant=self.tenant,
            order_no='ORD-CANCEL-001',
            total_amount=Decimal('50.00'),
            status=Order.STATUS_PENDING,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            product_name=self.product.name,
            unit_price=self.product.price,
            quantity=1,
        )
        auth_customer(self.client, self.customer)
        url = reverse('order-cancel', args=[order.id])
        response = self.client.post(url, {'reason': '不想买了'}, format='json')
        self.assertEqual(response.data['code'], 0)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_CANCELLED)

    def test_cancel_shipped_order_forbidden(self):
        order = Order.objects.create(
            customer=self.customer,
            tenant=self.tenant,
            order_no='ORD-SHIP-001',
            total_amount=Decimal('50.00'),
            status=Order.STATUS_SHIPPED,
        )
        auth_customer(self.client, self.customer)
        url = reverse('order-cancel', args=[order.id])
        response = self.client.post(url, {'reason': '测试'}, format='json')
        self.assertNotEqual(response.data['code'], 0)
        self.assertIn('已发货', response.data['message'])

    def test_confirm_receipt_route_and_success(self):
        from logistics.models import Logistics

        order = Order.objects.create(
            customer=self.customer,
            tenant=self.tenant,
            order_no='ORD-RECEIPT-001',
            total_amount=Decimal('50.00'),
            status=Order.STATUS_SHIPPED,
            address='广东省深圳市南山区科技园',
        )
        Logistics.objects.create(
            order=order,
            express_company='顺丰',
            express_code='SF',
            tracking_number='SF1234567890',
            status=Logistics.STATUS_DELIVERED,
            traces=[{'content': '已签收', 'time': '2026-06-27 10:00:00'}],
        )
        auth_customer(self.client, self.customer)
        url = reverse('order-confirm-receipt', args=[order.id])
        self.assertEqual(url, f'/api/orders/{order.id}/confirm-receipt/')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 0)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.STATUS_COMPLETED)
        self.assertEqual(order.receipt_type, 'normal')
