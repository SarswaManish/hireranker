import io
import csv

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.organizations.models import Organization, Membership
from apps.projects.models import HiringProject
from .models import Candidate, CandidateImportBatch
from .importers import detect_columns, normalize_candidate_data, _parse_year, _parse_decimal


class ImporterTests(TestCase):
    def test_detect_columns_basic(self):
        import pandas as pd
        df = pd.DataFrame(columns=['Name', 'Email', 'Phone', 'Skills'])
        mapping = detect_columns(df)
        self.assertEqual(mapping.get('name'), 'Name')
        self.assertEqual(mapping.get('email'), 'Email')
        self.assertEqual(mapping.get('phone'), 'Phone')
        self.assertEqual(mapping.get('skills'), 'Skills')

    def test_normalize_candidate_data(self):
        row = {
            'Name': 'John Doe',
            'Email': 'JOHN@EXAMPLE.COM',
            'Skills': 'Python, Django, REST',
            'Graduation Year': '2021',
            'CGPA': '8.5',
        }
        mapping = {
            'name': 'Name',
            'email': 'Email',
            'skills': 'Skills',
            'graduation_year': 'Graduation Year',
            'cgpa': 'CGPA',
        }
        data = normalize_candidate_data(row, mapping)
        self.assertEqual(data['name'], 'John Doe')
        self.assertEqual(data['email'], 'john@example.com')
        self.assertEqual(data['skills'], ['Python', 'Django', 'REST'])
        self.assertEqual(data['graduation_year'], 2021)
        self.assertIsNotNone(data['cgpa'])

    def test_parse_year_valid(self):
        self.assertEqual(_parse_year('2021'), 2021)
        self.assertEqual(_parse_year('Batch 2022'), 2022)
        self.assertIsNone(_parse_year('invalid'))
        self.assertIsNone(_parse_year(''))

    def test_parse_decimal_cgpa(self):
        self.assertAlmostEqual(_parse_decimal('8.5'), 8.5)
        self.assertAlmostEqual(_parse_decimal('85%'), 8.5)
        self.assertIsNone(_parse_decimal(''))
        self.assertIsNone(_parse_decimal('abc'))


class CandidateAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='cand@example.com', password='pass123', full_name='Cand User'
        )
        self.org = Organization.objects.create(name='Cand Org', slug='cand-org', created_by=self.user)
        Membership.objects.create(user=self.user, organization=self.org, role=Membership.Role.OWNER)
        self.project = HiringProject.objects.create(
            organization=self.org,
            name='Dev Search',
            role_title='Developer',
            job_description='Looking for a developer',
            created_by=self.user,
        )
        self.client.force_authenticate(user=self.user)

    def test_list_candidates_empty(self):
        response = self.client.get(f'/api/projects/{self.project.id}/candidates/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_retrieve_candidate(self):
        candidate = Candidate.objects.create(
            project=self.project,
            name='Test Cand',
            email='cand@test.com',
        )
        response = self.client.get(f'/api/projects/{self.project.id}/candidates/{candidate.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['name'], 'Test Cand')

    def test_update_candidate(self):
        candidate = Candidate.objects.create(
            project=self.project,
            name='Original Name',
            email='orig@test.com',
        )
        response = self.client.patch(
            f'/api/projects/{self.project.id}/candidates/{candidate.id}/',
            {'name': 'Updated Name'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        candidate.refresh_from_db()
        self.assertEqual(candidate.name, 'Updated Name')

    def test_add_tag(self):
        candidate = Candidate.objects.create(
            project=self.project,
            name='Tagged Cand',
            email='tag@test.com',
        )
        response = self.client.post(
            f'/api/projects/{self.project.id}/candidates/{candidate.id}/add_tag/',
            {'tag': 'shortlisted'},
            format='json'
        )
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        from .models import CandidateTag
        self.assertTrue(CandidateTag.objects.filter(candidate=candidate, tag='shortlisted').exists())
