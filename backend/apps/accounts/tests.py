from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User
from .services import register_user, create_organization_for_user


class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='testpassword123',
            full_name='Test User',
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpassword123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpassword123',
            full_name='Admin User',
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_user_str(self):
        user = User(email='hello@example.com', full_name='Hello World')
        self.assertEqual(str(user), 'hello@example.com')

    def test_user_first_last_name(self):
        user = User(email='test@example.com', full_name='John Doe')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')


class RegisterViewTests(APITestCase):
    def test_register_success(self):
        url = reverse('auth-register')
        data = {
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'full_name': 'New User',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data['data'])
        self.assertIn('refresh', response.data['data'])
        self.assertTrue(User.objects.filter(email='newuser@example.com').exists())

    def test_register_duplicate_email(self):
        User.objects.create_user(email='existing@example.com', password='pass123', full_name='Existing')
        url = reverse('auth-register')
        data = {
            'email': 'existing@example.com',
            'password': 'SecurePass123!',
            'full_name': 'New User',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_with_organization(self):
        url = reverse('auth-register')
        data = {
            'email': 'founder@example.com',
            'password': 'SecurePass123!',
            'full_name': 'Founder',
            'organization_name': 'Test Corp',
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data['data']['organization'])
        self.assertEqual(response.data['data']['organization']['name'], 'Test Corp')


class LoginViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='login@example.com',
            password='LoginPass123!',
            full_name='Login User',
        )

    def test_login_success(self):
        url = reverse('auth-login')
        response = self.client.post(url, {'email': 'login@example.com', 'password': 'LoginPass123!'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data['data'])

    def test_login_invalid_credentials(self):
        url = reverse('auth-login')
        response = self.client.post(url, {'email': 'login@example.com', 'password': 'wrongpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MeViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='me@example.com',
            password='MePass123!',
            full_name='Me User',
        )
        self.client.force_authenticate(user=self.user)

    def test_get_me(self):
        url = reverse('auth-me')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['email'], 'me@example.com')

    def test_update_profile(self):
        url = reverse('auth-me')
        response = self.client.patch(url, {'full_name': 'Updated Name'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.full_name, 'Updated Name')
