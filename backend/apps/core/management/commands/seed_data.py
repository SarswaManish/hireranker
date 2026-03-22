"""
Management command to seed test data.
Creates a test organization, user, project with sample candidates.
"""
import json
import random

from django.core.management.base import BaseCommand
from django.db import transaction


SAMPLE_SKILLS_POOL = [
    'Python', 'Django', 'FastAPI', 'JavaScript', 'TypeScript', 'React', 'Node.js',
    'PostgreSQL', 'Redis', 'Docker', 'Kubernetes', 'AWS', 'GCP', 'Celery',
    'REST API', 'GraphQL', 'Machine Learning', 'TensorFlow', 'PyTorch',
    'Java', 'Spring Boot', 'Go', 'Rust', 'C++', 'Microservices',
    'Git', 'CI/CD', 'Linux', 'Nginx', 'MongoDB', 'Elasticsearch',
]

SAMPLE_CANDIDATES = [
    {
        'name': 'Rahul Sharma',
        'email': 'rahul.sharma@example.com',
        'phone': '+91 9876543210',
        'location': 'Bengaluru, India',
        'college': 'IIT Bombay',
        'degree': 'B.Tech Computer Science',
        'graduation_year': 2020,
        'cgpa': 8.7,
        'skills': ['Python', 'Django', 'React', 'PostgreSQL', 'Docker', 'AWS'],
        'linkedin_url': 'https://linkedin.com/in/rahul-sharma',
        'github_url': 'https://github.com/rahulsharma',
    },
    {
        'name': 'Priya Patel',
        'email': 'priya.patel@example.com',
        'phone': '+91 9845123456',
        'location': 'Pune, India',
        'college': 'BITS Pilani',
        'degree': 'B.E. Computer Science',
        'graduation_year': 2019,
        'cgpa': 9.1,
        'skills': ['Python', 'FastAPI', 'Machine Learning', 'TensorFlow', 'Docker', 'Kubernetes'],
        'linkedin_url': 'https://linkedin.com/in/priya-patel',
        'github_url': 'https://github.com/priyapatel',
    },
    {
        'name': 'Arjun Nair',
        'email': 'arjun.nair@example.com',
        'phone': '+91 9901234567',
        'location': 'Hyderabad, India',
        'college': 'NIT Trichy',
        'degree': 'B.Tech Information Technology',
        'graduation_year': 2021,
        'cgpa': 8.2,
        'skills': ['JavaScript', 'TypeScript', 'React', 'Node.js', 'MongoDB', 'AWS'],
        'linkedin_url': 'https://linkedin.com/in/arjun-nair',
        'github_url': 'https://github.com/arjunnair',
    },
    {
        'name': 'Sneha Reddy',
        'email': 'sneha.reddy@example.com',
        'phone': '+91 9812345678',
        'location': 'Chennai, India',
        'college': 'VIT University',
        'degree': 'B.Tech Computer Science',
        'graduation_year': 2022,
        'cgpa': 8.5,
        'skills': ['Java', 'Spring Boot', 'Microservices', 'PostgreSQL', 'Redis', 'Docker'],
        'linkedin_url': 'https://linkedin.com/in/sneha-reddy',
        'github_url': 'https://github.com/snehareddy',
    },
    {
        'name': 'Vikram Singh',
        'email': 'vikram.singh@example.com',
        'phone': '+91 9654321098',
        'location': 'Delhi, India',
        'college': 'Delhi Technological University',
        'degree': 'B.Tech Computer Science',
        'graduation_year': 2018,
        'cgpa': 7.8,
        'skills': ['Python', 'Django', 'REST API', 'PostgreSQL', 'Git', 'Linux'],
        'linkedin_url': 'https://linkedin.com/in/vikram-singh',
        'github_url': 'https://github.com/vikramsingh',
    },
    {
        'name': 'Ananya Krishnan',
        'email': 'ananya.krishnan@example.com',
        'phone': '+91 9789012345',
        'location': 'Bengaluru, India',
        'college': 'IIT Madras',
        'degree': 'M.Tech Computer Science',
        'graduation_year': 2021,
        'cgpa': 9.3,
        'skills': ['Python', 'Machine Learning', 'PyTorch', 'FastAPI', 'Docker', 'Kubernetes', 'AWS'],
        'linkedin_url': 'https://linkedin.com/in/ananya-krishnan',
        'github_url': 'https://github.com/ananyakrishnan',
    },
    {
        'name': 'Rohan Gupta',
        'email': 'rohan.gupta@example.com',
        'phone': '+91 9567890123',
        'location': 'Mumbai, India',
        'college': 'VJTI Mumbai',
        'degree': 'B.Tech Computer Engineering',
        'graduation_year': 2020,
        'cgpa': 7.5,
        'skills': ['Go', 'Python', 'Microservices', 'Docker', 'Kubernetes', 'GCP'],
        'linkedin_url': 'https://linkedin.com/in/rohan-gupta',
        'github_url': 'https://github.com/rohangupta',
    },
    {
        'name': 'Divya Menon',
        'email': 'divya.menon@example.com',
        'phone': '+91 9456789012',
        'location': 'Bengaluru, India',
        'college': 'PSG College of Technology',
        'degree': 'B.E. Information Science',
        'graduation_year': 2019,
        'cgpa': 8.9,
        'skills': ['JavaScript', 'React', 'TypeScript', 'GraphQL', 'Node.js', 'PostgreSQL'],
        'linkedin_url': 'https://linkedin.com/in/divya-menon',
        'github_url': 'https://github.com/divyamenon',
    },
    {
        'name': 'Aditya Kumar',
        'email': 'aditya.kumar@example.com',
        'phone': '+91 9345678901',
        'location': 'Noida, India',
        'college': 'Thapar University',
        'degree': 'B.E. Computer Science',
        'graduation_year': 2017,
        'cgpa': 7.2,
        'skills': ['Java', 'Python', 'AWS', 'REST API', 'MySQL', 'Git'],
        'linkedin_url': 'https://linkedin.com/in/aditya-kumar',
        'github_url': 'https://github.com/adityakumar',
    },
    {
        'name': 'Kavya Iyer',
        'email': 'kavya.iyer@example.com',
        'phone': '+91 9234567890',
        'location': 'Bengaluru, India',
        'college': 'RV College of Engineering',
        'degree': 'B.E. Computer Science',
        'graduation_year': 2022,
        'cgpa': 8.3,
        'skills': ['Python', 'Django', 'React', 'PostgreSQL', 'Redis', 'CI/CD'],
        'linkedin_url': 'https://linkedin.com/in/kavya-iyer',
        'github_url': 'https://github.com/kavyaiyer',
    },
]


class Command(BaseCommand):
    help = 'Seed the database with test data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Clear existing seed data before creating new data',
        )
        parser.add_argument(
            '--email',
            type=str,
            default='admin@hireranker.com',
            help='Admin user email (default: admin@hireranker.com)',
        )
        parser.add_argument(
            '--password',
            type=str,
            default='Admin123!',
            help='Admin user password (default: Admin123!)',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        from apps.accounts.models import User
        from apps.organizations.models import Organization, Membership
        from apps.projects.models import HiringProject
        from apps.candidates.models import Candidate

        email = options['email']
        password = options['password']

        self.stdout.write(self.style.NOTICE('Seeding test data...'))

        # Create or get admin user
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'full_name': 'Admin User',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if created or options.get('reset'):
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'  Created admin user: {email} / {password}'))
        else:
            self.stdout.write(f'  Admin user already exists: {email}')

        # Create organization
        from apps.organizations.services import generate_unique_slug
        org, created = Organization.objects.get_or_create(
            slug='hireranker-demo',
            defaults={
                'name': 'HireRanker Demo Corp',
                'website': 'https://hireranker.com',
                'industry': 'technology',
                'size': '11-50',
                'created_by': user,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created organization: {org.name}'))
        else:
            self.stdout.write(f'  Organization already exists: {org.name}')

        # Ensure admin is owner
        Membership.objects.get_or_create(
            user=user,
            organization=org,
            defaults={'role': Membership.Role.OWNER},
        )

        # Create hiring project
        project, created = HiringProject.objects.get_or_create(
            organization=org,
            name='Senior Backend Engineer - 2024',
            defaults={
                'company_name': 'HireRanker Demo Corp',
                'role_title': 'Senior Backend Engineer',
                'job_description': '''We are looking for a Senior Backend Engineer to join our growing team.

## About the Role
You will be responsible for designing and building scalable backend systems that power our AI-driven hiring platform.

## Responsibilities
- Design and implement high-performance REST APIs using Python/Django or FastAPI
- Work with PostgreSQL, Redis, and Celery for data management and async processing
- Build and maintain cloud infrastructure on AWS
- Collaborate with frontend engineers and ML team
- Write clean, tested, documented code

## Requirements
- 3+ years of Python backend development experience
- Strong expertise in Django or FastAPI
- Experience with PostgreSQL and Redis
- Familiarity with Docker and Kubernetes
- Experience with AWS or GCP
- Strong understanding of system design and scalable architecture
- Experience with Celery or similar task queues

## Nice to Have
- Experience with machine learning APIs
- Contributions to open source projects
- Experience with React or other frontend frameworks

## What We Offer
- Competitive salary
- Remote-first culture
- Stock options
- Health insurance
''',
                'must_have_skills': ['Python', 'Django', 'PostgreSQL', 'Redis', 'Docker'],
                'good_to_have_skills': ['AWS', 'Kubernetes', 'FastAPI', 'Celery', 'React'],
                'min_experience_years': 3.0,
                'location_preference': 'Remote (India)',
                'degree_requirement': "Bachelor's in Computer Science or equivalent",
                'status': HiringProject.Status.ACTIVE,
                'created_by': user,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'  Created project: {project.name}'))
        else:
            self.stdout.write(f'  Project already exists: {project.name}')

        # Create candidates
        created_candidates = 0
        for cand_data in SAMPLE_CANDIDATES:
            candidate, created = Candidate.objects.get_or_create(
                project=project,
                email=cand_data['email'],
                defaults={
                    'name': cand_data['name'],
                    'phone': cand_data['phone'],
                    'location': cand_data['location'],
                    'college': cand_data['college'],
                    'degree': cand_data['degree'],
                    'graduation_year': cand_data['graduation_year'],
                    'cgpa': cand_data['cgpa'],
                    'skills': cand_data['skills'],
                    'linkedin_url': cand_data['linkedin_url'],
                    'github_url': cand_data['github_url'],
                    'status': Candidate.Status.PENDING,
                    'raw_data': cand_data,
                }
            )
            if created:
                created_candidates += 1

        self.stdout.write(self.style.SUCCESS(f'  Created {created_candidates} candidates'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('Seed data created successfully!'))
        self.stdout.write('')
        self.stdout.write(f'  Admin Login: {email} / {password}')
        self.stdout.write(f'  Organization: {org.name} (slug: {org.slug})')
        self.stdout.write(f'  Project: {project.name} (ID: {project.id})')
        self.stdout.write(f'  Candidates: {Candidate.objects.filter(project=project).count()} total')
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write('  1. Start the server: python manage.py runserver')
        self.stdout.write('  2. Visit the API: http://localhost:8000/api/docs/')
        self.stdout.write('  3. Trigger evaluations via POST /api/projects/{id}/evaluate/')
