from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.organizations.models import Organization, Membership
from .models import HiringProject


class HiringProjectModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='proj@example.com', password='pass123', full_name='Proj User'
        )
        self.org = Organization.objects.create(name='Test Org', slug='test-org', created_by=self.user)
        Membership.objects.create(user=self.user, organization=self.org, role=Membership.Role.OWNER)

    def test_create_project(self):
        project = HiringProject.objects.create(
            organization=self.org,
            name='Senior Engineer Search',
            role_title='Senior Software Engineer',
            job_description='Looking for an experienced engineer...',
            created_by=self.user,
        )
        self.assertEqual(str(project), f"Senior Engineer Search ({self.org.name})")
        self.assertEqual(project.status, HiringProject.Status.DRAFT)


class HiringProjectAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='proj@example.com', password='pass123', full_name='Proj User'
        )
        self.org = Organization.objects.create(name='Test Org', slug='test-org', created_by=self.user)
        Membership.objects.create(user=self.user, organization=self.org, role=Membership.Role.OWNER)
        self.client.force_authenticate(user=self.user)

    def test_create_project(self):
        response = self.client.post('/api/projects/', {
            'organization': str(self.org.id),
            'name': 'Dev Hiring',
            'role_title': 'Python Developer',
            'job_description': 'We need a Python dev',
            'must_have_skills': ['Python', 'Django'],
            'good_to_have_skills': ['Docker'],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_projects(self):
        HiringProject.objects.create(
            organization=self.org, name='P1', role_title='Dev', job_description='...', created_by=self.user
        )
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_project_stats(self):
        project = HiringProject.objects.create(
            organization=self.org, name='Stats Project', role_title='Dev',
            job_description='...', created_by=self.user
        )
        response = self.client.get(f'/api/projects/{project.id}/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_candidates', response.data['data'])
