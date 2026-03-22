# HireRanker REST API Reference

Base URL: `https://yourdomain.com/api/`

All authenticated endpoints require a JWT Bearer token in the `Authorization`
header:

```
Authorization: Bearer <access_token>
```

Timestamps are ISO 8601 UTC. Pagination uses `?page=N&page_size=N` query
params. All responses are JSON.

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Organizations](#2-organizations)
3. [Projects](#3-projects)
4. [Candidate Import](#4-candidate-import)
5. [Candidates](#5-candidates)
6. [Evaluations](#6-evaluations)
7. [Export](#7-export)
8. [Public Review](#8-public-review)
9. [Webhooks (Stripe)](#9-webhooks)
10. [Health Check](#10-health-check)

---

## 1. Authentication

### POST /api/auth/register/

Register a new user account.

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "Jane",
  "last_name": "Doe",
  "organization_name": "Acme Corp"
}
```

**Response 201:**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Doe"
  },
  "organization": {
    "id": "uuid",
    "name": "Acme Corp",
    "slug": "acme-corp"
  },
  "tokens": {
    "access": "<jwt_access_token>",
    "refresh": "<jwt_refresh_token>"
  }
}
```

---

### POST /api/auth/login/

Obtain JWT token pair.

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response 200:**
```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "organization_id": "uuid"
  }
}
```

---

### POST /api/auth/token/refresh/

Refresh an expired access token.

**Request body:**
```json
{
  "refresh": "<jwt_refresh_token>"
}
```

**Response 200:**
```json
{
  "access": "<new_jwt_access_token>"
}
```

---

### POST /api/auth/logout/

Blacklist the refresh token (requires auth).

**Request body:**
```json
{
  "refresh": "<jwt_refresh_token>"
}
```

**Response 204:** No content.

---

### GET /api/auth/me/

Get the current authenticated user's profile.

**Response 200:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "organization": {
    "id": "uuid",
    "name": "Acme Corp",
    "plan": "pro",
    "credits_remaining": 42
  }
}
```

---

### PATCH /api/auth/me/

Update profile (first_name, last_name, password).

---

## 2. Organizations

### GET /api/organizations/me/

Get the authenticated user's organization details.

**Response 200:**
```json
{
  "id": "uuid",
  "name": "Acme Corp",
  "slug": "acme-corp",
  "plan": "pro",
  "credits_remaining": 42,
  "member_count": 5,
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

### PATCH /api/organizations/me/

Update organization name or settings.

---

### GET /api/organizations/me/members/

List organization members.

**Response 200:**
```json
{
  "count": 3,
  "results": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "first_name": "Jane",
      "role": "admin",
      "joined_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

---

### POST /api/organizations/me/members/invite/

Invite a new member by email.

**Request body:**
```json
{
  "email": "colleague@example.com",
  "role": "member"
}
```

**Response 201:** Invitation sent.

---

### DELETE /api/organizations/me/members/{member_id}/

Remove a member from the organization.

---

## 3. Projects

A Project corresponds to a single job opening / hiring round.

### GET /api/projects/

List all projects for the organization.

**Query params:**
- `status` — `active` | `archived` | `draft`
- `search` — full-text search on title/description
- `ordering` — `created_at` | `-created_at` | `title`
- `page`, `page_size`

**Response 200:**
```json
{
  "count": 12,
  "next": "http://api/projects/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "title": "Senior Backend Engineer",
      "status": "active",
      "candidate_count": 34,
      "evaluated_count": 28,
      "created_at": "2024-03-01T09:00:00Z",
      "updated_at": "2024-03-10T14:30:00Z"
    }
  ]
}
```

---

### POST /api/projects/

Create a new project.

**Request body:**
```json
{
  "title": "Senior Backend Engineer",
  "description": "Optional internal notes",
  "job_description": "Full JD text or HTML...",
  "status": "active"
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "title": "Senior Backend Engineer",
  "status": "active",
  "job_description": "...",
  "created_at": "2024-03-01T09:00:00Z"
}
```

---

### GET /api/projects/{project_id}/

Retrieve a single project.

---

### PATCH /api/projects/{project_id}/

Update a project's title, JD, or status.

---

### DELETE /api/projects/{project_id}/

Delete a project and all associated candidates.

**Response 204:** No content.

---

### GET /api/projects/{project_id}/stats/

Aggregated statistics for a project.

**Response 200:**
```json
{
  "candidate_count": 34,
  "evaluated_count": 28,
  "pending_count": 6,
  "score_distribution": {
    "0-20": 2,
    "21-40": 5,
    "41-60": 10,
    "61-80": 14,
    "81-100": 3
  },
  "average_score": 58.4,
  "top_candidate": {
    "id": "uuid",
    "name": "Sophie Nguyen",
    "score": 91
  }
}
```

---

## 4. Candidate Import

### POST /api/projects/{project_id}/candidates/import/csv/

Import candidates in bulk from a CSV file.

**Request:** `multipart/form-data`
- `file` — CSV file (max 50 candidates, 10 MB)

Expected CSV columns (all optional except `name` and `email`):
`name, email, phone, location, college, degree, graduation_year, cgpa, skills, github, linkedin, resume_link, notes`

**Response 202:**
```json
{
  "task_id": "celery-task-uuid",
  "message": "Import queued. 15 candidates will be processed.",
  "status_url": "/api/tasks/celery-task-uuid/status/"
}
```

---

### POST /api/projects/{project_id}/candidates/import/resume/

Import a single candidate by uploading their resume PDF/DOCX.

**Request:** `multipart/form-data`
- `resume` — PDF or DOCX file (max 10 MB)
- `name` — optional override
- `email` — optional override

**Response 202:**
```json
{
  "task_id": "celery-task-uuid",
  "candidate_id": "uuid",
  "message": "Resume uploaded. Parsing and evaluation queued."
}
```

---

### POST /api/projects/{project_id}/candidates/import/bulk-resumes/

Upload multiple resumes as a ZIP archive.

**Request:** `multipart/form-data`
- `archive` — ZIP file containing PDF/DOCX resumes (max 50 files, 50 MB total)

**Response 202:**
```json
{
  "task_id": "celery-task-uuid",
  "queued_count": 12,
  "message": "Bulk import queued.",
  "status_url": "/api/tasks/celery-task-uuid/status/"
}
```

---

### GET /api/tasks/{task_id}/status/

Poll async task status.

**Response 200:**
```json
{
  "task_id": "celery-task-uuid",
  "status": "PROGRESS",
  "progress": 60,
  "total": 15,
  "current_item": "Processing resume for Marcus Johnson",
  "result": null,
  "error": null
}
```

Possible `status` values: `PENDING`, `PROGRESS`, `SUCCESS`, `FAILURE`.

---

## 5. Candidates

### GET /api/projects/{project_id}/candidates/

List all candidates in a project.

**Query params:**
- `status` — `pending` | `evaluated` | `shortlisted` | `rejected`
- `search` — name, email, skills
- `ordering` — `score` | `-score` | `name` | `created_at` | `-created_at`
- `min_score`, `max_score` — filter by evaluation score
- `page`, `page_size`

**Response 200:**
```json
{
  "count": 34,
  "results": [
    {
      "id": "uuid",
      "name": "Sophie Nguyen",
      "email": "sophie.nguyen.tech@gmail.com",
      "location": "Palo Alto CA",
      "college": "Stanford University",
      "degree": "M.S. Computer Science",
      "graduation_year": 2020,
      "cgpa": "3.96",
      "skills": ["Python", "Django", "FastAPI", "PostgreSQL", "AWS", "Kubernetes"],
      "status": "evaluated",
      "score": 91,
      "created_at": "2024-03-01T10:00:00Z"
    }
  ]
}
```

---

### POST /api/projects/{project_id}/candidates/

Manually add a single candidate.

**Request body:**
```json
{
  "name": "Sophie Nguyen",
  "email": "sophie.nguyen@example.com",
  "phone": "+1-650-555-0435",
  "location": "Palo Alto CA",
  "college": "Stanford University",
  "degree": "M.S. Computer Science",
  "graduation_year": 2020,
  "cgpa": "3.96",
  "skills": ["Python", "Django", "PostgreSQL"],
  "github": "github.com/sophienguyen",
  "linkedin": "linkedin.com/in/sophie-nguyen",
  "notes": "Referred by CTO"
}
```

---

### GET /api/projects/{project_id}/candidates/{candidate_id}/

Retrieve a single candidate with full evaluation details.

**Response 200:**
```json
{
  "id": "uuid",
  "name": "Sophie Nguyen",
  "email": "sophie.nguyen.tech@gmail.com",
  "phone": "+1-650-555-0435",
  "location": "Palo Alto CA",
  "college": "Stanford University",
  "degree": "M.S. Computer Science",
  "graduation_year": 2020,
  "cgpa": "3.96",
  "skills": ["Python", "Django", "FastAPI", "PostgreSQL", "AWS", "Kubernetes", "gRPC", "Terraform"],
  "github": "github.com/sophienguyen-ai",
  "linkedin": "linkedin.com/in/sophie-nguyen-eng",
  "resume_url": "https://storage.example.com/resumes/uuid.pdf",
  "status": "evaluated",
  "evaluation": {
    "score": 91,
    "summary": "Exceptional candidate with 4 years of Python/Django experience at Stripe...",
    "strengths": ["Strong PostgreSQL expertise", "Kubernetes production experience", "Open source contributor"],
    "weaknesses": ["Limited explicit fintech compliance experience"],
    "skill_match": 0.87,
    "experience_score": 88,
    "education_score": 95,
    "evaluated_at": "2024-03-01T10:05:00Z",
    "model_used": "gpt-4o"
  },
  "created_at": "2024-03-01T10:00:00Z",
  "updated_at": "2024-03-01T10:05:00Z"
}
```

---

### PATCH /api/projects/{project_id}/candidates/{candidate_id}/

Update candidate status or notes.

**Request body:**
```json
{
  "status": "shortlisted",
  "notes": "Moving to interview stage"
}
```

---

### DELETE /api/projects/{project_id}/candidates/{candidate_id}/

Delete a candidate.

---

### POST /api/projects/{project_id}/candidates/{candidate_id}/re-evaluate/

Trigger a fresh LLM evaluation for a candidate.

**Response 202:**
```json
{
  "task_id": "celery-task-uuid",
  "message": "Re-evaluation queued."
}
```

---

## 6. Evaluations

### GET /api/projects/{project_id}/evaluations/

List evaluations for all candidates in a project, sorted by score descending.

**Query params:**
- `min_score`, `max_score`
- `status` — `pending` | `complete` | `failed`
- `ordering` — `-score` | `score` | `-evaluated_at`
- `page`, `page_size`

**Response 200:**
```json
{
  "count": 28,
  "results": [
    {
      "id": "uuid",
      "candidate_id": "uuid",
      "candidate_name": "Sophie Nguyen",
      "score": 91,
      "summary": "...",
      "strengths": ["..."],
      "weaknesses": ["..."],
      "skill_match": 0.87,
      "evaluated_at": "2024-03-01T10:05:00Z"
    }
  ]
}
```

---

### GET /api/projects/{project_id}/evaluations/{evaluation_id}/

Retrieve a single evaluation record.

---

### POST /api/projects/{project_id}/evaluate-all/

Trigger evaluation for all un-evaluated candidates in the project.

**Response 202:**
```json
{
  "task_id": "celery-task-uuid",
  "queued_count": 6,
  "message": "Evaluation queued for 6 candidates."
}
```

---

## 7. Export

### GET /api/projects/{project_id}/export/csv/

Export all candidate evaluations as a CSV file.

**Query params:** Same filters as the candidate list endpoint.

**Response 200:** `Content-Type: text/csv`

Columns: `rank, name, email, score, status, skills, college, graduation_year, cgpa, summary, strengths, weaknesses, evaluated_at`

---

### GET /api/projects/{project_id}/export/json/

Export all candidate evaluations as a JSON file download.

**Response 200:** `Content-Type: application/json`

---

### GET /api/projects/{project_id}/export/pdf/

Generate a PDF summary report for the project's top candidates.

**Query params:**
- `top_n` — include top N candidates (default: 10, max: 50)

**Response 202:**
```json
{
  "task_id": "celery-task-uuid",
  "message": "PDF generation queued.",
  "download_url": null
}
```

Poll `GET /api/tasks/{task_id}/status/` until complete, then use
`result.download_url`.

---

## 8. Public Review

The public review endpoint allows candidates to pay for a detailed AI-generated
evaluation of their profile against a public job description. No authentication
required. Rate-limited at the nginx layer (10 requests/hour per IP).

### GET /api/review/{project_slug}/

Retrieve public project info (title, JD summary) for the review landing page.

**Response 200:**
```json
{
  "project_slug": "senior-backend-engineer-acme",
  "title": "Senior Backend Engineer",
  "organization": "Acme Corp",
  "jd_summary": "We are looking for a Senior Backend Engineer..."
}
```

---

### POST /api/review/{project_slug}/checkout/

Create a Stripe Checkout session for a candidate review purchase.

**Request body:**
```json
{
  "candidate_name": "John Doe",
  "candidate_email": "john@example.com",
  "resume_text": "Optional raw text of resume...",
  "success_url": "https://app.example.com/review/success",
  "cancel_url": "https://app.example.com/review/cancel"
}
```

**Response 200:**
```json
{
  "checkout_url": "https://checkout.stripe.com/pay/cs_test_...",
  "session_id": "cs_test_..."
}
```

---

### GET /api/review/{project_slug}/result/{review_token}/

Retrieve the completed review result after successful payment.
The `review_token` is returned by Stripe webhook and included in the success URL.

**Response 200:**
```json
{
  "candidate_name": "John Doe",
  "project_title": "Senior Backend Engineer",
  "score": 72,
  "summary": "Strong Python generalist with solid PostgreSQL fundamentals...",
  "strengths": ["4+ years Python experience", "PostgreSQL query optimization"],
  "weaknesses": ["Limited Kubernetes experience", "No fintech domain background"],
  "recommendations": ["Contribute to open source projects in the fintech space", "Get CKA certification"],
  "generated_at": "2024-03-01T12:00:00Z"
}
```

**Response 404:** Review not found or not yet complete.
**Response 402:** Payment not confirmed.

---

## 9. Webhooks

### POST /api/webhooks/stripe/

Stripe sends signed webhook events to this endpoint. HireRanker processes
`checkout.session.completed` to trigger candidate review generation.

The endpoint validates the `Stripe-Signature` header using `STRIPE_WEBHOOK_SECRET`.

**Response 200:** `{"received": true}`

---

## 10. Health Check

### GET /api/health/

Lightweight health check used by load balancers and Docker healthchecks.
No authentication required.

**Response 200:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "timestamp": "2024-03-01T12:00:00Z"
}
```

**Response 503:** If database or Redis is unreachable.

---

## Error Responses

All error responses follow this structure:

```json
{
  "error": "brief_error_code",
  "message": "Human-readable description of the error.",
  "details": {}
}
```

| HTTP Status | Meaning                                      |
|-------------|----------------------------------------------|
| 400         | Bad request / validation error               |
| 401         | Missing or invalid authentication token      |
| 403         | Insufficient permissions                     |
| 404         | Resource not found                           |
| 409         | Conflict (e.g., duplicate email)             |
| 413         | Request entity too large (file upload)       |
| 422         | Unprocessable entity                         |
| 429         | Rate limit exceeded                          |
| 500         | Internal server error                        |
| 503         | Service unavailable (dependency down)        |
