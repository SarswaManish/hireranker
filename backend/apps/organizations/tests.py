from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from .models import Organization, Membership
from .services import generate_unique_slug, get_user_role_in_org


class OrganizationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='pass123',
            full_name='Test User',
        )

    def test_create_organization(self):
        org = Organization.objects.create(
            name='Test Corp',
            slug='test-corp',
            created_by=self.user,
        )
        self.assertEqual(str(org), 'Test Corp')
        self.assertTrue(org.is_active)

    def test_generate_unique_slug(self):
        slug1 = generate_unique_slug('Test Corp')
        self.assertEqual(slug1, 'test-corp')
        Organization.objects.create(name='Test Corp', slug=slug1, created_by=self.user)
        slug2 = generate_unique_slug('Test Corp')
        self.assertNotEqual(slug1, slug2)


class OrganizationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='org@example.com',
            password='pass123',
            full_name='Org User',
        )
        self.client.force_authenticate(user=self.user)

    def test_create_organization(self):
        response = self.client.post('/api/organizations/', {'name': 'My Company'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        org_id = response.data['data']['id']
        self.assertTrue(Organization.objects.filter(id=org_id).exists())
        membership = Membership.objects.get(user=self.user, organization_id=org_id)
        self.assertEqual(membership.role, Membership.Role.OWNER)

    def test_list_organizations(self):
        org = Organization.objects.create(name='Visible Org', slug='visible-org', created_by=self.user)
        Membership.objects.create(user=self.user, organization=org, role=Membership.Role.OWNER)
        other_user = User.objects.create_user(email='other@example.com', password='pass123', full_name='Other')
        other_org = Organization.objects.create(name='Hidden Org', slug='hidden-org', created_by=other_user)
        Membership.objects.create(user=other_user, organization=other_org, role=Membership.Role.OWNER)

        response = self.client.get('/api/organizations/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        org_ids = [o['id'] for o in response.data['results']]
        self.assertIn(str(org.id), org_ids)
        self.assertNotIn(str(other_org.id), org_ids)
