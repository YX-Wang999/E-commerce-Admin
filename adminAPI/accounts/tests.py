"""Authentication API tests."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from common.test_utils import auth_staff, create_staff_user

User = get_user_model()


class AuthAPITestCase(APITestCase):
    def setUp(self):
        self.password = 'AdminPass123!'
        self.user = create_staff_user('test_admin', self.password, role_code='super_admin')
        self.login_url = reverse('auth-login')
        self.refresh_url = reverse('auth-refresh')
        self.change_password_url = reverse('auth-change-password')
        self.captcha_url = reverse('auth-captcha')
        self.captcha_verify_url = reverse('auth-captcha-verify')

    @patch('accounts.views.captcha_required_for_trust', return_value=False)
    def test_login_success(self, _mock_captcha):
        response = self.client.post(
            self.login_url,
            {'username': 'test_admin', 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 0)
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])

    @patch('accounts.views.captcha_required_for_trust', return_value=False)
    def test_login_wrong_password(self, _mock_captcha):
        response = self.client.post(
            self.login_url,
            {'username': 'test_admin', 'password': 'wrong-password'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 40007)

    @patch('accounts.views.captcha_required_for_trust', return_value=False)
    def test_login_user_not_found(self, _mock_captcha):
        response = self.client.post(
            self.login_url,
            {'username': 'no_such_user', 'password': 'any'},
            format='json',
        )
        self.assertEqual(response.data['code'], 40006)

    @patch('accounts.views.captcha_required_for_trust', return_value=False)
    def test_login_first_login_flag(self, _mock_captcha):
        self.user.is_first_login = True
        self.user.save(update_fields=['is_first_login'])
        response = self.client.post(
            self.login_url,
            {'username': 'test_admin', 'password': self.password},
            format='json',
        )
        self.assertEqual(response.data['code'], 1001)
        self.assertIn('首次登录', response.data['message'])

    def test_token_refresh_success(self):
        refresh = str(RefreshToken.for_user(self.user))
        response = self.client.post(self.refresh_url, {'refresh': refresh}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 0)
        self.assertIn('access', response.data['data'])

    def test_token_refresh_invalid(self):
        response = self.client.post(self.refresh_url, {'refresh': 'invalid-token'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['code'], 40100)

    def test_change_password_success(self):
        auth_staff(self.client, self.user)
        response = self.client.post(
            self.change_password_url,
            {'old_password': self.password, 'new_password': 'NewPass123!', 'confirm_password': 'NewPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 0)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_first_login)
        self.assertTrue(self.user.check_password('NewPass123!'))

    def test_change_password_wrong_old_password(self):
        auth_staff(self.client, self.user)
        response = self.client.post(
            self.change_password_url,
            {'old_password': 'wrong', 'new_password': 'NewPass123!', 'confirm_password': 'NewPass123!'},
            format='json',
        )
        self.assertNotEqual(response.data['code'], 0)

    def test_captcha_generate_and_verify(self):
        captcha = self.client.get(self.captcha_url)
        self.assertEqual(captcha.status_code, status.HTTP_200_OK)
        captcha_id = captcha.data['data']['captcha_id']
        offset = captcha.data['data']['target_offset']
        verify = self.client.post(
            self.captcha_verify_url,
            {'captcha_id': captcha_id, 'offset': offset, 'trail': []},
            format='json',
        )
        self.assertEqual(verify.data['code'], 0)
